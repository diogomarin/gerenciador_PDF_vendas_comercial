from sqlalchemy import Column, Date, Float, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from database import Base


# Tabela de gerenciamento de importações
class Importacao(Base):
    __tablename__ = "importacao"

    id = Column(Integer, primary_key=True)
    apelido = Column(String(50), unique=True)
    data_referencia = Column(Date)
    registros = relationship("PDFData", backref="importacao", cascade="all, delete-orphan")


# Tabela para armazenar os dados do PDF
class PDFData(Base):
    __tablename__ = "pdf_data"

    id = Column(Integer, primary_key=True)
    codigo = Column(String(50))
    descricao = Column(String(255))
    qtd_emb = Column(String(50))
    preco = Column(Float)
    importacao_id = Column(Integer, ForeignKey("importacao.id"))


# Tabela de carrinhos de itens
class Carrinho(Base):
    __tablename__ = "carrinho"

    id = Column(Integer, primary_key=True)
    apelido = Column(String(50), nullable=False)
    apelido_importacao = Column(String(50), nullable=False)
    itens = relationship("ItemCarrinho", backref="carrinho", cascade="all, delete-orphan")

    @property
    def total(self):
        return sum(item.preco for item in self.itens)


# Itens dentro do carrinho
class ItemCarrinho(Base):
    __tablename__ = "item_carrinho"

    id = Column(Integer, primary_key=True)
    descricao = Column(String(255))
    preco = Column(Float)
    carrinho_id = Column(Integer, ForeignKey("carrinho.id"))
