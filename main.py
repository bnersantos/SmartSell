from flask import Flask, render_template, request, redirect, url_for, jsonify
from flask_pydantic_spec import FlaskPydanticSpec
from datetime import datetime, timedelta
from functools import wraps
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity, jwt_required, JWTManager
from sqlalchemy.testing.pickleable import User
from flask_cors import CORS
from models import *
import sqlalchemy
from sqlalchemy import select
from models import *

app = Flask(__name__)
app.config['JWT_SECRET_KEY'] = 'super-secret'
jwt = JWTManager(app)
spec = FlaskPydanticSpec('flask', title='API - SMARTSELL', version='1.0.0')

#http://10.135.235.27:5002
@app.route('/login', methods=['POST'])
def login():
    """
        API para login do usuário.

        ## Endpoint:
            /login

        ## Método:
            POST

        ## Requisição (JSON):
            {
                "email": "usuario@exemplo.com",
                "senha": "senha123"
            }

        ## Respostas (JSON):
            Sucesso - 200 OK
            ```json
            {
                "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6...",
                "papel": "admin",
                "nome": "João Silva"
            }
            ```

        ## Erros possíveis (JSON):

        Credenciais inválidas - 401 Unauthorized
            ```json
            {
                "msg": "Credenciais inválidas"
            }
            ```

        Erro interno do servidor - 500 Internal Server Error
            ```json
            {
                "msg": "Erro interno do servidor"
            }
            ```
        """
    data = request.get_json()
    email = data.get('email')
    senha = data.get('senha')

    db_session = local_session()
    try:
        user = db_session.execute(
            select(Usuario).where(Usuario.email == email)
        ).scalar()

        if user and user.check_senha(senha):
            # Gera o token JWT usando o email do usuário
            access_token = create_access_token(identity=user.email)
            return jsonify({
                "access_token": access_token,
                "papel": user.papel,
                "nome": user.nome
            }), 200

        return jsonify({"msg": "Credenciais inválidas"}), 401

    except Exception as e:
        print(e)
        return jsonify({"msg": "Erro interno do servidor"}), 500
    finally:
        db_session.close()


@app.route('/cadastro/usuario', methods=['POST'])
def cadastro_usuario():
    db_session = local_session()
    try:
        data = request.get_json()
        nome = data['nome']
        telefone = data['telefone'].strip()
        email = data['email'].strip()
        senha = data['senha']
        papel = data.get('papel', 'usuario')

        # Validação dos campos obrigatórios
        if not nome or not telefone or not email or not senha or not papel:
            return jsonify({
                "msg": "Nome, telefone, email e senha são obrigatórios."
            }), 400

        # Verifica se já existe usuário com o mesmo email
        check_user = select(Usuario).where(Usuario.email == email)
        user_exists = db_session.execute(check_user).scalar()
        if user_exists:
            return jsonify({
                "msg": "Usuário já existente!"
            }), 400

        # Cria o usuário e define o hash da senha
        new_user = Usuario(
            nome=nome,
            telefone=telefone,
            email=email,
            papel=papel)
        new_user.set_senha_hash(senha)
        new_user.save(db_session)

        id_user = new_user.id
        return jsonify({
            "msg": "Usuário criado com sucesso!",
            "user_id": id_user,
        }), 201

    except Exception as e:
        db_session.rollback()
        return jsonify({
            "msg": f"Erro ao cadastrar usuário: {str(e)}"
        }), 500
    finally:
        db_session.close()


