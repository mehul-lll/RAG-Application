import json
from fastapi import APIRouter, Depends
from typing import List
from sqlalchemy.orm import Session
from datetime import datetime
from fastapi import UploadFile, File

from ..helper.rag import call_advanced_mistral_api
from ..database import get_db
from .. import schemas, models
from ..helper import auth
from ..service.rag import (
    get_relevant_documents,
    delete_document_by_source,
    process_uploaded_file,
    get_user_chat_history
)


router = APIRouter() 


@router.post("/query", response_model=schemas.Response)
def query(
    query: schemas.Query, 
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_active_user)
):
    relevant_docs = get_relevant_documents(query.text, db, current_user.id, similarity_threshold=0.5)
    doc_context = "\n".join([doc.content for doc in relevant_docs]) if relevant_docs else ""
    
    answer = call_advanced_mistral_api(
        query=query.text,
        document_context=doc_context,
    )
    db_chat = models.ChatHistory(
        user_query=query.text,
        bot_response=answer,
        timestamp=datetime.now(),
        user_id=current_user.id,
        sources=json.dumps([doc.source for doc in relevant_docs]) if relevant_docs else "[]"
    )
    db.add(db_chat)
    db.commit()

    return {
        "answer": answer,
        "sources": [doc.source for doc in relevant_docs] if relevant_docs else []
    }


@router.get("/chat-history", response_model=List[schemas.ChatHistory])
def get_chat_history(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_active_user)
):
    return get_user_chat_history(db, current_user)

@router.post("/upload-file")
def upload_file(
    file: UploadFile = File(...), 
    db: Session = Depends(get_db),
    current_user: auth.models.User = Depends(auth.get_current_active_user)
):
    return process_uploaded_file(file, db, current_user)

@router.get("/documents", response_model=List[schemas.Document])
def get_user_documents(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_active_user)
):
    return db.query(models.Document).filter(models.Document.owner_id == current_user.id).all()

@router.delete("/documents/{source}")
def delete_document(
    source: str,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_active_user)
):
    return delete_document_by_source(source, db, current_user)
