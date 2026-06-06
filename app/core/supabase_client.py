"""
app/core/supabase_client.py — cliente Supabase para salvar conversas e PDFs
"""
from supabase import create_client, Client
from app.core.config import get_settings
from functools import lru_cache


@lru_cache
def get_supabase() -> Client:
    s = get_settings()
    return create_client(s.supabase_url, s.supabase_service_key)


async def save_message(conversation_id: str, role: str, content: str) -> None:
    """Persiste uma mensagem na tabela messages do Supabase."""
    db = get_supabase()
    db.table("messages").insert(
        {
            "conversation_id": conversation_id,
            "role": role,
            "content": content,
        }
    ).execute()


async def save_pdf(conversation_id: str, file_bytes: bytes, filename: str) -> str:
    """
    Faz upload do PDF no Supabase Storage e retorna a URL pública.
    O bucket 'imatchy-pdfs' precisa existir no seu projeto Supabase.
    """
    db = get_supabase()
    path = f"{conversation_id}/{filename}"
    db.storage.from_("imatchy-pdfs").upload(
        path=path,
        file=file_bytes,
        file_options={"content-type": "application/pdf"},
    )
    public_url = db.storage.from_("imatchy-pdfs").get_public_url(path)
    db.table("pdf_files").insert(
        {
            "conversation_id": conversation_id,
            "filename": filename,
            "storage_url": public_url,
        }
    ).execute()
    return public_url


async def get_conversation_history(conversation_id: str) -> list[dict]:
    """Recupera todo o histórico de uma conversa."""
    db = get_supabase()
    result = (
        db.table("messages")
        .select("role, content")
        .eq("conversation_id", conversation_id)
        .order("created_at")
        .execute()
    )
    return result.data or []


async def upsert_conversation(
    conversation_id: str,
    phone: str,
    name: str,
    email: str,
    profile: str,
) -> None:
    """Cria ou atualiza o registro da conversa."""
    db = get_supabase()
    db.table("conversations").upsert(
        {
            "id": conversation_id,
            "phone": phone,
            "name": name,
            "email": email,
            "profile": profile,
            "status": "active",
        }
    ).execute()


async def close_conversation(conversation_id: str) -> None:
    """Marca a conversa como encerrada."""
    db = get_supabase()
    db.table("conversations").update({"status": "closed"}).eq(
        "id", conversation_id
    ).execute()
