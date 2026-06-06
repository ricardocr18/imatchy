"""
app/agents/graph.py — LangGraph com estado da conversa iMatchy

Fluxo:
  entrada → transcreve_audio (se voz) → chama_llm → verifica_encerramento
                                                  ↓ se encerrado
                                             encerra_conversa
"""
from __future__ import annotations

import re
from typing import Annotated, TypedDict

from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
from langchain_openai import ChatOpenAI
from langgraph.graph import END, StateGraph
from langgraph.graph.message import add_messages

from app.agents.prompts import AGENT_PROMPTS, DEFAULT_PROMPT
from app.core.config import get_settings


# ── Estado compartilhado ──────────────────────────────────────────────────────
class ConversationState(TypedDict):
    messages: Annotated[list, add_messages]
    nome: str
    email: str
    telefone: str
    perfil: str
    is_closed: bool
    awaiting_pdf: bool   # True após pergunta 5 ser enviada
    pdf_received: bool


# ── Helpers ───────────────────────────────────────────────────────────────────
_ENCERRAMENTO_PHRASES = [
    "Bom falar com você, até mais!",
    "não estamos conseguindo nos entender",
]

def _conversation_ended(text: str) -> bool:
    return any(phrase.lower() in text.lower() for phrase in _ENCERRAMENTO_PHRASES)

def _pergunta5_sent(text: str) -> bool:
    markers = ["enviar agora aqui um arquivo", "tese de investimento", "Pergunta 5"]
    return any(m.lower() in text.lower() for m in markers)


# ── Nó: chamar o LLM ─────────────────────────────────────────────────────────
def call_llm(state: ConversationState) -> ConversationState:
    settings = get_settings()
    llm = ChatOpenAI(
        model=settings.openai_model,
        api_key=settings.openai_api_key,
        temperature=0.4,
        max_tokens=400,
    )

    perfil = state.get("perfil", "")
    system_prompt = AGENT_PROMPTS.get(perfil, DEFAULT_PROMPT)
    system_prompt = system_prompt.replace("{nome}", state.get("nome", ""))

    messages = [SystemMessage(content=system_prompt)] + list(state["messages"])
    response = llm.invoke(messages)

    new_awaiting_pdf = state.get("awaiting_pdf", False)
    if not new_awaiting_pdf and _pergunta5_sent(response.content):
        new_awaiting_pdf = True

    return {
        "messages": [AIMessage(content=response.content)],
        "is_closed": _conversation_ended(response.content),
        "awaiting_pdf": new_awaiting_pdf,
    }


# ── Nó: encerrar conversa ────────────────────────────────────────────────────
def close_conversation_node(state: ConversationState) -> ConversationState:
    # Apenas sinaliza — a API faz a limpeza no Supabase
    return {"is_closed": True}


# ── Roteador ─────────────────────────────────────────────────────────────────
def should_close(state: ConversationState) -> str:
    return "close" if state.get("is_closed") else END


# ── Construção do grafo ───────────────────────────────────────────────────────
def build_graph() -> StateGraph:
    graph = StateGraph(ConversationState)
    graph.add_node("call_llm", call_llm)
    graph.add_node("close_conversation", close_conversation_node)

    graph.set_entry_point("call_llm")
    graph.add_conditional_edges("call_llm", should_close, {"close": "close_conversation", END: END})
    graph.add_edge("close_conversation", END)

    return graph.compile()


# Instância global (compilada uma única vez)
imatchy_graph = build_graph()
