"""
app/api/webhook.py — endpoint POST /webhook/whatsapp (Twilio → iMatchy)
"""
from __future__ import annotations
import hashlib
import logging

from fastapi import APIRouter, Form, Request, Response
from twilio.rest import Client as TwilioClient

from app.agents.graph import ConversationState, imatchy_graph
from app.core.config import get_settings
from app.core.supabase_client import (
    _conversations,
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
    return hashlib.sha256(phone.encode()).hexdigest()[:24]


def _parse_initial_message(body: str) -> dict:
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
        conv = _conversations.get(conversation_id, {})
        if conv.get("status") == "closed":
            return Response(content="", media_type="text/plain")
        user_meta["nome"] = conv.get("name", "")
        user_meta["email"] = conv.get("email", "")
        user_meta["perfil"] = conv.get("profile", "")

    # ── 2. Verifica se agente já pediu PDF ───────────────────────────────────
    awaiting_pdf = any(
        "enviar agora aqui um arquivo" in m.get("content", "").lower()
        for m in history
        if m.get("role") == "assistant"
    )

    # ── 3. Processa mídia ────────────────────────────────────────────────────
    user_text = Body.strip()

    if NumMedia > 0 and MediaUrl0:
        file_bytes, content_type = await download_media(
            MediaUrl0,
            settings.twilio_account_sid,
            settings.twilio_auth_token,
        )

        if not awaiting_pdf:
            _send_whatsapp(phone, "Obrigado! Por enquanto, vamos continuar nossa conversa 😊")
            return Response(content="", media_type="text/plain")

        if "audio" in content_type.lower() or "ogg" in content_type.lower():
            user_text = await transcribe_audio(
                MediaUrl0, settings.twilio_account_sid, settings.twilio_auth_token
            )
        else:
            error_msg = validate_pdf(file_bytes, content_type)
            if error_msg:
                _send_whatsapp(phone, error_msg)
                return Response(content="", media_type="text/plain")
            filename = f"doc_{conversation_id[:8]}.pdf"
            await save_pdf(conversation_id, file_bytes, filename)
            user_text = f"[PDF enviado: {filename}]"

    elif not user_text:
        return Response(content="", media_type="text/plain")

    # ── 4. Salva mensagem do usuário ─────────────────────────────────────────
    await save_message(conversation_id, "user", user_text)

    # ── 5. Monta estado e roda o grafo ───────────────────────────────────────
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

    # ── 6. Extrai e envia resposta ────────────────────────────────────────────
    ai_messages = [m for m in result["messages"] if isinstance(m, AIMessage)]
    if not ai_messages:
        return Response(content="", media_type="text/plain")

    reply_text = ai_messages[-1].content
    await save_message(conversation_id, "assistant", reply_text)
    _send_whatsapp(phone, reply_text)

    # ── 7. Encerra se necessário ──────────────────────────────────────────────
    if result.get("is_closed"):
        await close_conversation(conversation_id)
        logger.info(f"Conversa {conversation_id} encerrada.")

    return Response(content="", media_type="text/plain")