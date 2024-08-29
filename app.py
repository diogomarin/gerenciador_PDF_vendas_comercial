from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from dotenv import load_dotenv
import os
from models import db

# Carrega variáveis de ambiente do .env se existirem
load_dotenv()

app = Flask(__name__)


# Configuração para Azure
if 'WEBSITE_HOSTNAME' not in os.environ:
    # Desenvolvimento local, onde usaremos variáveis ​​de ambiente
    print("Loading config.development and environment variables from .env.sample file.")
    app.config.from_object('azureproject.development')
    
else:
    # Production
    print("Loading config.production.")
    app.config.from_object('azureproject.production')

app.config.update(
    SQLALCHEMY_DATABASE_URI=app.config.get('DATABASE_URI'),
    SQLALCHEMY_TRACK_MODIFICATIONS=False,
)

'''
# Configuração para localhost
# Desenvolvimento local: usa variáveis de ambiente do arquivo .env
print("Carregando configuração de desenvolvimento.")
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('SQLALCHEMY_DATABASE_URI')

#Carregando a chave secreta do Flask para proteção de sessões e CSRF
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'defaultsecretkey')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
'''

# Inicializa o banco de dados
db.init_app(app)

# Habilita comandos Flask-Migrate para migração do banco de dados
migrate = Migrate(app, db)

from routes import *

if __name__ == '__main__':
    app.run(debug=True)
