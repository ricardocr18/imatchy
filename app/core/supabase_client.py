"""
app/core/supabase_client.py — versão em memória para testes locais
Substitui o Supabase real por um dicionário em RAM.
Quando o Lovable integrar o Supabase, basta trocar este arquivo.
"""
from __future__ import annotations
import logging

logger = logging.getLogger(__name__)

# ── Storage em memória ────────────────────────────────────────────────────────
_conversations: dict[str, dict] = {}
_messages: dict[str, list] = {}
_pdfs: dict[str, list] = {}


async def save_message(conversation_id: str, role: str, content: str) -> None:
    if conversation_id not in _messages:
        _messages[conversation_id] = []
    _messages[conversation_id].append({"role": role, "content": content})
    logger.info(f"[MEM] {conversation_id} | {role}: {content[:60]}...")


async def save_pdf(conversation_id: str, file_bytes: bytes, filename: str) -> str:
    if conversation_id not in _pdfs:
        _pdfs[conversation_id] = []
    _pdfs[conversation_id].append({"filename": filename, "size": len(file_bytes)})
    logger.info(f"[MEM] PDF salvo: {filename} ({len(file_bytes)} bytes)")
    return f"memory://{conversation_id}/{filename}"


async def get_conversation_history(conversation_id: str) -> list[dict]:
    return _messages.get(conversation_id, [])


async def upsert_conversation(
    conversation_id: str,
    phone: str,
    name: str,
    email: str,
    profile: str,
) -> None:
    _conversations[conversation_id] = {
        "id": conversation_id,
        "phone": phone,
        "name": name,
        "email": email,
        "profile": profile,
        "status": "active",
    }
    logger.info(f"[MEM] Conversa criada: {name} | {profile}")


async def close_conversation(conversation_id: str) -> None:
    if conversation_id in _conversations:
        _conversations[conversation_id]["status"] = "closed"
    logger.info(f"[MEM] Conversa encerrada: {conversation_id}")


def get_supabase():
    """Stub — não usado na versão em memória."""
    return None