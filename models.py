from datetime import datetime
from sqlalchemy import create_engine, Column, Integer, String, ForeignKey, Float, DateTime, Boolean
from sqlalchemy.orm import relationship, sessionmaker, scoped_session
from sqlalchemy.orm import declarative_base
from werkzeug.security import generate_password_hash, check_password_hash

engine = create_engine('sqlite:///SmartSell.sqlite3')
local_session = sessionmaker(bind=engine)

Base = declarative_base()

class Usuario(Base): #TÁ PRONTO
    __tablename__ = 'usuario'
    id = Column(Integer, primary_key=True)
    nome = Column(String, nullable=False, unique=True)
    telefone = Column(String(20), nullable=False, unique=True)
    email = Column(String, nullable=False, unique=True)
    senha_hash = Column(String, nullable=False)
    papel = Column(String, nullable=False)
    status = Column(Boolean, default=True)

    pedidos = relationship("Pedido", back_populates="usuario")

    def set_senha_hash(self, senha):
        self.senha_hash = generate_password_hash(senha)

    def check_senha(self, senha):
        return check_password_hash(self.senha_hash, senha)

    def __repr__(self):
        return f'<Usuario(id={self.id}, nome={self.nome}, telefone={self.telefone}, email={self.email}, papel={self.papel})>'

    def serialize(self):
        return {
            "id": self.id,
            "nome": self.nome,
            "telefone": self.telefone,
            "email": self.email,
            "papel": self.papel
        }

    def save(self, db_session):
        if not self.nome or not self.email or not self.senha_hash:
            raise ValueError("Nome, email e senha são obrigatórios")
        try:
            db_session.add(self)
            db_session.commit()
        except Exception as e:
            db_session.rollback()
            raise e

    def delete(self, db_session):
        try:
            db_session.delete(self)
            db_session.commit()
        except Exception as e:
            db_session.rollback()
            raise e


class Produto(Base): #TÁ PRONTO
    __tablename__ = 'produto'
    id = Column(Integer, primary_key=True)
    nome = Column(String, nullable=False)
    descricao = Column(String)
    preco = Column(Float, nullable=False)
    categoria = Column(String, nullable=False)
    status = Column(Boolean, default=True)

    pedidos = relationship("Pedido", back_populates="produto")
    ingredientes_necessarios = relationship("ProdutoIngrediente", back_populates="produto")

    def __repr__(self):
        return f'<Cardapio(id={self.id}, nome={self.nome}, preco={self.preco}, categoria={self.categoria}, disponivel={self.disponivel})>'

    def serialize(self):
        return {
            "id": self.id,
            "nome": self.nome,
            "descricao": self.descricao,
            "preco": self.preco,
            "categoria": self.categoria,
            "status": self.status
        }

    def save(self, db_session):
        try:
            db_session.add(self)
            db_session.commit()
        except Exception as e:
            db_session.rollback()
            raise e

    def delete(self, db_session):
        try:
            db_session.delete(self)
            db_session.commit()
        except Exception as e:
            db_session.rollback()
            raise e


class Pedido(Base): #TÁ PRONTO
    __tablename__ = 'pedido'
    id = Column(Integer, primary_key=True)
    valor_total = Column(Float, nullable=False)
    quantidade = Column(Integer, default=1)
    metodo_pagamento = Column(String)
    data = Column(DateTime, default=datetime.utcnow)
    status = Column(String, default="pendente")

    usuario_id = Column(Integer, ForeignKey('usuario.id'), nullable=False)
    produto_id = Column(Integer, ForeignKey('produto.id'), nullable=False)

    usuario = relationship("Usuario", back_populates="pedidos")
    produto = relationship("Produto", back_populates="pedidos")
    movimentos = relationship("Movimento", back_populates="pedido")  # <-- corrigido aqui

    def __repr__(self):
        return (f'<Pedido(id={self.id}, usuario={self.usuario.nome if self.usuario else None}, '
                f'cardapio={self.produto.nome if self.produto else None}, quantidade={self.quantidade}, '
                f'status={self.status}, metodo_pagamento={self.metodo_pagamento}, '
                f'valor_total={self.valor_total}, data={self.data})>')

    def serialize(self):
        return {
            "id": self.id,
            "usuario": self.usuario.nome if self.usuario else None,
            "cardapio": self.produto.nome if self.produto else None,
            "quantidade": self.quantidade,
            "metodo_pagamento": self.metodo_pagamento,
            "data": self.data.isoformat(),
            "status": self.status,
            "valor_total": self.valor_total
        }

    def save(self, db_session):
        try:
            db_session.add(self)
            db_session.commit()
        except Exception as e:
            db_session.rollback()
            raise e

    def delete(self, db_session):
        try:
            db_session.delete(self)
            db_session.commit()
        except Exception as e:
            db_session.rollback()
            raise e


