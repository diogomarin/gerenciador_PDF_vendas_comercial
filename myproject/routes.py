from flask import render_template, request, jsonify
from app import app, db
from models import PDFData
import pdfplumber
import pandas as pd

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
        if 'file' not in request.files:
            return jsonify({"error": "No file part"}), 400

        file = request.files['file']

        if file.filename == '':
            return jsonify({"error": "No selected file"}), 400

        # Tente extrair os dados do PDF
        df = extract_data_from_pdf(file)
        
        # Salvar os dados no banco de dados
        for index, row in df.iterrows():
            # Limpar o valor do preço
            preco_str = row['PREÇO'].replace('R$', '').replace('.', '').replace(',', '.').strip()
            try:
                preco = float(preco_str)
            except ValueError:
                return jsonify({"error": f"Invalid price format: {row['PREÇO']}"}), 400

            new_data = PDFData(
                codigo=row['CÓDIGO'], 
                descricao=row['DESCRIÇÃO'], 
                qtd_emb=row['QTD EMB'], 
                preco=preco
            )
            db.session.add(new_data)
        db.session.commit()

        return jsonify({"message": "File processed and data saved"}), 200

    except Exception as e:
        print(f"Error processing the PDF: {e}")
        return jsonify({"error": "Internal Server Error"}), 500

# Rota para exibir os dados salvos
@app.route('/data')
def data():
    data = PDFData.query.all()
    return render_template('data.html', data=data)

# Rota para exibir o formulário de upload
@app.route('/')
def index():
    print("Rota principal acessada")
    return render_template('upload.html')
