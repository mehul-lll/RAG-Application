from typing import Optional, List
from pydantic import BaseModel, EmailStr
from datetime import datetime

class UserBase(BaseModel):
    username: str
    email: EmailStr

class UserCreate(UserBase):
    password: str

class User(UserBase):
    id: int
    is_active: bool

    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None

class Document(BaseModel):
    id: int
    source: str
    content: str

    class Config:
        from_attributes = True

class Query(BaseModel):
    text: str
    type: Optional[str] = None  # Optional parameter to force a specific query type

class Response(BaseModel):
    answer: str
    sources: List[str]

class ChatHistory(BaseModel):
    id: int
    user_query: str
    bot_response: str
    timestamp: datetime
    sources: str

    class Config:
        from_attributes = True