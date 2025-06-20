# 🔍 RAG-Application

RAG‑Application is a **Retrieval-Augmented Generation (RAG)** demo powered by LangChain, designed to help you build a robust end-to-end pipeline that:

1. Ingests documents (e.g. PDFs, text)
2. Splits them into searchable chunks
3. Embeds chunks into a vector store (e.g. FAISS, Chroma)
4. Serves queries by retrieving relevant chunks and augmenting an LLM prompt
5. Generates accurate, context-aware responses

---

## 🧩 Architecture

- **Ingestion & Chunking**: Convert PDFs/text into semantically meaningful vector chunks.
- **Vector Store**: Use FAISS, Chroma, or similar for fast similarity retrieval.
- **Retriever**: Fetch top‑K similar chunks given a query.
- **LLM Prompting**: Craft prompts that combine user query with retrieved context.
- **Answer Generation**: Output answers with citations or metadata attached.

---

## 🚀 Quick Start

### ▶️ Clone & setup

```bash 
git clone https://github.com/mehul-lll/RAG-Application.git
cd RAG-Application
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt
fastapi dev app/main.py
streamlit run app.py
