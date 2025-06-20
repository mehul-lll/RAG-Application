
from datetime import datetime, timedelta
import json
from typing import List
from requests import Session

from ..helper.rag import get_embedding
from ..models import Document
from .. import models


def save_document_chunks(chunks, filename, db, user_id):
    for chunk in chunks:
        embedding = get_embedding(chunk)
        db_doc = Document(
            content=chunk,
            embedding=embedding,
            source=filename,
            owner_id=user_id
        )
        db.add(db_doc)
    db.commit()

def get_documents_by_source(db: Session, source: str, owner_id: int):
    return db.query(models.Document).filter(
        models.Document.owner_id == owner_id,
        models.Document.source == source
    ).all()

def save_chat(db, query: str, response: str, user_id: int, sources: list):
    db_chat = models.ChatHistory(
        user_query=query,
        bot_response=response,
        timestamp=datetime.now(),
        user_id=user_id,
        sources=json.dumps(sources)
    )
    db.add(db_chat)
    db.commit()


def call_mistral(query: str, document_context: str) -> str:
    # Replace this with your real Mistral API call
    return f"Mocked response for: {query}"


def save_chat_history(db, user_query: str, bot_response: str, user_id: int, sources: list):
    db_chat = models.ChatHistory(
        user_query=user_query,
        bot_response=bot_response,
        timestamp=datetime.now(),
        user_id=user_id,
        sources=json.dumps(sources)
    )
    db.add(db_chat)
    db.commit()


def get_recent_chat_history(db: Session, user_id: int) -> List[models.ChatHistory]:
    five_days_ago = datetime.utcnow() - timedelta(days=5)
    return db.query(models.ChatHistory)\
             .filter(models.ChatHistory.user_id == user_id)\
             .filter(models.ChatHistory.timestamp >= five_days_ago)\
             .order_by(models.ChatHistory.timestamp.desc())\
             .all()