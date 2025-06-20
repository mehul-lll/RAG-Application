
from typing import List
from fastapi import HTTPException
from requests import Session

from ..helper.rag import chunk_text, read_file
from .. import schemas
from .. import models
from ..repository.rag import save_document_chunks, get_documents_by_source, call_mistral, save_chat_history, get_recent_chat_history
from ..helper.rag import get_relevant_documents

def process_uploaded_file(file, db, current_user):
    content = read_file(file)
    chunks = chunk_text(content)
    save_document_chunks(chunks, file.filename, db, current_user.id)
    return {"message": f"Uploaded and processed {len(chunks)} chunks from {file.filename}"}


def delete_document_by_source(source: str, db: Session, current_user: models.User):
    documents = get_documents_by_source(db, source, current_user.id)
    
    if not documents:
        raise HTTPException(status_code=404, detail="Document not found")
    
    for doc in documents:
        db.delete(doc)
    
    db.commit()
    return {"message": f"Deleted document '{source}' with {len(documents)} chunks"}

def get_user_chat_history(db: Session, user: models.User) -> List[models.ChatHistory]:
    return get_recent_chat_history(db, user.id)



def handle_query(query: schemas.Query, db: Session, current_user: models.User):
    relevant_docs = get_relevant_documents(
        db, query.text, current_user.id, similarity_threshold=0.5
    )

    doc_context = "\n".join([doc.content for doc in relevant_docs]) if relevant_docs else ""

    answer = call_mistral(query.text, doc_context)

    save_chat_history(
        db=db,
        user_query=query.text,
        bot_response=answer,
        user_id=current_user.id,
        sources=[doc.source for doc in relevant_docs] if relevant_docs else []
    )

    return schemas.Response(
        answer=answer,
        sources=[doc.source for doc in relevant_docs] if relevant_docs else []
    )