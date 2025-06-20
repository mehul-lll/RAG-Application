import os
from typing import List
from fastapi import HTTPException, UploadFile
import fitz
import pandas as pd
from requests import Session
import requests
from sentence_transformers import SentenceTransformer
import numpy as np

from dotenv import load_dotenv
from .. import models

load_dotenv()


embedding_model = SentenceTransformer('all-MiniLM-L6-v2')

def get_embedding(text: str) -> list[float]:
    return embedding_model.encode(text).tolist()


def cosine_similarity(a: list[float], b: list[float]) -> float:
    return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))


def read_file(file: UploadFile) -> str:
    content = ""
    if file.filename.endswith(".pdf"):
        with fitz.open(stream=file.file.read(), filetype="pdf") as doc:
            content = "\n".join([page.get_text() for page in doc])
    elif file.filename.endswith(".csv"):
        df = pd.read_csv(file.file)
        content = df.to_string()
    elif file.filename.endswith(".txt"):
        content = file.file.read().decode("utf-8")
    else:
        raise HTTPException(status_code=400, detail="Unsupported file type")
    return content

def chunk_text(text: str, max_chunk_size: int = 500) -> List[str]:
    paragraphs = text.split("\n")
    chunks = []
    current_chunk = ""

    for para in paragraphs:
        if len(current_chunk) + len(para) < max_chunk_size:
            current_chunk += para + "\n"
        else:
            chunks.append(current_chunk.strip())
            current_chunk = para + "\n"
    if current_chunk:
        chunks.append(current_chunk.strip())
    return chunks


def get_relevant_chat_history(
    query: str,
    db: Session,
    user_id: int,
    top_k: int = 3,
    similarity_threshold: float = 0.4
):
    query_embedding = get_embedding(query)
    chats = db.query(models.ChatHistory).filter(models.ChatHistory.user_id == user_id).all()
    
    if not chats:
        return []
    
    scored_chats = []
    for chat in chats:
        chat_embedding = get_embedding(chat.user_query)
        score = cosine_similarity(query_embedding, chat_embedding)
        if score >= similarity_threshold:
            scored_chats.append((chat, score))
    
    scored_chats.sort(key=lambda x: x[1], reverse=True)
    return [chat for chat, score in scored_chats[:top_k]]


def get_relevant_documents(
    query: str, 
    db: Session, 
    user_id: int,
    top_k: int = 3, 
    similarity_threshold: float = 0.5
):
    query_embedding = get_embedding(query)
    documents = db.query(models.Document).filter(models.Document.owner_id == user_id).all()
    
    if not documents:
        return []
    
    scored_docs = []
    for doc in documents:
        doc_embedding = doc.embedding
        if isinstance(doc_embedding, np.ndarray):
            score = cosine_similarity(query_embedding, doc_embedding)
            if score >= similarity_threshold:
                scored_docs.append((doc, score))
    
    scored_docs.sort(key=lambda x: x[1], reverse=True)
    return [doc for doc, score in scored_docs[:top_k]]



def call_advanced_mistral_api(query: str, document_context: str = "") -> str:
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {os.getenv('MISTRAL_API_KEY')}"
    }

    system_prompt = """You are a helpful assistant with two strict capabilities:

1. Document-based Q&A: You answer questions based ONLY on the user's uploaded documents.
2. General conversation: You can engage in simple, casual exchanges like greetings.

RULES:
- If the question is asking for factual information and document context is provided, ONLY answer using that document context.
- If the answer is NOT in the document context, respond with EXACTLY: "Not found in Database".
- For greetings or casual conversation (e.g., "hello", "how are you"), respond conversationally.
- DO NOT answer factual or specific questions unless the answer is found in the provided document context.
- DO NOT use prior conversation history.
- DO NOT hallucinate or make up any information.
"""

    user_input = f"Question: {query}\n\n"

    if document_context:
        user_input += f"Document Context:\n{document_context}\n"

    data = {
        "model": "mistral-tiny",
        "messages": [
            {
                "role": "system",
                "content": system_prompt
            },
            {
                "role": "user",
                "content": user_input
            }
        ],
        "temperature": 0.3
    }

    response = requests.post(os.getenv('MISTRAL_API_URL'), headers=headers, json=data)
    if response.status_code != 200:
        raise HTTPException(status_code=response.status_code, detail="Mistral API error")
    
    return response.json()["choices"][0]["message"]["content"]