@app.route('/editar/usuario/<int:id>', methods=['PUT'])
def editar_usuario(id):
    db_session = local_session()
    try:
        data = request.get_json()
        nome = data['nome']
        telefone = data['telefone'].strip()
        email = data['email'].strip()
        senha = data['senha'].strip()
        papel = data.get('papel', 'usuario')
        status = data.get('status')

        put_user = db_session.execute(select(Usuario).where(Usuario.id == id)).scalar()
        if not put_user:
            return jsonify({"msg": "Usuário não encontrado!"}), 404

        email_exists = db_session.execute(select(Usuario).where(Usuario.email == email, Usuario.id != id)).scalar()
        phone_exists = db_session.execute(
            select(Usuario).where(Usuario.telefone == telefone, Usuario.id != id)).scalar()
        if email_exists:
            return jsonify({"msg": "Este email já está cadastrado!"}), 400
        if phone_exists:
            return jsonify({"msg": "Este telefone já está cadastrado!"}), 400

        put_user.nome = data.get('nome', put_user.nome).strip() if data.get('nome') else put_user.nome
        put_user.telefone = data.get('telefone', put_user.telefone).strip() if data.get(
            'telefone') else put_user.telefone
        put_user.email = data.get('email', put_user.email).strip() if data.get('email') else put_user.email
        put_user.papel = data.get('papel', put_user.papel).strip() if data.get('papel') else put_user.papel

        # status pode ser bool ou None, então só atualiza se estiver no JSON
        if 'status' in data:
            val = data['status']

            # Aceita booleanos True/False diretamente
            if val is True or val is False:
                put_user.status = val
            else:
                # Converter para string para facilitar checagem
                val_str = str(val).lower()

                # Checa strings aceitas
                if val_str == 'true' or val_str == '1':
                    put_user.status = True
                elif val_str == 'false' or val_str == '2':
                    put_user.status = False
                # Caso contrário, ignora a atualização para evitar erro

        if data.get('senha'):
            put_user.set_senha_hash(data['senha'].strip())

        if data.get('senha'):
            put_user.set_senha_hash(data['senha'].strip())

        put_user.save(db_session)

        return jsonify({
            "nome": put_user.nome,
            "telefone": put_user.telefone,
            "email": put_user.email,
            "papel": put_user.papel,
            "status": put_user.status,
        }), 200

    except sqlalchemy.exc.IntegrityError:
        return jsonify({"msg": "O email ou telefone já estão cadastrados!"}), 400
    except Exception as e:
        print(f"Erro inesperado: {str(e)}")
        return jsonify({"msg": "Erro interno do servidor!"}), 500
    finally:
        db_session.close()


@app.route('/cadastro/ingrediente', methods=['POST'])
def cadastro_ingrediente():
    db_session = local_session()
    try:
        data = request.get_json()

        nome = data.get('nome')
        unidade = data.get('unidade')
        quantidade_estoque = data.get('quantidade_estoque', 0)
        status = data.get('status', True)

        # Verifica campos obrigatórios
        if not nome or not unidade:
            return jsonify({"msg": "Nome e unidade são obrigatórios."}), 400

        # Verifica se já existe produto com o mesmo nome
        ja_existe = db_session.execute(
            select(Ingrediente).where(Ingrediente.nome == nome)
        ).scalar()

        unidades_validas = ['g', 'mg', 'kg', 'ml', 'l','un']
        unidade_normalizada = unidade.strip().lower()

        if unidade_normalizada not in unidades_validas:
            return jsonify({
                "msg": f"Unidade inválida. Use apenas: {', '.join(unidades_validas)}."
            }), 400

        if ja_existe:
            return jsonify({"msg": "Ingrediente com esse nome já existe."}), 400

        # Validação do status
        if status is True or status is False:
            status_final = status
        else:
            status_str = str(status).strip().lower()
            if status_str == 'true' or status_str == '1' or status_str == 'ativo':
                status_final = True
            elif status_str == 'false' or status_str == '2' or status_str == 'desativo':
                status_final = False
            else:
                return jsonify({"msg": "Valor de 'status' inválido. Use true/false ou 1/2."}), 400

        # Criação do novo produto
        novo_ingrediente = Ingrediente(
            nome=nome.strip(),
            unidade=unidade.strip(),
            quantidade_estoque=quantidade_estoque,
            status=status_final
        )
        novo_ingrediente.save(db_session)

        return jsonify({
            "msg": "Ingrediente cadastrado com sucesso!",
            "produto": novo_ingrediente.serialize()
        }), 201

    except Exception as e:
        db_session.rollback()
        return jsonify({"msg": f"Erro ao cadastrar o ingrediente : {str(e)}"}), 500

    finally:
        db_session.close()


