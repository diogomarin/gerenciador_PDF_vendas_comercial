import json
from datetime import datetime
from pathlib import Path

from fastapi import APIRouter, Depends, Form, Request, UploadFile
from fastapi.responses import JSONResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import or_
from sqlalchemy.orm import Session

from database import BASE_DIR, get_db
from models import Carrinho, Importacao, ItemCarrinho, PDFData
from pdf_service import PDFInvalido, format_brl, importar_pdf

router = APIRouter()
templates = Jinja2Templates(directory=Path(BASE_DIR) / "templates")


def _render(request: Request, name: str, status_code: int = 200, **context):
    return templates.TemplateResponse(request, name, context, status_code=status_code)


# Rota para a página inicial, onde o usuário escolhe entre upload ou seleção de tabela
@router.get("/")
def index(request: Request):
    return _render(request, "index.html")


# Rota para exibir o formulário de upload de PDF
@router.get("/upload_pdf_form")
def upload_pdf_form(request: Request):
    return _render(request, "upload_pdf_form.html")


# Rota para upload de PDF e extração de dados
@router.post("/upload_pdf")
def upload_pdf(
    request: Request,
    file: UploadFile,
    apelido: str = Form(...),
    data_referencia: str = Form(...),
    db: Session = Depends(get_db),
):
    if not file.filename:
        return _render(request, "upload_pdf_form.html", 400, error="No selected file")
    try:
        data = datetime.strptime(data_referencia, "%Y-%m-%d").date()
        importar_pdf(db, file.file, apelido, data)
    except (PDFInvalido, ValueError) as e:
        db.rollback()
        return _render(request, "upload_pdf_form.html", 400, error=str(e))
    except Exception as e:
        db.rollback()
        print(f"Error processing the PDF: {e}")
        return _render(request, "upload_pdf_form.html", 500, error="Internal Server Error")
    return _render(request, "upload_pdf_form.html", success=True)


# Rota para listar as tabelas importadas
@router.get("/select_table")
def select_table_form(request: Request, db: Session = Depends(get_db)):
    return _render(request, "select_table.html", importacoes=db.query(Importacao).all(), importacao=None)


# Rota para carregar e exibir uma tabela existente
@router.post("/select_table")
def select_table(request: Request, importacao_id: int = Form(...), db: Session = Depends(get_db)):
    importacao = db.get(Importacao, importacao_id)
    if not importacao:
        return _render(request, "select_table.html", data=[], importacao=None, error="Tabela não encontrada.")

    data = db.query(PDFData).filter_by(importacao_id=importacao_id).all()
    for item in data:
        item.preco_formatado = format_brl(item.preco)
    return _render(request, "select_table.html", data=data, importacao=importacao)


# Rota para busca de itens dentro da tabela selecionada
@router.post("/search_items")
def search_items(
    request: Request,
    importacao_id: int = Form(...),
    search_query: str = Form(...),
    db: Session = Depends(get_db),
):
    # Divide a consulta em termos, separando por vírgula ou ponto e vírgula
    terms = [t.strip() for t in search_query.replace(";", ",").split(",") if t.strip()]

    items = (
        db.query(PDFData)
        .filter(
            PDFData.importacao_id == importacao_id,
            or_(*[PDFData.descricao.ilike(f"%{t}%") for t in terms]),
        )
        .all()
    )
    for item in items:
        item.preco_formatado = format_brl(item.preco)

    return _render(
        request,
        "select_table.html",
        data=items,
        importacao=db.get(Importacao, importacao_id),
        importacoes=db.query(Importacao).all(),
    )


# Rota para salvar o carrinho de itens selecionados
@router.post("/save_cart")
def save_cart(
    request: Request,
    cart_items: str = Form(""),
    apelido: str = Form(...),
    apelido_importacao: str = Form(...),
    db: Session = Depends(get_db),
):
    if not cart_items:
        return _render(request, "select_table.html", data=[], importacao=None, error="Nenhum item no carrinho para salvar.")

    carrinho = Carrinho(apelido=apelido, apelido_importacao=apelido_importacao)
    for item in json.loads(cart_items):
        # Preço vem formatado em pt-BR ('1.234,50')
        preco = float(item["preco"].replace(".", "").replace(",", "."))
        carrinho.itens.append(ItemCarrinho(descricao=item["descricao"], preco=preco))
    db.add(carrinho)
    db.commit()

    return RedirectResponse("/view_carts", status_code=303)


# Rota para visualizar carrinhos salvos
@router.get("/view_carts")
def view_carts(request: Request, apelido_importacao: str | None = None, db: Session = Depends(get_db)):
    query = db.query(Carrinho)
    if apelido_importacao:
        query = query.filter_by(apelido_importacao=apelido_importacao)
    carrinhos = query.all()

    for carrinho in carrinhos:
        carrinho.total_formatado = format_brl(carrinho.total)
        for item in carrinho.itens:
            item.preco_formatado = format_brl(item.preco)

    return _render(request, "view_carts.html", carrinhos=carrinhos, importacoes=db.query(Importacao).all())


# Rota para deletar um carrinho
@router.post("/delete_cart/{cart_id}")
def delete_cart(cart_id: int, db: Session = Depends(get_db)):
    cart = db.get(Carrinho, cart_id)
    if not cart:
        return JSONResponse({"error": "Carrinho não encontrado"}, status_code=404)
    db.delete(cart)
    db.commit()
    return {"message": "Carrinho deletado com sucesso"}
