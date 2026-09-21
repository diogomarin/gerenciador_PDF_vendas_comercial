import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app import app
from database import Base, get_db

DATA = Path(__file__).resolve().parent.parent / "data"
PDFS = sorted(DATA.glob("*.pdf"))


@pytest.fixture
def client():
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine, expire_on_commit=False)

    def override():
        with Session() as s:
            yield s

    app.dependency_overrides[get_db] = override
    yield TestClient(app)
    app.dependency_overrides.clear()


def upload(client, pdf, apelido="lista"):
    with open(pdf, "rb") as f:
        return client.post(
            "/upload_pdf",
            files={"file": (pdf.name, f, "application/pdf")},
            data={"apelido": apelido, "data_referencia": "2026-09-02"},
        )


def test_paginas(client):
    for path in ["/", "/upload_pdf_form", "/select_table", "/view_carts", "/static/main.js"]:
        assert client.get(path).status_code == 200, path


def test_fluxo_completo(client):
    assert PDFS, "sem PDFs em data/"
    r = upload(client, PDFS[0])
    assert r.status_code == 200 and "File processed" in r.text

    # apelido duplicado -> 400 com mensagem
    assert upload(client, PDFS[0]).status_code == 400

    r = client.post("/select_table", data={"importacao_id": 1})
    assert "ABS C/AB SV ALWAYS BAS 18X08UN" in r.text  # 1º item não é descartado
    assert "1.175,04" in r.text  # milhar/decimal pt-BR

    r = client.post("/search_items", data={"importacao_id": 1, "search_query": "always; sempre livre"})
    assert "ALWAYS BAS 18X08UN" in r.text and "SEMPRE LIVRE ADAPT" in r.text and "SYM BAS 60X8UN" not in r.text

    cart = [{"descricao": "ITEM A", "preco": "1.234,50"}, {"descricao": "ITEM B", "preco": "10,00"}]
    r = client.post(
        "/save_cart",
        data={"cart_items": json.dumps(cart), "apelido": "c1", "apelido_importacao": "lista"},
        follow_redirects=False,
    )
    assert r.status_code == 303
    r = client.get("/view_carts", params={"apelido_importacao": "lista"})
    assert "1.244,50" in r.text and "ITEM A" in r.text

    assert client.post("/delete_cart/1").status_code == 200
    assert client.post("/delete_cart/1").status_code == 404
    assert "ITEM A" not in client.get("/view_carts").text


def test_pdf_invalido(client):
    r = client.post(
        "/upload_pdf",
        files={"file": ("x.pdf", b"nao e pdf", "application/pdf")},
        data={"apelido": "x", "data_referencia": "2026-09-02"},
    )
    assert r.status_code in (400, 500)
