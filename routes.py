from flask import render_template, request, jsonify, redirect, url_for, flash
from app import app, db
from models import PDFData, Importacao, Carrinho, ItemCarrinho
import pdfplumber
import pandas as pd
from datetime import datetime
import json


# Função para extrair dados do PDF
def extract_data_from_pdf(pdf_file):
    try:
        data = []
        with pdfplumber.open(pdf_file) as pdf:
            for page in pdf.pages:
                table = page.extract_table()
                if table:
                    data.extend(table)
        
        # Convertendo a lista de listas para um DataFrame
        df = pd.DataFrame(data[1:], columns=["CÓDIGO", "DESCRIÇÃO", "QTD EMB", "PREÇO"])
        return df
    except Exception as e:
        print(f"Error extracting data from PDF: {e}")
        raise

# Rota para upload de PDF e extração de dados
@app.route('/upload_pdf', methods=['POST'])
def upload_pdf():
    try:
        if 'file' not in request.files or 'apelido' not in request.form or 'data_referencia' not in request.form:
            return render_template('upload_pdf_form.html', error="Missing data"), 400

        file = request.files['file']
        apelido = request.form['apelido']
        data_referencia = request.form['data_referencia']

        if file.filename == '':
            return render_template('upload_pdf_form.html', error="No selected file"), 400

        # Criar uma nova importação
        nova_importacao = Importacao(apelido=apelido, data_referencia=datetime.strptime(data_referencia, '%Y-%m-%d').date())
        db.session.add(nova_importacao)
        db.session.commit()

        # Tente extrair os dados do PDF
        df = extract_data_from_pdf(file)
        
        # Salvar os dados no banco de dados vinculando à nova importação
        for index, row in df.iterrows():
            preco_str = row['PREÇO'].replace('R$', '').replace('.', '').replace(',', '.').strip()
            try:
                preco = float(preco_str)
            except ValueError:
                return render_template('upload_pdf_form.html', error=f"Invalid price format: {row['PREÇO']}"), 400

            new_data = PDFData(
                codigo=row['CÓDIGO'], 
                descricao=row['DESCRIÇÃO'], 
                qtd_emb=row['QTD EMB'], 
                preco=preco,  # Mantenha o valor como float sem dividir
                importacao_id=nova_importacao.id
            )
            db.session.add(new_data)
        db.session.commit()

        # Renderiza a página com uma mensagem de sucesso e o botão de "Selecionar Tabela"
        return render_template('upload_pdf_form.html', success=True)

    except Exception as e:
        print(f"Error processing the PDF: {e}")
        return render_template('upload_pdf_form.html', error="Internal Server Error"), 500
    
    
# Rota para carregar e exibir uma tabela existente
@app.route('/select_table', methods=['GET', 'POST'])
def select_table():
    if request.method == 'POST':
        importacao_id = request.form['importacao_id']
        importacao = Importacao.query.get(importacao_id)
        if not importacao:
            return render_template('select_table.html', data=[], importacao=None, error="Tabela não encontrada.")
        
        data = PDFData.query.filter_by(importacao_id=importacao_id).all()

        # Formatar os preços antes de passar para o template
        for item in data:
            item.preco_formatado = f"R${item.preco / 100:,.2f}".replace(',', 'v').replace('.', ',').replace('v', '.')

        return render_template('select_table.html', data=data, importacao=importacao)
    else:
        importacoes = Importacao.query.all()
        return render_template('select_table.html', importacoes=importacoes, importacao=None)

# Rota para busca de itens dentro da tabela selecionada
@app.route('/search_items', methods=['POST'])
def search_items():
    importacao_id = request.form['importacao_id']
    search_query = request.form['search_query']

    # Divide a consulta em termos, separando por vírgula ou ponto e vírgula
    search_terms = [term.strip() for term in search_query.replace(';', ',').split(',')]

    # Filtra os itens que correspondem a qualquer um dos termos
    items = PDFData.query.filter(
        PDFData.importacao_id == importacao_id,
        db.or_(*[PDFData.descricao.ilike(f"%{term}%") for term in search_terms])
    ).all()

    # Formatar os preços antes de passar para o template
    for item in items:
        item.preco_formatado = f"R$ {item.preco:,.2f}".replace(",", "v").replace(".", ",").replace("v", ".")

    # Obtenha os dados da importação para renderizar a mesma página com os itens filtrados
    importacao = Importacao.query.get(importacao_id)
    
    return render_template('select_table.html', data=items, importacao=importacao, importacoes=Importacao.query.all())

