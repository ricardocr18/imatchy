"""
app/agents/graph.py — LangGraph com suporte a PT, EN, ES
"""
from __future__ import annotations
import logging
from typing import Annotated, TypedDict

from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
from langchain_openai import ChatOpenAI
from langgraph.graph import END, StateGraph
from langgraph.graph.message import add_messages

from app.agents.personas import AGENT_PROMPTS_BY_LANG, DEFAULT_PROMPT
from app.core.config import get_settings
import app.core.supabase_client as store

logger = logging.getLogger(__name__)

MSG_NAO_ENTENDEMOS = {
    "PT": "Acredito que não estamos conseguindo nos entender. Depois a equipe da Conecta Cientista vai entrar em contato com você para entender melhor seus interesses.",
    "EN": "I believe we're having trouble understanding each other. The Conecta Cientista team will get in touch with you soon to better understand your interests.",
    "ES": "Creo que no nos estamos entendiendo bien. El equipo de Conecta Cientista se pondrá en contacto contigo para entender mejor tus intereses.",
}


class ConversationState(TypedDict):
    messages: Annotated[list, add_messages]
    nome: str
    email: str
    telefone: str
    perfil: str
    language: str
    conversation_id: str
    is_closed: bool
    awaiting_pdf: bool
    pdf_received: bool


_ENCERRAMENTO_PHRASES = [
    "bom falar com você, até mais!",
    "great talking to you, see you soon!",
    "un placer hablar contigo, hasta pronto!",
    "não estamos conseguindo nos entender",
    "having trouble understanding each other",
    "no nos estamos entendiendo",
]

def _conversation_ended(text: str) -> bool:
    return any(p in text.lower() for p in _ENCERRAMENTO_PHRASES)


def _resolve_prompt(perfil: str, language: str) -> str:
    lang = language.upper().strip() if language else "PT"
    if lang not in AGENT_PROMPTS_BY_LANG:
        lang = "PT"

    prompts = AGENT_PROMPTS_BY_LANG[lang]
    perfil_clean = perfil.strip()

    if perfil_clean in prompts:
        logger.info(f"Perfil resolvido (exato) [{lang}]: '{perfil_clean}'")
        return prompts[perfil_clean]

    perfil_lower = perfil_clean.lower()
    for key, prompt in prompts.items():
        if key.lower() == perfil_lower:
            logger.info(f"Perfil resolvido (case-insensitive) [{lang}]: '{perfil_clean}' → '{key}'")
            return prompt

    for key, prompt in prompts.items():
        if perfil_lower in key.lower() or key.lower() in perfil_lower:
            logger.info(f"Perfil resolvido (parcial) [{lang}]: '{perfil_clean}' → '{key}'")
            return prompt

    logger.warning(f"Perfil '{perfil_clean}' não reconhecido em [{lang}]. Usando DEFAULT PT.")
    return DEFAULT_PROMPT


