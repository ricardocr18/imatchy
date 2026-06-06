"""
app/main.py — ponto de entrada da aplicação iMatchy
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.webhook import router as webhook_router

app = FastAPI(
    title="iMatchy Backend",
    description="Chatbot WhatsApp para a plataforma Conecta Cientista",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["POST", "GET"],
    allow_headers=["*"],
)

app.include_router(webhook_router)


@app.get("/health")
async def health():
    return {"status": "ok", "service": "iMatchy"}
