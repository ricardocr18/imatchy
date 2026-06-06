"""
app/api/webhook.py — endpoint POST /webhook/whatsapp (Twilio → iMatchy)

Fluxo de entrada:
  1. Twilio envia POST com a mensagem do usuário
  2. Identificamos o remetente e carregamos o histórico do Supabase
  3. Se for áudio → Whisper transcreve
  4. Se for arquivo e agente ainda não pediu PDF → mensagem de aviso
  5. Se for PDF na hora certa → valida, salva no Supabase Storage
  6. LangGraph processa e gera resposta
  7. Twilio envia a resposta de volta via WhatsApp
  8. Se encerrado → fecha conversa no Supabase
"""
from __future__ import annotations

import hashlib
import logging

from fastapi import APIRouter, Form, Request, Response
from twilio.rest import Client as TwilioClient
from twilio.twiml.messaging_response import MessagingResponse

from app.agents.graph import ConversationState, imatchy_graph
from app.core.config import get_settings
from app.core.supabase_client import (
    close_conversation,
    get_conversation_history,
    save_message,
    save_pdf,
    upsert_conversation,
)
from app.utils.media import download_media, transcribe_audio, validate_pdf
from langchain_core.messages import HumanMessage, AIMessage

logger = logging.getLogger(__name__)
router = APIRouter()
settings = get_settings()
twilio_client = TwilioClient(settings.twilio_account_sid, settings.twilio_auth_token)


def _make_conversation_id(phone: str) -> str:
    """ID estável baseado no telefone — mesmo usuário sempre reutiliza a conversa ativa."""
    return hashlib.sha256(phone.encode()).hexdigest()[:24]


def _parse_initial_message(body: str) -> dict:
    """
    Extrai nome, email, telefone e perfil da primeira mensagem enviada pelo
    deep link do frontend, ex.:
      Oi iMatchy, sou Ricardo Ribeiro.
      E-mail: ricardocribeiro@gmail.com
      Telefone: +5561993981536
      Perfil: Investidor
    """
    data = {"nome": "", "email": "", "telefone": "", "perfil": ""}
    for line in body.splitlines():
        line = line.strip()
        if line.lower().startswith("oi imatchy, sou "):
            data["nome"] = line[len("oi imatchy, sou "):].rstrip(".")
        elif line.lower().startswith("e-mail:"):
            data["email"] = line.split(":", 1)[1].strip()
        elif line.lower().startswith("telefone:"):
            data["telefone"] = line.split(":", 1)[1].strip()
        elif line.lower().startswith("perfil:"):
            data["perfil"] = line.split(":", 1)[1].strip()
    return data


def _send_whatsapp(to: str, body: str) -> None:
    twilio_client.messages.create(
        from_=f"whatsapp:{settings.twilio_whatsapp_number}",
        to=f"whatsapp:{to}",
        body=body,
    )


@router.post("/webhook/whatsapp")
async def whatsapp_webhook(
    request: Request,
    From: str = Form(...),
    Body: str = Form(default=""),
    NumMedia: int = Form(default=0),
    MediaUrl0: str = Form(default=""),
    MediaContentType0: str = Form(default=""),
):
    phone = From.replace("whatsapp:", "")
    conversation_id = _make_conversation_id(phone)

    # ── 1. Carrega ou cria conversa ──────────────────────────────────────────
    history = await get_conversation_history(conversation_id)

    is_first_message = len(history) == 0
    user_meta = {"nome": "", "email": "", "telefone": phone, "perfil": ""}

    if is_first_message:
        user_meta = _parse_initial_message(Body)
        user_meta["telefone"] = user_meta.get("telefone") or phone
        await upsert_conversation(
            conversation_id=conversation_id,
            phone=phone,
            name=user_meta["nome"],
            email=user_meta["email"],
            profile=user_meta["perfil"],
        )
    else:
        # Recupera metadados da conversa existente
        from app.core.supabase_client import get_supabase
        db = get_supabase()
        row = db.table("conversations").select("name,email,profile,status").eq("id", conversation_id).single().execute()
        if row.data:
            if row.data.get("status") == "closed":
                # Conversa já encerrada, não responde
                return Response(content="", media_type="text/plain")
            user_meta["nome"] = row.data.get("name", "")
            user_meta["email"] = row.data.get("email", "")
            user_meta["perfil"] = row.data.get("profile", "")

    # ── 2. Processa mídia ────────────────────────────────────────────────────
    user_text = Body.strip()

    # Verifica se agente já pediu PDF (histórico tem pergunta 5)
    awaiting_pdf = any(
        "enviar agora aqui um arquivo" in m.get("content", "").lower()
        for m in history
        if m.get("role") == "assistant"
    )

    if NumMedia > 0 and MediaUrl0:
        file_bytes, content_type = await download_media(
            MediaUrl0,
            settings.twilio_account_sid,
            settings.twilio_auth_token,
        )

        # Usuário tenta enviar arquivo antes de ser pedido
        if not awaiting_pdf:
            _send_whatsapp(phone, "Obrigado! Por enquanto, vamos continuar nossa conversa 😊")
            return Response(content="", media_type="text/plain")

        # Áudio → transcreve
        if "audio" in content_type.lower() or "ogg" in content_type.lower():
            user_text = await transcribe_audio(
                MediaUrl0, settings.twilio_account_sid, settings.twilio_auth_token
            )

        # Documento → valida PDF
        elif "document" in content_type.lower() or "pdf" in content_type.lower() or "application" in content_type.lower():
            error_msg = validate_pdf(file_bytes, content_type)
            if error_msg:
                _send_whatsapp(phone, error_msg)
                return Response(content="", media_type="text/plain")

            # PDF válido → salva
            filename = f"doc_{conversation_id[:8]}.pdf"
            pdf_url = await save_pdf(conversation_id, file_bytes, filename)
            user_text = f"[PDF enviado: {filename}]"
            logger.info(f"PDF salvo para conversa {conversation_id}: {pdf_url}")

    elif not user_text:
        return Response(content="", media_type="text/plain")

    # ── 3. Salva mensagem do usuário ──────────────────────────────────────────
    await save_message(conversation_id, "user", user_text)

    # ── 4. Monta estado e roda o grafo ───────────────────────────────────────
    lc_history = []
    for m in history:
        if m["role"] == "user":
            lc_history.append(HumanMessage(content=m["content"]))
        elif m["role"] == "assistant":
            lc_history.append(AIMessage(content=m["content"]))

    state: ConversationState = {
        "messages": lc_history + [HumanMessage(content=user_text)],
        "nome": user_meta["nome"],
        "email": user_meta["email"],
        "telefone": user_meta["telefone"],
        "perfil": user_meta["perfil"],
        "is_closed": False,
        "awaiting_pdf": awaiting_pdf,
        "pdf_received": bool(NumMedia > 0 and awaiting_pdf),
    }

    result = imatchy_graph.invoke(state)

    # ── 5. Extrai e envia resposta ────────────────────────────────────────────
    ai_messages = [m for m in result["messages"] if isinstance(m, AIMessage)]
    if not ai_messages:
        return Response(content="", media_type="text/plain")

    reply_text = ai_messages[-1].content
    await save_message(conversation_id, "assistant", reply_text)
    _send_whatsapp(phone, reply_text)

    # ── 6. Encerra se necessário ──────────────────────────────────────────────
    if result.get("is_closed"):
        await close_conversation(conversation_id)
        logger.info(f"Conversa {conversation_id} encerrada.")

    return Response(content="", media_type="text/plain")