def call_llm(state: ConversationState) -> ConversationState:
    settings = get_settings()
    conversation_id = state.get("conversation_id", "")
    language = state.get("language", "PT").upper()
    all_messages = list(state["messages"])

    last_ai = next(
        (m.content for m in reversed(all_messages[:-1]) if isinstance(m, AIMessage)),
        ""
    )

    _invalid_markers = [
        "desculpe, não entendi bem",
        "i didn't quite understand",
        "no entendí bien",
        "não entendi bem",
        "não estamos conseguindo nos entender",
    ]
    last_was_invalid = any(m in last_ai.lower() for m in _invalid_markers)

    current_attempts = store._invalid_attempts.get(conversation_id, 0)

    if last_was_invalid:
        current_attempts += 1
        store._invalid_attempts[conversation_id] = current_attempts
    else:
        store._invalid_attempts[conversation_id] = 0
        current_attempts = 0

    if current_attempts >= 2:
        store._invalid_attempts[conversation_id] = 0
        msg = MSG_NAO_ENTENDEMOS.get(language, MSG_NAO_ENTENDEMOS["PT"])
        return {
            "messages": [AIMessage(content=msg)],
            "is_closed": True,
            "awaiting_pdf": state.get("awaiting_pdf", False),
        }

    llm = ChatOpenAI(
        model=settings.openai_model,
        api_key=settings.openai_api_key,
        temperature=0.3,
        max_tokens=800,
    )

    nome = state.get("nome", "")
    system_prompt = _resolve_prompt(state.get("perfil", ""), language)
    system_prompt = system_prompt.replace("{nome}", nome)

    # Reforça o encerramento no idioma correto com o nome já substituído
    _encerramentos = {
        "PT": f'Perfeito, {nome}! Seu perfil está sendo preparado para a Conecta Cientista. Nossa IA irá analisar suas competências, interesses e oportunidades para gerar conexões mais estratégicas dentro do ecossistema de inovação, ciência, startups e negócios. Bom falar com você, até mais! Obrigado!',
        "EN": f'Perfect, {nome}! Your profile is being prepared for Conecta Cientista. Our AI will analyze your skills, interests, and opportunities to generate more strategic connections within the innovation, science, startups, and business ecosystem. Great talking to you, see you soon! Thank you!',
        "ES": f'¡Perfecto, {nome}! Tu perfil está siendo preparado para Conecta Cientista. Nuestra IA analizará tus competencias, intereses y oportunidades para generar conexiones más estratégicas dentro del ecosistema de innovación, ciencia, startups y negocios. ¡Un placer hablar contigo, hasta pronto! ¡Gracias!',
    }
    encerramento_final = _encerramentos.get(language, _encerramentos["PT"])

    _instrucao_final = {
        "PT": f"""

=== MENSAGEM FINAL OBRIGATÓRIA ===
ATENÇÃO: Você DEVE fazer TODAS as perguntas do roteiro antes de encerrar.
A última pergunta é OBRIGATÓRIA — ela oferece ao usuário a opção de enviar um PDF.
Somente APÓS receber qualquer resposta à última pergunta, envie EXATAMENTE esta mensagem, sem alterar uma vírgula, sem traduzir:

{encerramento_final}

NÃO encerre antes da última pergunta. NÃO pule a última pergunta. NÃO envie o encerramento junto com a última pergunta.
""",
        "EN": f"""

=== MANDATORY FINAL MESSAGE ===
IMPORTANT: You MUST ask ALL questions in the script before closing.
The last question is MANDATORY — it offers the user the option to send a PDF.
Only AFTER receiving any response to the last question, send EXACTLY this message, without changing a single word:

{encerramento_final}

DO NOT close before the last question. DO NOT skip the last question. DO NOT send the closing message together with the last question.
""",
        "ES": f"""

=== MENSAJE FINAL OBLIGATORIO ===
ATENCIÓN: DEBES hacer TODAS las preguntas del guión antes de cerrar.
La última pregunta es OBLIGATORIA — ofrece al usuario la opción de enviar un PDF.
Solo DESPUÉS de recibir cualquier respuesta a la última pregunta, envía EXACTAMENTE este mensaje, sin cambiar ni una coma:

{encerramento_final}

NO cierres antes de la última pregunta. NO omitas la última pregunta. NO envíes el mensaje de cierre junto con la última pregunta.
""",
    }
    system_prompt += _instrucao_final.get(language, _instrucao_final["PT"])

    messages = [SystemMessage(content=system_prompt)] + all_messages
    response = llm.invoke(messages)

    invalid_phrases = [
        "desculpe, não entendi bem",
        "não entendi bem",
        "i didn't quite understand",
        "no entendí bien",
    ]
    if any(p in response.content.lower() for p in invalid_phrases):
        store._invalid_attempts[conversation_id] = current_attempts + 1
        logger.info(f"[TENTATIVAS] LLM disse frase inválida → contador: {current_attempts + 1}")

    return {
        "messages": [AIMessage(content=response.content)],
        "is_closed": _conversation_ended(response.content),
        "awaiting_pdf": state.get("awaiting_pdf", False),
    }


def close_conversation_node(state: ConversationState) -> ConversationState:
    return {"is_closed": True}


def should_close(state: ConversationState) -> str:
    return "close" if state.get("is_closed") else END


def build_graph() -> StateGraph:
    graph = StateGraph(ConversationState)
    graph.add_node("call_llm", call_llm)
    graph.add_node("close_conversation", close_conversation_node)
    graph.set_entry_point("call_llm")
    graph.add_conditional_edges("call_llm", should_close, {"close": "close_conversation", END: END})
    graph.add_edge("close_conversation", END)
    return graph.compile()


imatchy_graph = build_graph()