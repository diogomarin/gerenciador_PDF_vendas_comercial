import streamlit as st
import pandas as pd
import sqlite3
import pdfplumber
from datetime import datetime

# Função para extrair dados do PDF
def extract_data_from_pdf(pdf_file):
    data = []
    with pdfplumber.open(pdf_file) as pdf:
        for page in pdf.pages:
            table = page.extract_table()
            if table:
                data.extend(table)
    
    # Convertendo a lista de listas para um DataFrame
    df = pd.DataFrame(data[1:], columns=["CÓDIGO", "DESCRIÇÃO", "QTD EMB", "PREÇO"])
    return df

# Conexão com o banco de dados SQLite
def init_db():
    conn = sqlite3.connect('tabelas.db')
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS tabelas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            apelido TEXT,
            cliente TEXT,
            referencia TEXT
        )
    ''')
    c.execute('''
        CREATE TABLE IF NOT EXISTS carrinhos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            descricao TEXT,
            quantidade INTEGER,
            preco REAL,
            total REAL,
            data TEXT
        )
    ''')
    c.execute('''
        CREATE TABLE IF NOT EXISTS carrinho_registros (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            carrinho_id INTEGER,
            item_id INTEGER,
            descricao TEXT,
            quantidade INTEGER,
            preco REAL,
            total REAL,
            data TEXT,
            FOREIGN KEY (carrinho_id) REFERENCES carrinhos (id)
        )
    ''')
    conn.commit()
    return conn, c

# Função para salvar a tabela no banco de dados
def save_table_to_db(conn, df, apelido, cliente, referencia):
    df.to_sql(apelido, conn, if_exists='replace', index=False)
    c = conn.cursor()
    c.execute('''
        INSERT INTO tabelas (apelido, cliente, referencia)
        VALUES (?, ?, ?)
    ''', (apelido, cliente, referencia))
    conn.commit()

# Função para salvar o carrinho no banco de dados
def save_carrinho_to_db(conn, carrinho):
    c = conn.cursor()
    c.execute('''
        INSERT INTO carrinhos (descricao, quantidade, preco, total, data)
        VALUES (?, ?, ?, ?, ?)
    ''', (carrinho['descricao'], carrinho['quantidade'], carrinho['preco'], carrinho['total'], carrinho['data']))
    carrinho_id = c.lastrowid
    conn.commit()
    return carrinho_id

# Função para adicionar itens ao carrinho no banco de dados
def add_items_to_carrinho(conn, carrinho_id, items):
    c = conn.cursor()
    for item in items:
        c.execute('''
            INSERT INTO carrinho_registros (carrinho_id, item_id, descricao, quantidade, preco, total, data)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (carrinho_id, item['item_id'], item['descricao'], item['quantidade'], item['preco'], item['total'], item['data']))
    conn.commit()

# Tela 1: Importar PDF e salvar tabela
def tela_importar_pdf():
    st.header("Importar PDF e Salvar Tabela")

    uploaded_file = st.file_uploader("Escolha um arquivo PDF", type="pdf")
    
    if uploaded_file:
        st.success("PDF importado com sucesso! Aguarde, carregando a tabela...")
        df = extract_data_from_pdf(uploaded_file)
        st.write("Nomes das Colunas:")
        st.write(df.columns.tolist())
        st.write("Pré-visualização dos dados:")
        st.write(df)
        
        st.header("Detalhes da Tabela")
        apelido = st.text_input("Apelido da Tabela")
        cliente = st.text_input("Cliente")
        referencia = st.date_input("Data de Referência", format="YYYY-MM-DD")
        
        if st.button("Salvar Tabela no Banco de Dados"):
            referencia_formatada = referencia.strftime("%m-%Y")
            save_table_to_db(conn, df, apelido, cliente, referencia_formatada)
            st.success("Tabela salva no banco de dados com sucesso!")

