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

# ── Triggers que indicam que o agente já abriu a janela de PDF (PT + EN + ES) ─
_PDF_TRIGGERS = [
    # PT
    "enviar agora aqui um arquivo",
    "pode enviar um arquivo do tipo pdf",
    "pode enviar aqui agora um arquivo",
    "pode enviar aqui um arquivo",
    "enviar aqui um arquivo do tipo pdf",
    "enviar um arquivo do tipo pdf",
    # EN
    "you can send a pdf file",
    "send a pdf file here",
    "if you'd like, you can send",
    "maximum file size 3mb",
    "send a pdf",
    # ES
    "puedes enviar un archivo pdf",
    "pueden enviar ahora un archivo pdf",
    "enviar un archivo pdf",
    "tamaño máximo del archivo",
]

# ── Mensagens de encerramento por idioma ──────────────────────────────────────
def _build_encerramento(nome: str, lang: str) -> str:
    msgs = {
        "PT": f"Perfeito, {nome}! Seu perfil está sendo preparado para a Conecta Cientista. Nossa IA irá analisar suas competências, interesses e oportunidades para gerar conexões mais estratégicas dentro do ecossistema de inovação, ciência, startups e negócios. Bom falar com você, até mais! Obrigado!",
        "EN": f"Perfect, {nome}! Your profile is being prepared for Conecta Cientista. Our AI will analyze your skills, interests, and opportunities to generate more strategic connections within the innovation, science, startups, and business ecosystem. Great talking to you, see you soon! Thank you!",
        "ES": f"¡Perfecto, {nome}! Tu perfil está siendo preparado para Conecta Cientista. Nuestra IA analizará tus competencias, intereses y oportunidades para generar conexiones más estratégicas dentro del ecosistema de innovación, ciencia, startups y negocios. ¡Un placer hablar contigo, hasta pronto! ¡Gracias!",
    }
    return msgs.get(lang.upper(), msgs["PT"])

# ── Mensagens de erro de arquivo por idioma ───────────────────────────────────
def _msg_not_pdf(lang: str) -> str:
    msgs = {
        "PT": "Só aceito arquivos em PDF. Pode reenviar em PDF por favor?",
        "EN": "I only accept PDF files. Could you resend it as a PDF?",
        "ES": "Solo acepto archivos en PDF. ¿Puedes reenviarlo en PDF?",
    }
    return msgs.get(lang.upper(), msgs["PT"])

def _msg_pdf_too_large(lang: str) -> str:
    msgs = {
        "PT": "Este arquivo é maior que 3 MB. Pode enviar um PDF menor?",
        "EN": "This file is larger than 3 MB. Could you send a smaller PDF?",
        "ES": "Este archivo es mayor a 3 MB. ¿Puedes enviar un PDF más pequeño?",
    }
    return msgs.get(lang.upper(), msgs["PT"])

def _msg_continue(lang: str) -> str:
    msgs = {
        "PT": "Obrigado! Por enquanto, vamos continuar nossa conversa 😊",
        "EN": "Thank you! For now, let's continue our conversation 😊",
        "ES": "¡Gracias! Por ahora, continuemos con nuestra conversación 😊",
    }
    return msgs.get(lang.upper(), msgs["PT"])


def _make_conversation_id(phone: str) -> str:
    return hashlib.sha256(phone.encode()).hexdigest()[:24]


def _parse_initial_message(body: str) -> dict:
    data = {"nome": "", "email": "", "telefone": "", "perfil": "", "language": "PT"}
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
        elif line.lower().startswith("language:") or line.lower().startswith("idioma:"):
            data["language"] = line.split(":", 1)[1].strip().upper()
    return data


def _send_whatsapp(to: str, body: str) -> None:
    twilio_client.messages.create(
        from_=f"whatsapp:{settings.twilio_whatsapp_number}",
        to=f"whatsapp:{to}",
        body=body,
    )


def _is_awaiting_pdf(history: list[dict]) -> bool:
    return any(
        any(trigger in m.get("content", "").lower() for trigger in _PDF_TRIGGERS)
        for m in history
        if m.get("role") == "assistant"
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
    user_meta = {"nome": "", "email": "", "telefone": phone, "perfil": "", "language": "PT"}

    is_form_start = Body.strip().lower().startswith("oi imatchy, sou ")

    if is_first_message or is_form_start:
        if is_form_start and not is_first_message:
            from app.core.supabase_client import _messages, _invalid_attempts
            _messages[conversation_id] = []
            _invalid_attempts[conversation_id] = 0
            history = []
            logger.info(f"[TESTE] Histórico resetado para {conversation_id}")
        user_meta = _parse_initial_message(Body)
        user_meta["telefone"] = user_meta.get("telefone") or phone
        await upsert_conversation(
            conversation_id=conversation_id,
            phone=phone,
            name=user_meta["nome"],
            email=user_meta["email"],
            profile=user_meta["perfil"],
            language=user_meta.get("language", "PT"),
        )
    else:
        conv = _conversations.get(conversation_id, {})
        if conv.get("status") == "closed":
            return Response(content="", media_type="text/plain")
        user_meta["nome"] = conv.get("name", "")
        user_meta["email"] = conv.get("email", "")
        user_meta["perfil"] = conv.get("profile", "")
        user_meta["language"] = conv.get("language", "PT")

    lang = user_meta.get("language", "PT").upper()

    # ── 2. Verifica se está aguardando PDF ────────────────────────────────────
    awaiting_pdf = _is_awaiting_pdf(history)
    user_text = Body.strip()

    # ── 3. Processa mídia ─────────────────────────────────────────────────────
    if NumMedia > 0 and MediaUrl0:
        file_bytes, content_type = await download_media(
            MediaUrl0,
            settings.twilio_account_sid,
            settings.twilio_auth_token,
        )

        # Áudio → transcreve como texto
        if "audio" in content_type.lower() or "ogg" in content_type.lower():
            user_text = await transcribe_audio(
                MediaUrl0, settings.twilio_account_sid, settings.twilio_auth_token
            )

        # Arquivo antes de ser solicitado → avisa no idioma certo
        elif not awaiting_pdf:
            _send_whatsapp(phone, _msg_continue(lang))
            return Response(content="", media_type="text/plain")

        # Arquivo na hora certa → valida
        else:
            is_pdf = "pdf" in content_type.lower() or file_bytes[:4] == b"%PDF"
            if not is_pdf:
                _send_whatsapp(phone, _msg_not_pdf(lang))
                return Response(content="", media_type="text/plain")

            if len(file_bytes) > settings.pdf_max_bytes:
                _send_whatsapp(phone, _msg_pdf_too_large(lang))
                return Response(content="", media_type="text/plain")

            # PDF válido → salva e envia encerramento direto no idioma certo
            filename = f"doc_{conversation_id[:8]}.pdf"
            await save_pdf(conversation_id, file_bytes, filename)
            logger.info(f"PDF salvo: {filename} [{lang}]")

            encerramento = _build_encerramento(user_meta["nome"], lang)
            await save_message(conversation_id, "user", f"[PDF enviado: {filename}]")
            await save_message(conversation_id, "assistant", encerramento)
            _send_whatsapp(phone, encerramento)
            await close_conversation(conversation_id)
            return Response(content="", media_type="text/plain")

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
        "language": lang,
        "conversation_id": conversation_id,
        "is_closed": False,
        "awaiting_pdf": awaiting_pdf,
        "pdf_received": False,
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
        logger.info(f"Conversa {conversation_id} encerrada [{lang}].")

    return Response(content="", media_type="text/plain")