@app.route('/editar/item/<tipo>/<valor>', methods=['PUT'])
def editar_ingrediente(tipo, valor):
    db_session = local_session()
    try:
        data = request.get_json()

        UNIDADES_PERMITIDAS = {'g', 'mg', 'kg', 'ml', 'l', 'un'}

        # Buscar produto por ID ou nome
        if tipo == 'id':
            try:
                ingrediente = db_session.execute(
                    select(Ingrediente).where(Ingrediente.id == int(valor))
                ).scalar()
            except ValueError:
                return jsonify({"msg": "ID inválido."}), 400

        elif tipo == 'nome':
            ingrediente = db_session.execute(
                select(Ingrediente).where(Ingrediente.nome == valor.strip())
            ).scalar()
        else:
            return jsonify({"msg": "Parâmetro de busca inválido. Use 'id' ou 'nome'."}), 400

        if not ingrediente:
            return jsonify({"msg": "Produto não encontrado."}), 404

        # Atualiza nome (se enviado)
        if 'nome' in data:
            novo_nome = data['nome'].strip()
            if not novo_nome:
                return jsonify({"msg": "Nome não pode ser vazio."}), 400
            if novo_nome != ingrediente.nome:
                existente = db_session.execute(
                    select(Produto).where(Produto.nome == novo_nome, Produto.id != ingrediente.id)
                ).scalar()
                if existente:
                    return jsonify({"msg": "Já existe um produto com esse nome."}), 400
                ingrediente.nome = novo_nome

        if 'unidade' in data:
            nova_unidade = data['unidade'].strip().lower()
            if not nova_unidade:
                return jsonify({"msg": "Unidade não pode ser vazia."}), 400
            if nova_unidade not in UNIDADES_PERMITIDAS:
                return jsonify({"msg": "Unidade inválida. Use g, mg, kg, ml, l ou un."}), 400
            ingrediente.unidade = nova_unidade

        if 'quantidade_estoque' in data:
            valor_qtd = str(data['quantidade_estoque']).strip()
            if valor_qtd == '' or valor_qtd.lower() == 'none':
                ingrediente.quantidade_estoque = 0.0
            else:
                try:
                    ingrediente.quantidade_estoque = float(valor_qtd)
                except:
                    return jsonify({"msg": "Quantidade de estoque inválida."}), 400

        # Atualiza status
        if 'status' in data:
            val = data['status']
            if val is True or val is False:
                ingrediente.status = val
            else:
                val_str = str(val).strip().lower()
                if val_str == 'true' or val_str == '1':
                    ingrediente.status = True
                elif val_str == 'false' or val_str == '2':
                    ingrediente.status = False
                else:
                    return jsonify({"msg": "Valor de 'status' inválido. Use true/false ou 1/2."}), 400

        # Salvar alterações
        ingrediente.save(db_session)

        return jsonify({
            "msg": "Ingrediente atualizado com sucesso!",
            "ingrediente": ingrediente.serialize()
        }), 200

    except Exception as e:
        db_session.rollback()
        return jsonify({"msg": f"Erro ao editar produto: {str(e)}"}), 500

    finally:
        db_session.close()


@app.route('/itens', methods=['GET'])
def listar_ingrediente():
    db_session = local_session()
    try:
        ingredientes = db_session.execute(select(Ingrediente)).scalars().all()

        if not ingredientes:
            return jsonify({"msg": "Nenhum ingredientes encontrado."}), 404

        return jsonify({
            "produtos": [ingrediente.serialize() for ingrediente in ingredientes]
        }), 200

    except Exception as e:
        return jsonify({"msg": f"Erro ao listar produtos: {str(e)}"}), 500

    finally:
        db_session.close()