class Movimento(Base): #TÁ PRONTO
    __tablename__ = 'movimento'
    id = Column(Integer, primary_key=True)
    pedido_id = Column(Integer, ForeignKey('pedido.id'), nullable=False)
    valor_total = Column(Float, nullable=False)
    entrada = Column(Boolean, default=False)
    saida = Column(Boolean, default=False)

    pedido = relationship("Pedido", back_populates="movimentos")  # <-- corrigido aqui

    def __repr__(self):
        return f'<Movimento(id={self.id}, pedido={self.pedido_id}, valor={self.valor_total}, entrada={self.entrada}, saida={self.saida})>'

    def serialize(self):
        return {
            "id": self.id,
            "pedido_id": self.pedido_id,
            "valor_total": self.valor_total,
            "entrada": self.entrada,
            "saida": self.saida
        }

    def save(self, db_session):
        try:
            db_session.add(self)
            db_session.commit()
        except Exception as e:
            db_session.rollback()
            raise e

    def delete(self, db_session):
        try:
            db_session.delete(self)
            db_session.commit()
        except Exception as e:
            db_session.rollback()
            raise e

class Ingrediente(Base):
    __tablename__ = 'ingrediente'
    id = Column(Integer, primary_key=True)
    nome = Column(String, nullable=False, unique=True)
    unidade = Column(String, nullable=False)  # ex: "kg", "un", "ml"
    quantidade_estoque = Column(Float, nullable=False, default=0)
    status = Column(Boolean, default=True)

    usado_em_produtos = relationship("ProdutoIngrediente", back_populates="ingrediente")

    def __repr__(self):
        return f"<Produto(id={self.id}, nome={self.nome}, estoque={self.quantidade_estoque}{self.unidade})>"

    def serialize(self):
        return {
            "id": self.id,
            "nome": self.nome,
            "unidade": self.unidade,
            "quantidade_estoque": self.quantidade_estoque
        }

    def save(self, db_session):
        try:
            db_session.add(self)
            db_session.commit()
        except Exception as e:
            db_session.rollback()
            raise e

    def delete(self, db_session):
        try:
            db_session.delete(self)
            db_session.commit()
        except Exception as e:
            db_session.rollback()
            raise e

class ProdutoIngrediente(Base):
    __tablename__ = 'produtoIngrediente'
    id = Column(Integer, primary_key=True)

    produto_id = Column(Integer, ForeignKey('produto.id'), nullable=False)
    ingrediente_id = Column(Integer, ForeignKey('ingrediente.id'), nullable=False)

    quantidade_necessaria = Column(Float, nullable=False)  # quanto do produto é necessário

    produto = relationship("Produto", back_populates="ingredientes_necessarios")
    ingrediente = relationship("Ingrediente", back_populates="usado_em_produtos")

    def __repr__(self):
        return f"<ProdutoIngrediente(produto_id={self.produto_id}, ingrediente_id={self.ingrediente_id}, quantidade={self.quantidade_necessaria})>"

    def serialize(self):
        return {
            "produto_id": self.produto_id,
            "ingrediente_id": self.ingrediente_id,
            "quantidade_necessaria": self.quantidade_necessaria
        }

    def save(self, db_session):
        try:
            db_session.add(self)
            db_session.commit()
        except Exception as e:
            db_session.rollback()
            raise e

    def delete(self, db_session):
        try:
            db_session.delete(self)
            db_session.commit()
        except Exception as e:
            db_session.rollback()
            raise e




def init_db():
    Base.metadata.create_all(engine)


if __name__ == '__main__':
    init_db()

