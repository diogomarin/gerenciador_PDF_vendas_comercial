# Gerenciador de PDFs - Importação e Gestão de Itens

Aplicação **FastAPI** que roda apenas localmente, com banco **SQLite**. Importa listas de preço em PDF, permite buscar itens, montar carrinhos e gerar mensagens para WhatsApp.

## Funcionalidades

- **Upload de PDFs**: extrai a tabela de itens (código, descrição, qtd emb, preço) e grava no SQLite.
- **Seleção de tabelas importadas** e **busca** por descrição (vários termos separados por `,` ou `;`).
- **Carrinhos**: adicione itens, salve com um apelido, filtre por tabela de referência e delete.
- **Mensagem para WhatsApp** a partir de um carrinho salvo.

## Estrutura

- `app.py`: cria a aplicação FastAPI, monta `/static` e cria as tabelas na inicialização.
- `database.py`: engine/sessão SQLAlchemy (arquivo `gerenciador.db` na raiz, ignorado pelo git).
- `models.py`: `Importacao`, `PDFData`, `Carrinho`, `ItemCarrinho`.
- `pdf_service.py`: extração do PDF (pdfplumber + pandas) e gravação da importação.
- `routes.py`: rotas e templates Jinja2 (`templates/`, `static/`).
- `seed.py`: importa os PDFs de `data/` para o banco local.
- `tests/`: testes usando os PDFs de `data/` com um SQLite em memória.

## Como executar

Requer [uv](https://docs.astral.sh/uv/).

```bash
uv sync
uv run python seed.py            # opcional: importa os PDFs de exemplo em data/
uv run uvicorn app:app --reload
```

Acesse <http://127.0.0.1:8000> (documentação automática da API em `/docs`).

> Se o projeto estiver numa pasta do OneDrive e o `uv sync` falhar com erro de hardlink, use `UV_LINK_MODE=copy`.

### Alternativa sem uv (pip)

```bash
python -m venv .venv
.venv\Scripts\activate          # Windows (Linux/macOS: source .venv/bin/activate)
pip install -r requirements.txt
python seed.py
uvicorn app:app --reload
```

## Dependências

A fonte de verdade é o `pyproject.toml` (versões travadas no `uv.lock`). O `requirements.txt` é apenas gerado a partir deles, para quem usar pip, e não deve ser editado à mão. Para regenerá-lo após alterar dependências:

```bash
uv export --no-hashes --no-dev --no-emit-project -o requirements.txt
```

## Testes

```bash
uv run pytest
```
