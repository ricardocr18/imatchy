"""
tests/test_webhook.py — testes básicos sem dependências externas
"""
import pytest
from app.api.webhook import _parse_initial_message, _make_conversation_id
from app.utils.media import validate_pdf


def test_parse_initial_message():
    body = (
        "Oi iMatchy, sou Ricardo Ribeiro.\n"
        "E-mail: ricardocribeiro@gmail.com\n"
        "Telefone: +5561993981536\n"
        "Perfil: Investidor"
    )
    result = _parse_initial_message(body)
    assert result["nome"] == "Ricardo Ribeiro"
    assert result["email"] == "ricardocribeiro@gmail.com"
    assert result["telefone"] == "+5561993981536"
    assert result["perfil"] == "Investidor"


def test_conversation_id_is_stable():
    phone = "+5511999999999"
    assert _make_conversation_id(phone) == _make_conversation_id(phone)
    assert len(_make_conversation_id(phone)) == 24


def test_validate_pdf_wrong_type():
    fake_docx = b"PK\x03\x04"  # ZIP header (docx)
    err = validate_pdf(fake_docx, "application/vnd.openxmlformats-officedocument")
    assert err is not None
    assert "PDF" in err


def test_validate_pdf_too_large():
    # Cria bytes com cabeçalho PDF mas acima de 3 MB
    big_pdf = b"%PDF" + b"0" * (3_145_729)
    err = validate_pdf(big_pdf, "application/pdf")
    assert err is not None
    assert "3 MB" in err


def test_validate_pdf_valid():
    minimal_pdf = b"%PDF-1.4 valid content"
    err = validate_pdf(minimal_pdf, "application/pdf")
    assert err is None
