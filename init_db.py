from app.database import engine
from app.models import Base

def init_db():
    Base.metadata.create_all(bind=engine)
    print("Database tables created successfully!")

if __name__ == "__main__":
    init_db()




#     @app.post("/query", response_model=schemas.Response)
# def query(
#     query: schemas.Query, 
#     db: Session = Depends(get_db),
#     current_user: models.User = Depends(auth.get_current_active_user)
# ):
#     # First check if this is a continuation of conversation
#     chat_history = db.query(models.ChatHistory)\
#         .filter(models.ChatHistory.user_id == current_user.id)\
#         .order_by(models.ChatHistory.timestamp.desc())\
#         .limit(10)\
#         .all()[::-1]  # Get last 5 exchanges in order

#     # Check for personal questions
#     personal_keywords = ["my name", "I am", "I'm called", "call me", "what is my name"]
#     if any(keyword in query.text.lower() for keyword in personal_keywords):
#         # Try to answer from chat history only
#         answer_from_history = answer_from_chat_history(query.text, chat_history)
#         if answer_from_history:
#             return {
#                 "answer": answer_from_history,
#                 "sources": ["chat history"]
#             }

#     # Get relevant documents
#     relevant_docs = get_relevant_documents(query.text, db, current_user.id, similarity_threshold=0.5)
#     context = "\n".join([doc.content for doc in relevant_docs]) if relevant_docs else ""

#     # Prepare messages for Mistral
#     messages = []
    
#     # System message with strict instructions
#     system_message = {
#         "role": "system",
#         "content": (
#             "You are a strict assistant that must follow these rules:\n"
#             "1. For factual questions, ONLY use the provided document context\n"
#             "2. For conversational context, use the chat history\n"
#             "3. If the answer isn't in documents or chat history, reply: 'can't find in database'\n"
#             "4. Never use your own knowledge or make up answers\n"
#             "5. For personal questions, ONLY use chat history"
#         )
#     }
#     messages.append(system_message)
    
#     # Add document context if available
#     if context:
#         messages.append({
#             "role": "system",
#             "content": f"DOCUMENT CONTEXT (use for factual answers only):\n{context}"
#         })
    
#     # Add chat history
#     for chat in chat_history:
#         messages.append({"role": "user", "content": chat.user_query})
#         messages.append({"role": "assistant", "content": chat.bot_response})
    
#     # Add current query
#     messages.append({"role": "user", "content": query.text})
    
#     # Call Mistral API
#     headers = {
#         "Content-Type": "application/json",
#         "Authorization": f"Bearer {MISTRAL_API_KEY}"
#     }
    
#     data = {
#         "model": "mistral-tiny",
#         "messages": messages,
#         "temperature": 0.1
#     }
    
#     response = requests.post(MISTRAL_API_URL, headers=headers, json=data)
#     if response.status_code != 200:
#         raise HTTPException(status_code=response.status_code, detail="Mistral API error")
    
#     answer = response.json()["choices"][0]["message"]["content"]
    
#     # Ensure we don't return made-up answers
#     if not relevant_docs and not is_conversational_response(query.text):
#         if "can't find in database" not in answer.lower():
#             answer = "can't find in database"
    
#     # Save to chat history
#     db_chat = models.ChatHistory(
#         user_query=query.text,
#         bot_response=answer,
#         timestamp=datetime.now(),
#         user_id=current_user.id,
#         sources=str([doc.source for doc in relevant_docs]) if relevant_docs else "chat history"
#     )
#     db.add(db_chat)
#     db.commit()
    
#     return {
#         "answer": answer,
#         "sources": [doc.source for doc in relevant_docs] if relevant_docs else ["chat history"]
#     }

# def answer_from_chat_history(query: str, chat_history: list) -> str:
#     """Try to answer purely from chat history for personal questions"""
#     name_keywords = ["my name is", "i am called", "call me"]
#     for i in range(len(chat_history)-1):
#         user_msg = chat_history[i].user_query.lower()
#         bot_msg = chat_history[i].bot_response
        
#         # Check if user previously shared their name
#         if any(keyword in user_msg for keyword in name_keywords):
#             if "what is my name" in query.lower():
#                 for keyword in name_keywords:
#                     if keyword in user_msg:
#                         name = user_msg.split(keyword)[-1].strip()
#                         return f"Your name is {name.capitalize()}"
    
#     return None

# def is_conversational_response(query: str) -> bool:
#     """Check if the query is conversational (not requiring factual answers)"""
#     conversational_keywords = [
#         "hello", "hi", "hey", 
#         "how are you", "what's up",
#         "thank you", "thanks",
#         "good morning", "good afternoon"
#     ]
#     return any(keyword in query.lower() for keyword in conversational_keywords)