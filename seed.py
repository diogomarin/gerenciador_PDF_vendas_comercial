"""Importa os PDFs de exemplo da pasta data/ para o banco SQLite local.

Uso: uv run python seed.py
O apelido é o nome do arquivo; a data de referência vem do sufixo DD-MM (ano atual).
"""
import re
from datetime import date

import models  # noqa: F401
from database import BASE_DIR, Base, SessionLocal, engine
from pdf_service import PDFInvalido, importar_pdf


def main():
    Base.metadata.create_all(engine)
    with SessionLocal() as db:
        for pdf in sorted((BASE_DIR / "data").glob("*.pdf")):
            m = re.search(r"(\d{2})-(\d{2})$", pdf.stem)
            ref = date(date.today().year, int(m[2]), int(m[1])) if m else date.today()
            try:
                with open(pdf, "rb") as f:
                    n = importar_pdf(db, f, pdf.stem, ref)
                print(f"{pdf.name}: {n} itens importados")
            except PDFInvalido as e:
                print(f"{pdf.name}: ignorado ({e})")


if __name__ == "__main__":
    main()
