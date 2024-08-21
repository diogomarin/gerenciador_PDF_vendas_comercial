from flask_sqlalchemy import SQLAlchemy

# Inicializa o SQLAlchemy
db = SQLAlchemy()

# Definição do modelo básico para armazenar os dados do PDF
class PDFData(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    codigo = db.Column(db.String(50))
    descricao = db.Column(db.String(255))
    qtd_emb = db.Column(db.String(50))
    preco = db.Column(db.Float)

    def __init__(self, codigo, descricao, qtd_emb, preco):
        self.codigo = codigo
        self.descricao = descricao
        self.qtd_emb = qtd_emb
        self.preco = preco
