from agents.analyzer import analyze
from utils.embeddings import create_vectorstore
from utils.invoice_index import (
    DATA_DIR,
    add_invoice_record,
    allocate_invoice_storage,
    build_invoice_record,
    list_invoices,
    resolve_project_path,
)
from utils.loader import load_and_split_pdf


def already_indexed_paths():
    paths = set()
    for record in list_invoices():
        file_path = record.get("file_path")
        if file_path:
            paths.add(resolve_project_path(file_path).resolve())
    return paths


def index_pdf(pdf_path):
    invoice_id, _, vectorstore_path = allocate_invoice_storage(pdf_path.name)
    chunks = load_and_split_pdf(str(pdf_path))

    for chunk in chunks:
        chunk.metadata = {
            **(chunk.metadata or {}),
            "invoice_id": invoice_id,
            "original_filename": pdf_path.name,
            "stored_filename": pdf_path.name,
        }

    create_vectorstore(chunks, path=str(vectorstore_path))
    extracted = analyze("extract all fields", chunks)
    record = build_invoice_record(
        invoice_id=invoice_id,
        original_filename=pdf_path.name,
        file_path=pdf_path,
        vectorstore_path=vectorstore_path,
        extracted=extracted,
        chunk_count=len(chunks),
    )
    add_invoice_record(record)
    return record


indexed = already_indexed_paths()
pdfs = [path for path in DATA_DIR.glob("*.pdf") if path.resolve() not in indexed]

if not pdfs:
    print("No new PDFs to index.")
else:
    for pdf in pdfs:
        record = index_pdf(pdf)
        print(f"Indexed {pdf.name} as {record['invoice_id']}")
