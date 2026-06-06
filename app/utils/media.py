"""
app/utils/media.py — transcrição de voz (Whisper) e validação de PDF
"""
from __future__ import annotations

import httpx
from openai import AsyncOpenAI

from app.core.config import get_settings

settings = get_settings()
_openai = AsyncOpenAI(api_key=settings.openai_api_key)


async def transcribe_audio(media_url: str, twilio_sid: str, twilio_token: str) -> str:
    """
    Baixa o áudio do WhatsApp via Twilio e transcreve com Whisper.
    Retorna o texto transcrito.
    """
    async with httpx.AsyncClient() as client:
        resp = await client.get(
            media_url,
            auth=(twilio_sid, twilio_token),
            follow_redirects=True,
            timeout=30,
        )
        resp.raise_for_status()
        audio_bytes = resp.content

    transcription = await _openai.audio.transcriptions.create(
        model=settings.whisper_model,
        file=("audio.ogg", audio_bytes, "audio/ogg"),
    )
    return transcription.text


async def download_media(media_url: str, twilio_sid: str, twilio_token: str) -> tuple[bytes, str]:
    """
    Baixa qualquer mídia do Twilio e retorna (bytes, content_type).
    Usado para validar e salvar PDFs.
    """
    async with httpx.AsyncClient() as client:
        resp = await client.get(
            media_url,
            auth=(twilio_sid, twilio_token),
            follow_redirects=True,
            timeout=30,
        )
        resp.raise_for_status()
        content_type = resp.headers.get("content-type", "")
        return resp.content, content_type


def validate_pdf(file_bytes: bytes, content_type: str) -> str | None:
    """
    Valida se o arquivo é PDF e está dentro do limite de tamanho.
    Retorna mensagem de erro ou None se tudo ok.
    """
    is_pdf = "pdf" in content_type.lower() or file_bytes[:4] == b"%PDF"
    if not is_pdf:
        return "Só aceito arquivos em PDF. Pode reenviar em PDF por favor?"

    if len(file_bytes) > settings.pdf_max_bytes:
        size_mb = len(file_bytes) / 1_048_576
        return f"Este arquivo é maior que 3 MB ({size_mb:.1f} MB). Pode enviar um PDF menor?"

    return None