# Tela 2: Selecionar tabela, buscar e adicionar itens ao carrinho
def tela_selecionar_tabela():
    st.header("Selecionar Tabela e Adicionar Itens ao Carrinho")

    c.execute("SELECT apelido FROM tabelas")
    tabelas = c.fetchall()
    
    carrinho = st.session_state.get('carrinho', [])
    carrinho_id = st.session_state.get('carrinho_id', None)

    if tabelas:
        escolha_tabela = st.selectbox("Escolha uma tabela para trabalhar", [t[0] for t in tabelas])
        if escolha_tabela:
            df_selecionada = pd.read_sql_query(f"SELECT * FROM '{escolha_tabela}'", conn)
            st.write("Tabela Selecionada:")
            st.dataframe(df_selecionada.style.set_properties(**{'width': '800px'}, subset=['DESCRIÇÃO']))
            
            descricao_busca = st.text_input("Buscar Descrição")
            if descricao_busca:
                resultado_busca = df_selecionada[df_selecionada["DESCRIÇÃO"].str.contains(descricao_busca, case=False)]
                st.write("Resultados da Busca:")
                st.dataframe(resultado_busca.style.set_properties(**{'width': '800px'}, subset=['DESCRIÇÃO']))
                
                selected_rows = st.multiselect(
                    "Selecione os itens para adicionar ao carrinho",
                    resultado_busca.index,
                    format_func=lambda x: resultado_busca.loc[x, "DESCRIÇÃO"]
                )
                
                if st.button("Adicionar Selecionados ao Carrinho"):
                    for idx in selected_rows:
                        row = resultado_busca.loc[idx]
                        carrinho.append({
                            'item_id': idx,
                            'descricao': row['DESCRIÇÃO'],
                            'quantidade': row['QTD EMB'],
                            'preco': float(row['PREÇO'].replace('R$', '').replace(',', '.').strip()),
                            'total': float(row['QTD EMB']) * float(row['PREÇO'].replace('R$', '').replace(',', '.').strip()),
                            'data': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        })
                    st.session_state['carrinho'] = carrinho
                    st.success("Itens adicionados ao carrinho com sucesso!")

    if carrinho:
        st.header("Carrinho")
        df_carrinho = pd.DataFrame(carrinho)
        st.write(df_carrinho)
        total_geral = df_carrinho['total'].sum()
        st.write(f"Total Geral: R$ {total_geral:.2f}")
        
        items_to_remove = st.multiselect(
            "Selecione os itens para remover do carrinho",
            df_carrinho.index,
            format_func=lambda x: df_carrinho.loc[x, "descricao"]
        )
        
        if st.button("Remover Selecionados do Carrinho"):
            carrinho = [item for idx, item in enumerate(carrinho) if idx not in items_to_remove]
            st.session_state['carrinho'] = carrinho
            st.experimental_rerun()  # Atualiza a interface após a remoção dos itens
            st.success("Itens removidos do carrinho com sucesso!")
        
        if st.button("Fechar Carrinho"):
            if carrinho_id is None:
                carrinho_id = save_carrinho_to_db(conn, {'descricao': 'Carrinho de Itens', 'quantidade': len(carrinho), 'preco': total_geral, 'total': total_geral, 'data': datetime.now().strftime("%Y-%m-%d %H:%M:%S")})
                st.session_state['carrinho_id'] = carrinho_id
            add_items_to_carrinho(conn, carrinho_id, carrinho)
            st.success("Carrinho fechado e salvo no banco de dados com sucesso!")
            st.session_state['carrinho'] = []
            st.session_state['carrinho_id'] = None
            st.experimental_rerun()  # Atualiza a interface após fechar o carrinho

# Tela 3: Histórico de carrinhos fechados e visualização dos itens
def tela_historico_carrinhos():
    st.header("Histórico de Carrinhos Fechados")

    carrinho_historico = pd.read_sql_query("SELECT id, descricao, quantidade, total, data FROM carrinhos", conn)
    st.write(carrinho_historico)
    
    selected_carrinho = st.selectbox("Selecione um carrinho para ver os itens", carrinho_historico['id'] if not carrinho_historico.empty else [])
    if selected_carrinho:
        itens_carrinho = pd.read_sql_query(f"SELECT * FROM carrinho_registros WHERE carrinho_id = {selected_carrinho}", conn)
        st.write(itens_carrinho)

# Inicialização do banco de dados
conn, c = init_db()

# Menu de navegação com botões
st.sidebar.title("Navegação")
if st.sidebar.button("Importar PDF e Salvar"):
    st.session_state.page = "importar"
if st.sidebar.button("Selecionar Tabela e Adicionar Itens ao Carrinho"):
    st.session_state.page = "selecionar"
if st.sidebar.button("Histórico de Carrinhos Fechados"):
    st.session_state.page = "historico"

# Exibição das telas com base no estado da sessão
if st.session_state.get("page") == "importar":
    tela_importar_pdf()
elif st.session_state.get("page") == "selecionar":
    tela_selecionar_tabela()
elif st.session_state.get("page") == "historico":
    tela_historico_carrinhos()
else:
    st.session_state.page = "importar"
    tela_importar_pdf()