# Rota para adicionar itens ao carrinho
@app.route('/add_to_cart', methods=['POST'])
def add_to_cart():
    descricao = request.form['descricao']
    quantidade = int(request.form['quantidade'])
    preco = float(request.form['preco'])
    importacao_id = request.form['importacao_id']

    carrinho = Carrinho(importacao_id=importacao_id)
    db.session.add(carrinho)
    db.session.commit()

    item = ItemCarrinho(descricao=descricao, quantidade=quantidade, preco=preco, carrinho_id=carrinho.id)
    db.session.add(item)
    db.session.commit()

    return jsonify({"message": "Item added to cart"}), 200

# Rota para salvar o carrinho de itens selecionados
@app.route('/save_cart', methods=['POST'])
def save_cart():
    cart_items = request.form.get('cart_items')
    apelido = request.form.get('apelido')
    apelido_importacao = request.form.get('apelido_importacao')
    
    if not cart_items:
        return render_template('select_table.html', data=[], importacao=None, error="Nenhum item no carrinho para salvar.")
    
    cart_items = json.loads(cart_items)

    # Cria um novo carrinho com o apelido e o apelido da importação
    carrinho = Carrinho(apelido=apelido, apelido_importacao=apelido_importacao)
    db.session.add(carrinho)
    db.session.commit()

    # Adiciona os itens ao carrinho
    for item in cart_items:
        item_carrinho = ItemCarrinho(
            descricao=item['descricao'],
            preco=item['preco'],
            carrinho_id=carrinho.id
        )
        db.session.add(item_carrinho)
    
    db.session.commit()

    return redirect(url_for('view_carts'))

# Rota para visualizar carrinhos salvos na página inicial
@app.route('/view_carts')
def view_carts():
    apelido_importacao = request.args.get('apelido_importacao')
    
    if apelido_importacao:
        carrinhos = Carrinho.query.filter_by(apelido_importacao=apelido_importacao).all()
    else:
        carrinhos = Carrinho.query.all()

    # Formatar os preços em cada item e no total do carrinho
    for carrinho in carrinhos:
        for item in carrinho.itens:
            item.preco_formatado = f"R$ {item.preco:,.2f}".replace(",", "v").replace(".", ",").replace("v", ".")
        carrinho.total_formatado = f"R$ {carrinho.total:,.2f}".replace(",", "v").replace(".", ",").replace("v", ".")

    importacoes = Importacao.query.all()
    
    return render_template('view_carts.html', carrinhos=carrinhos, importacoes=importacoes)

@app.route('/send_cart', methods=['POST'])
def send_cart():
    selected_carts = request.form.getlist('selected_carts')
    nome_cliente = request.form.get('nome_cliente')
    venda_realizada = request.form.get('venda_realizada') == 'on'

    if not selected_carts or not nome_cliente:
        flash("Você deve selecionar um carrinho e fornecer o nome do cliente.", "error")
        return redirect(url_for('view_carts'))

    # Gera a mensagem personalizada
    mensagens = []
    for cart_id in selected_carts:
        carrinho = Carrinho.query.get(cart_id)
        itens_mensagem = "\n".join([f"{item.descricao}: R${item.preco}" for item in carrinho.itens])
        mensagem = (
            f"Olá {nome_cliente},\n"
            f"Aqui estão os itens do seu carrinho:\n{itens_mensagem}\n"
            f"Total: R${carrinho.total:.2f}\n"
        )
        mensagens.append(mensagem)

        # Atualiza o carrinho com os detalhes do envio
        carrinho.enviado_para = nome_cliente
        carrinho.data_envio = datetime.utcnow()
        db.session.commit()

    return render_template('send_cart.html', mensagens=mensagens, nome_cliente=nome_cliente, venda_realizada=venda_realizada)

# Rota para deletar um carrinho
@app.route('/delete_cart/<int:cart_id>', methods=['POST'])
def delete_cart(cart_id):
    try:
        cart = Carrinho.query.get(cart_id)
        if not cart:
            return jsonify({'error': 'Carrinho não encontrado'}), 404

        db.session.delete(cart)
        db.session.commit()
        return jsonify({'message': 'Carrinho deletado com sucesso'}), 200
    except Exception as e:
        # Log the error for further inspection
        print(f"Erro ao deletar o carrinho: {e}")
        return jsonify({'error': 'Erro interno do servidor'}), 500


# Rota para a página inicial, onde o usuário escolhe entre upload ou seleção de tabela
@app.route('/')
def index():
    return render_template('index.html')

# Rota para exibir o formulário de upload de PDF
@app.route('/upload_pdf_form', methods=['GET'])
def upload_pdf_form():
    return render_template('upload_pdf_form.html')