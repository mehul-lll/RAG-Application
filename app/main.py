from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .routes import rag, auth
from .database import init_db

app = FastAPI()
init_db()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(rag.router)
app.include_router(auth.router)


# # https://ai-agent01.app.n8n.cloud/webhook-test/3ba0daa6-4543-4112-84cf-91f59d2bddb5

# import streamlit as st
# import requests

# st.title("Trigger AI Analyst Agent")

# if st.button("Run Workflow"):
#     webhook_url = "https://ai-agent01.app.n8n.cloud/webhook/3ba0daa6-4543-4112-84cf-91f59d2bddb5"
    
#     try:
#         response = requests.post(webhook_url)
#         if response.status_code == 200:
#             st.success("Workflow triggered successfully!")
#         else:
#             st.error(f"Failed with status code: {response.status_code}")
#     except Exception as e:
#         st.error(f"Error: {e}")