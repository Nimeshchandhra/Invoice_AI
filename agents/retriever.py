from utils.embeddings import load_vectorstore

def retrieve(query, filename):
    db = load_vectorstore(f"vectorstore/{filename}")
    docs = db.similarity_search(query, k=3)
    return docs