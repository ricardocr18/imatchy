"""
app/agents/prompts.py
Ponto de entrada para importação dos prompts — mantido por compatibilidade.
Os prompts individuais agora ficam em app/agents/personas/
"""
from app.agents.personas import AGENT_PROMPTS, DEFAULT_PROMPT

__all__ = ["AGENT_PROMPTS", "DEFAULT_PROMPT"]
