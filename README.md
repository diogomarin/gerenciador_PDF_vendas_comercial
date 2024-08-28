# Gerenciador de PDFs - Importação e Gestão de Itens

Este projeto é uma aplicação Flask para importar, processar e gerenciar dados extraídos de PDFs. A aplicação permite carregar PDFs, visualizar itens importados, adicionar itens a carrinhos e visualizar carrinhos salvos.

## Funcionalidades

- **Upload de PDFs**: Carregue arquivos PDF e processe os dados, armazenando-os no banco de dados PostgreSQL.
- **Seleção de Tabelas Importadas**: Selecione tabelas previamente importadas para visualização e manipulação.
- **Busca e Filtro de Itens**: Realize buscas na tabela importada para filtrar itens com base na descrição.
- **Gerenciamento de Carrinhos**: Adicione itens ao carrinho, salve carrinhos com um apelido e visualize carrinhos salvos.
- **Visualização de Carrinhos**: Veja todos os carrinhos salvos, com a opção de filtrar por tabela de referência.

## Estrutura do Projeto

- **`app.py`**: Arquivo principal para iniciar o aplicativo Flask.
- **`models.py`**: Define os modelos de dados usando SQLAlchemy.
- **`routes.py`**: Contém todas as rotas da aplicação, incluindo o processamento de PDFs, gerenciamento de carrinhos, e busca de itens.
- **`index.html`**: Página inicial com as opções principais da aplicação.
- **`upload_pdf_form.html`**: Formulário para upload de PDFs.
- **`select_table.html`**: Interface para seleção de tabela, busca de itens, e gerenciamento de carrinho.
- **`view_carts.html`**: Página para visualizar e filtrar carrinhos salvos.
- **`main.js`**: JavaScript para manipulação dinâmica da interface, incluindo adicionar itens ao carrinho e manipular o DOM.

## Tabelas do Banco de Dados e Relações

A aplicação utiliza PostgreSQL como banco de dados, gerenciado pelo SQLAlchemy. Abaixo estão as principais tabelas e suas relações:

- **`PDFData`**:
  - Armazena dados extraídos dos PDFs.
  - Colunas principais: `id`, `codigo`, `descricao`, `qtd_emb`, `preco`, `importacao_id`.
  - Relação: Cada `PDFData` está associado a uma `Importacao` através de `importacao_id`.

- **`Importacao`**:
  - Representa as tabelas importadas a partir dos PDFs.
  - Colunas principais: `id`, `apelido`, `data_referencia`.
  - Relação: Uma `Importacao` pode ter vários registros na tabela `PDFData`. Também está relacionada a múltiplos `Carrinho`.

- **`Carrinho`**:
  - Armazena itens que foram selecionados pelo usuário de uma tabela de importação.
  - Colunas principais: `id`, `apelido`, `apelido_importacao`.
  - Relação: Cada `Carrinho` está vinculado a uma `Importacao` por `apelido_importacao` e possui múltiplos `ItemCarrinho`.

- **`ItemCarrinho`**:
  - Armazena itens específicos dentro de um carrinho.
  - Colunas principais: `id`, `descricao`, `preco`, `carrinho_id`.
  - Relação: Cada `ItemCarrinho` está associado a um `Carrinho`.

## Configuração e Execução

Para configurar e executar a aplicação, siga os passos abaixo:

1. **Clone o repositório:**

   git clone <https://github.com/seu-usuario/seu-repositorio.git>

   cd seu-repositorio

2. **Instale as dependências**

    pip install -r requirements.txt

3. **Instale o PostgreSQL**

    Certifique-se de que o PostgreSQL esteja instalado em sua máquina.

4. **Configure o Banco de Dados**

    Crie um banco de dados chamado "mydatabase".

    Por padrão, a aplicação está configurada para conectar-se ao PostgreSQL com o usuário postgres e senha postgres. Se necessário, você pode alterar essas configurações no arquivo app.py

    app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres:postgres@localhost:5432/mydatabase'

5. **Execute as migrações para configurar o banco de dados**

    flask db upgrade

6. **Inicie a aplicação**

    flask run

7. **Acesse aplicação em seu navegador**

    <http://127.0.0.1:5000>
