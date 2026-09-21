import re
from datetime import date

import pandas as pd
import pdfplumber
from sqlalchemy.orm import Session

from models import Importacao, PDFData

COLUNAS = ["CÓDIGO", "DESCRIÇÃO", "QTD EMB", "PREÇO"]
PRECO_RE = re.compile(r"R\$\s*[\d,]*\.\d{2}")


class PDFInvalido(ValueError):
    pass


def parse_preco(texto: str) -> float:
    # Formato do PDF: 'R$ 1,175.04' -> vírgula é separador de milhar, ponto é decimal
    try:
        return float(texto.replace("R$", "").replace(",", "").strip())
    except ValueError:
        raise PDFInvalido(f"Formato de preço inválido: {texto}")


def format_brl(valor: float) -> str:
    return f"{valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def extract_data_from_pdf(pdf_file) -> pd.DataFrame:
    linhas = []
    with pdfplumber.open(pdf_file) as pdf:
        for page in pdf.pages:
            table = page.extract_table()
            if table:
                linhas.extend(r for r in table if len(r) == len(COLUNAS))
    # Os PDFs não têm cabeçalho; descarta apenas linhas cujo preço não é um preço
    linhas = [r for r in linhas if PRECO_RE.fullmatch((r[3] or "").strip())]
    if not linhas:
        raise PDFInvalido("Nenhuma tabela de itens encontrada no PDF")
    return pd.DataFrame(linhas, columns=COLUNAS)


def importar_pdf(db: Session, pdf_file, apelido: str, data_referencia: date) -> int:
    """Extrai o PDF e grava a importação. Retorna a quantidade de itens."""
    if db.query(Importacao).filter_by(apelido=apelido).first():
        raise PDFInvalido(f"Já existe uma tabela com o apelido '{apelido}'")

    df = extract_data_from_pdf(pdf_file)
    importacao = Importacao(apelido=apelido, data_referencia=data_referencia)
    importacao.registros = [
        PDFData(
            codigo=row["CÓDIGO"],
            descricao=row["DESCRIÇÃO"],
            qtd_emb=row["QTD EMB"],
            preco=parse_preco(row["PREÇO"]),
        )
        for _, row in df.iterrows()
    ]
    db.add(importacao)
    db.commit()
    return len(importacao.registros)
