from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

# Inicializa o SQLAlchemy
db = SQLAlchemy()

# Tabela de gerenciamento de importações
class Importacao(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    apelido = db.Column(db.String(50), unique=True)
    data_referencia = db.Column(db.Date)
    registros = db.relationship('PDFData', backref='importacao', lazy=True)

# Tabela para armazenar os dados do PDF
class PDFData(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    codigo = db.Column(db.String(50))
    descricao = db.Column(db.String(255))
    qtd_emb = db.Column(db.String(50))
    preco = db.Column(db.Float)
    importacao_id = db.Column(db.Integer, db.ForeignKey('importacao.id'))

    def __init__(self, codigo, descricao, qtd_emb, preco, importacao_id):
        self.codigo = codigo
        self.descricao = descricao
        self.qtd_emb = qtd_emb
        self.preco = preco
        self.importacao_id = importacao_id

# Tabela de carrinhos de itens
class Carrinho(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    apelido = db.Column(db.String(50), nullable=False)
    apelido_importacao = db.Column(db.String(50), nullable=False)
    itens = db.relationship('ItemCarrinho', backref='carrinho', lazy=True)

    @property
    def total(self):
        return sum(item.preco for item in self.itens)

    def total_formatado(self):
        return f"R${self.total / 100:,.2f}".replace(',', 'v').replace('.', ',').replace('v', '.')

# Itens dentro do carrinho
class ItemCarrinho(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    descricao = db.Column(db.String(255))
    preco = db.Column(db.Float)
    carrinho_id = db.Column(db.Integer, db.ForeignKey('carrinho.id'))