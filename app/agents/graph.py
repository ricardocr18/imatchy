"""
app/agents/graph.py — LangGraph com estado da conversa iMatchy
Contagem de tentativas inválidas persistida no supabase_client (memória).
"""
from __future__ import annotations
import logging
from typing import Annotated, TypedDict

from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
from langchain_openai import ChatOpenAI
from langgraph.graph import END, StateGraph
from langgraph.graph.message import add_messages

from app.agents.personas import AGENT_PROMPTS, DEFAULT_PROMPT
from app.core.config import get_settings
import app.core.supabase_client as store

logger = logging.getLogger(__name__)

MSG_NAO_ENTENDEMOS = (
    "Acredito que não estamos conseguindo nos entender. "
    "Depois a equipe da Conecta Cientista vai entrar em contato "
    "com você para entender melhor seus interesses."
)


# ── Estado ────────────────────────────────────────────────────────────────────
class ConversationState(TypedDict):
    messages: Annotated[list, add_messages]
    nome: str
    email: str
    telefone: str
    perfil: str
    conversation_id: str
    is_closed: bool
    awaiting_pdf: bool
    pdf_received: bool


# ── Helpers ───────────────────────────────────────────────────────────────────
_ENCERRAMENTO_PHRASES = [
    "bom falar com você, até mais!",
    "não estamos conseguindo nos entender",
]

def _conversation_ended(text: str) -> bool:
    return any(p in text.lower() for p in _ENCERRAMENTO_PHRASES)

def _resolve_prompt(perfil: str) -> str:
    perfil_clean = perfil.strip()
    if perfil_clean in AGENT_PROMPTS:
        return AGENT_PROMPTS[perfil_clean]
    perfil_lower = perfil_clean.lower()
    for key, prompt in AGENT_PROMPTS.items():
        if key.lower() == perfil_lower:
            return prompt
    for key, prompt in AGENT_PROMPTS.items():
        if perfil_lower in key.lower() or key.lower() in perfil_lower:
            return prompt
    logger.warning(f"Perfil '{perfil_clean}' não reconhecido. Usando DEFAULT.")
    return DEFAULT_PROMPT


# ── Nó: chamar o LLM ─────────────────────────────────────────────────────────
def call_llm(state: ConversationState) -> ConversationState:
    settings = get_settings()
    conversation_id = state.get("conversation_id", "")
    all_messages = list(state["messages"])

    # ── Verifica última resposta do assistente ────────────────────────────────
    last_ai = next(
        (m.content for m in reversed(all_messages[:-1]) if isinstance(m, AIMessage)),
        ""
    )
    last_user = all_messages[-1].content if all_messages else ""

    # ── Gerencia contagem de tentativas inválidas via store ───────────────────
    last_was_invalid = "desculpe, não entendi bem" in last_ai.lower()
    current_attempts = store._invalid_attempts.get(conversation_id, 0)

    if last_was_invalid:
        # Última resposta do bot foi "Desculpe" → usuário respondeu de novo
        # Se essa nova resposta ainda é inválida, o LLM vai dizer "Desculpe" novamente
        # Mas se já chegamos em 2 → encerra direto sem chamar o LLM
        current_attempts += 1
        store._invalid_attempts[conversation_id] = current_attempts
        logger.info(f"[TENTATIVAS] {conversation_id}: {current_attempts}")
    else:
        # Última resposta do bot foi válida → reseta contador
        store._invalid_attempts[conversation_id] = 0
        current_attempts = 0

    # ── Encerra por incompreensão na 2ª tentativa inválida ───────────────────
    if current_attempts >= 2:
        store._invalid_attempts[conversation_id] = 0
        logger.info(f"[ENCERRA] 2 tentativas inválidas → encerrando {conversation_id}")
        return {
            "messages": [AIMessage(content=MSG_NAO_ENTENDEMOS)],
            "is_closed": True,
            "awaiting_pdf": state.get("awaiting_pdf", False),
        }

    # ── Chama o LLM normalmente ───────────────────────────────────────────────
    llm = ChatOpenAI(
        model=settings.openai_model,
        api_key=settings.openai_api_key,
        temperature=0.3,
        max_tokens=500,
    )

    system_prompt = _resolve_prompt(state.get("perfil", ""))
    system_prompt = system_prompt.replace("{nome}", state.get("nome", ""))

    messages = [SystemMessage(content=system_prompt)] + all_messages
    response = llm.invoke(messages)

    # Se o LLM disse "Desculpe" agora, incrementa o contador para a próxima vez
    if "desculpe, não entendi bem" in response.content.lower():
        store._invalid_attempts[conversation_id] = current_attempts + 1
        logger.info(f"[TENTATIVAS] LLM disse Desculpe → contador: {current_attempts + 1}")

    is_closed = _conversation_ended(response.content)

    return {
        "messages": [AIMessage(content=response.content)],
        "is_closed": is_closed,
        "awaiting_pdf": state.get("awaiting_pdf", False),
    }


# ── Nó: encerrar conversa ────────────────────────────────────────────────────
def close_conversation_node(state: ConversationState) -> ConversationState:
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
    graph.add_conditional_edges(
        "call_llm",
        should_close,
        {"close": "close_conversation", END: END}
    )
    graph.add_edge("close_conversation", END)
    return graph.compile()


imatchy_graph = build_graph()
