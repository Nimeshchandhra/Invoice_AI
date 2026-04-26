from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from pypdf import PdfReader
import os
import re


def clean_text(text):
    text = re.sub(r'\s+', ' ', text)   # remove extra spaces
    return text.strip()


def load_and_split_pdf(file_path):
    reader = PdfReader(file_path)
    documents = []

    filename = os.path.basename(file_path)

    for page_number, page in enumerate(reader.pages, start=1):
        text = page.extract_text() or ""

        text = clean_text(text)

        if text:
            documents.append(
                Document(
                    page_content=text,
                    metadata={
                        "source": filename,   # ✅ FIXED
                        "page": page_number
                    },
                )
            )

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=500,
        chunk_overlap=100
    )

    chunks = splitter.split_documents(documents)

    return chunks