@app.route('/cadastro/item/cardapio', methods=['POST'])
def cadastrar_produto_cardapio():
    """
    API para cadastrar um novo item no cardápio com seus ingredientes.

    ## Endpoint:
        /cadastro/item/cardapio

    ## Método:
        POST

    ## Requisição (JSON):
        {
            "nome": "Pizza Calabresa",
            "descricao": "Pizza com calabresa, queijo e molho",
            "preco": 39.90,
            "categoria": "Pizza",
            "ingredientes": [
                {
                    "produto_id": 1,
                    "quantidade_necessaria": 0.2
                },
                {
                    "produto_id": 2,
                    "quantidade_necessaria": 0.1
                }
            ]
        }

    ## Respostas (JSON):
        Sucesso - 201
        {
            "msg": "Item do cardápio cadastrado com sucesso!",
            "item": {
                "id": 5,
                "nome": "Pizza Calabresa",
                "descricao": "Pizza com calabresa, queijo e molho",
                "preco": 39.90,
                "categoria": "Pizza",
                "status": true
            }
        }

    ## Erros possíveis (JSON):
        Nome duplicado - 400
        {
            "msg": "Já existe um item com esse nome no cardápio."
        }

        Produto não encontrado - 400
        {
            "msg": "Produto com id 99 não encontrado."
        }

        Campos obrigatórios ausentes - 400
        {
            "msg": "Todos os campos são obrigatórios."
        }

        Erro interno - 500
        {
            "msg": "Erro ao cadastrar item: detalhes..."
        }
    """
    db_session = local_session()
    try:
        data = request.get_json()

        nome = data.get("nome", "").strip() if data.get("nome") else ""
        descricao = data.get("descricao", "").strip() if data.get("descricao") else ""
        preco = data.get("preco")
        categoria = data.get("categoria", "").strip() if data.get("categoria") else ""
        ingredientes = data.get("ingredientes")

        if not nome or preco is None or not categoria or not ingredientes:
            return jsonify({"msg": "Todos os campos são obrigatórios."}), 400

        # Checar se ingredientes é iterável e tem pelo menos um item
        try:
            iter(ingredientes)
        except TypeError:
            return jsonify({"msg": "O campo 'ingredientes' deve ser uma lista de ingredientes."}), 400

        # Tentar acessar o primeiro item para ver se tem pelo menos um ingrediente
        try:
            primeiro_ingrediente = ingredientes[0]
        except (IndexError, TypeError):
            return jsonify({"msg": "O campo 'ingredientes' deve conter pelo menos um ingrediente."}), 400

        # Verifica se nome já existe
        name_exist = select(Produto).where(Produto.nome == nome)
        existente = db_session.execute(name_exist).scalars().first()
        if existente:
            return jsonify({"msg": "Já existe um item com esse nome no cardápio."}), 400

        # Cria item no cardápio
        novo_item = Produto(
            nome=nome,
            descricao=descricao,
            preco=preco,
            categoria=categoria,
            status=True
        )
        db_session.add(novo_item)
        db_session.flush()  # para obter o ID

        # Relaciona os ingredientes
        for ingrediente in ingredientes:
            # Verifica se ingrediente tem os campos esperados e é acessível via get()
            if not hasattr(ingrediente, "get"):
                return jsonify({"msg": "Cada ingrediente deve ser um objeto com produto_id e quantidade_necessaria."}), 400

            produto_id = ingrediente.get("produto_id")
            quantidade = ingrediente.get("quantidade_necessaria")

            if not produto_id or quantidade is None:
                return jsonify({"msg": "Cada ingrediente precisa de produto_id e quantidade_necessaria."}), 400

            produto = db_session.query(Produto).filter_by(id=produto_id).first()
            if not produto:
                db_session.rollback()
                return jsonify({"msg": f"Produto com id {produto_id} não encontrado."}), 400

            relacao = ProdutoIngrediente(
                produto_id=novo_item.id,
                ingrediente_id=produto_id,
                quantidade_necessaria=quantidade
            )
            db_session.add(relacao)

        db_session.commit()

        return jsonify({
            "msg": "Item do cardápio cadastrado com sucesso!",
            "item": novo_item.serialize()
        }), 201

    except Exception as e:
        db_session.rollback()
        return jsonify({"msg": f"Erro ao cadastrar item: {str(e)}"}), 500

    finally:
        db_session.close()


@app.route('/cardapio', methods=['GET'])
def listar_cardapio():
    db_session = local_session()
    try:
        # Busca todos os produtos ativos
        produtos_ativos = db_session.query(Produto).filter(Produto.status == True).all()

        cardapio = []
        for produto in produtos_ativos:
            item_dict = produto.serialize()
            ingredientes = []

            for pi in produto.ingredientes_necessarios:
                ingrediente = pi.ingrediente  # Aqui pega o objeto Ingrediente relacionado

                ingredientes.append({
                    "ingrediente_id": ingrediente.id,
                    "nome": ingrediente.nome,
                    "quantidade_necessaria": pi.quantidade_necessaria,
                    "unidade": ingrediente.unidade
                })

            item_dict["ingredientes"] = ingredientes
            cardapio.append(item_dict)

        return jsonify({"cardapio": cardapio}), 200

    except Exception as e:
        db_session.rollback()
        return jsonify({"msg": f"Erro ao listar cardápio: {str(e)}"}), 500

    finally:
        db_session.close()





if __name__ == '__main__':
    app.run(debug=True, port=5002, host="0.0.0.0")  # Rodar em uma porta diferente da API principal
