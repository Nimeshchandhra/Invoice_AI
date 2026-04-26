from flask import Flask, request, jsonify, render_template
from agents.analyzer import analyze
from agents.retriever import retrieve
from utils.loader import load_and_split_pdf
from utils.embeddings import create_vectorstore

import os, shutil
os.makedirs("data", exist_ok=True)
os.makedirs("vectorstore", exist_ok=True)
app = Flask(__name__)

UPLOAD_FOLDER = "data"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

invoice_store = {}
current_invoice = None


@app.route("/")
def home():
    return render_template("index.html")


# ------------------ UPLOAD ------------------
@app.route("/upload", methods=["POST"])
def upload():
    global invoice_store, current_invoice

    file = request.files.get("file")

    if not file:
        return jsonify({"error": "No file"}), 400

    filename = file.filename
    filepath = os.path.join(UPLOAD_FOLDER, filename)
    file.save(filepath)

    db_path = f"vectorstore/{filename}"

    if os.path.exists(db_path):
        shutil.rmtree(db_path)

    chunks = load_and_split_pdf(filepath)
    create_vectorstore(chunks, db_path)

    data = analyze("extract all fields", chunks)

    invoice_store[filename] = data
    current_invoice = filename

    return jsonify({"message": f"{filename} processed", "data": data})


# ------------------ QUERY ------------------
def answer_query(q, data):
    q = q.lower()

    if not data:
        return "No data available"

    if any(x in q for x in ["amount", "total", "due"]):
        return data.get("total_amount") or "NOT FOUND"

    elif "date" in q:
        return data.get("date") or "NOT FOUND"

    elif "vendor" in q:
        return data.get("vendor") or "NOT FOUND"

    elif any(x in q for x in ["item", "items", "line"]):
        items = data.get("item_name")
        if isinstance(items, list):
            return "\n".join(items)
        return items or "NOT FOUND"

    return str(data)

from agents.retriever import retrieve
from utils.llm import generate_response


@app.route("/query", methods=["POST"])
def query():
    global invoice_store, current_invoice

    q = request.json.get("query").lower()

    if not invoice_store:
        return jsonify({"answer": "No invoices uploaded"})

    data = invoice_store[current_invoice]

    # -------------------------
    # 🔥 USE RULE-BASED FIRST
    # -------------------------
# -------------------------
    # 🔥 USE RULE-BASED FIRST
    # -------------------------
    # 1. Date (Check this first to safely catch "due date")
    if "date" in q:
        return jsonify({"answer": data.get("date") or "NOT FOUND"})

    # 2. Total Amount (Removed 'due' as a standalone trigger to avoid overlaps)
    if any(x in q for x in ["total", "amount", "balance"]):
        return jsonify({"answer": data.get("total_amount") or "NOT FOUND"})

    # 3. Vendor
    if "vendor" in q:
        return jsonify({"answer": data.get("vendor") or "NOT FOUND"})

    # 4. Items (Make sure they aren't asking for the "price" of an item!)
    if any(x in q for x in ["item", "items", "line"]) and "price" not in q:
        items = data.get("item_name")
        if isinstance(items, list):
            return jsonify({"answer": "\n".join(items)})
        return jsonify({"answer": items or "NOT FOUND"})
    # -------------------------
    # 🤖 FALLBACK TO RAG
    # -------------------------
# -------------------------
    # 🤖 FALLBACK TO RAG
    # -------------------------
    try:
        from agents.retriever import retrieve
        from utils.llm import generate_response

        docs = retrieve(q, current_invoice)
        context = "\n".join([d.page_content for d in docs])

        prompt = f"""
Answer ONLY from context.
Rules:
- No guessing
- No calculation
- If not found → NOT FOUND
- Keep answer short

Context:
{context}

Question:
{q}
"""
        answer = generate_response(prompt)
        return jsonify({"answer": answer})
        
    except Exception as e:
        # If the LLM or Retriever fails, print the error to your terminal and return a safe message to the user
        print(f"RAG Error: {e}")
        return jsonify({"answer": "Sorry, I encountered an error processing that request."})
# ------------------ CLEAR ------------------
@app.route("/clear", methods=["POST"])
def clear():
    invoice_store.clear()
    return jsonify({"message": "Cleared"})


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)