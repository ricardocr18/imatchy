"""
app/agents/personas/__init__.py
Mapa central de perfis → prompts.
Inclui todas as variações de escrita para cada perfil
para evitar erros de digitação ou capitalização.
"""
from app.agents.personas.investidor import INVESTIDOR_PROMPT
from app.agents.personas.pesquisador import PESQUISADOR_PROMPT
from app.agents.personas.startup import STARTUP_PROMPT
from app.agents.personas.corporacao import CORPORACAO_PROMPT
from app.agents.personas.governo import GOVERNO_PROMPT
from app.agents.personas.aceleradora import ACELERADORA_PROMPT
from app.agents.personas.universidade import UNIVERSIDADE_PROMPT
from app.agents.personas.mentor import MENTOR_PROMPT
from app.agents.personas.profissional import PROFISSIONAL_PROMPT

AGENT_PROMPTS: dict[str, str] = {

    # ── Investidor ────────────────────────────────────────────────────────────
    "Investidor": INVESTIDOR_PROMPT,
    "investidor": INVESTIDOR_PROMPT,
    "Investor": INVESTIDOR_PROMPT,
    "investor": INVESTIDOR_PROMPT,
    "Fundo": INVESTIDOR_PROMPT,
    "fundo": INVESTIDOR_PROMPT,
    "Fundo de Investimento": INVESTIDOR_PROMPT,
    "Angel": INVESTIDOR_PROMPT,
    "angel": INVESTIDOR_PROMPT,
    "Anjo": INVESTIDOR_PROMPT,
    "anjo": INVESTIDOR_PROMPT,

    # ── Pesquisador ou Cientista ──────────────────────────────────────────────
    "Pesquisador ou Cientista": PESQUISADOR_PROMPT,
    "pesquisador ou cientista": PESQUISADOR_PROMPT,
    "Pesquisador": PESQUISADOR_PROMPT,
    "pesquisador": PESQUISADOR_PROMPT,
    "Cientista": PESQUISADOR_PROMPT,
    "cientista": PESQUISADOR_PROMPT,
    "Researcher": PESQUISADOR_PROMPT,
    "researcher": PESQUISADOR_PROMPT,
    "Doutor": PESQUISADOR_PROMPT,
    "doutor": PESQUISADOR_PROMPT,
    "Professor": PESQUISADOR_PROMPT,
    "professor": PESQUISADOR_PROMPT,
    "Pós-doc": PESQUISADOR_PROMPT,
    "pos-doc": PESQUISADOR_PROMPT,

    # ── Startup ───────────────────────────────────────────────────────────────
    "Startup": STARTUP_PROMPT,
    "startup": STARTUP_PROMPT,
    "Founder": STARTUP_PROMPT,
    "founder": STARTUP_PROMPT,
    "Cofundador": STARTUP_PROMPT,
    "cofundador": STARTUP_PROMPT,
    "Co-fundador": STARTUP_PROMPT,
    "co-fundador": STARTUP_PROMPT,
    "Empreendedor": STARTUP_PROMPT,
    "empreendedor": STARTUP_PROMPT,
    "CEO": STARTUP_PROMPT,
    "ceo": STARTUP_PROMPT,
    "CTO": STARTUP_PROMPT,
    "cto": STARTUP_PROMPT,
    "Startup / Founder": STARTUP_PROMPT,
    "startup / founder": STARTUP_PROMPT,

    # ── Corporação / Empresa ──────────────────────────────────────────────────
    "Corporação": CORPORACAO_PROMPT,
    "corporação": CORPORACAO_PROMPT,
    "Corporacao": CORPORACAO_PROMPT,
    "corporacao": CORPORACAO_PROMPT,
    "Empresa": CORPORACAO_PROMPT,
    "empresa": CORPORACAO_PROMPT,
    "Empresa / Inovação Aberta": CORPORACAO_PROMPT,
    "empresa / inovação aberta": CORPORACAO_PROMPT,
    "Inovação Aberta": CORPORACAO_PROMPT,
    "inovação aberta": CORPORACAO_PROMPT,
    "Inovacao Aberta": CORPORACAO_PROMPT,
    "inovacao aberta": CORPORACAO_PROMPT,
    "Indústria": CORPORACAO_PROMPT,
    "indústria": CORPORACAO_PROMPT,
    "industria": CORPORACAO_PROMPT,
    "Corporate": CORPORACAO_PROMPT,
    "corporate": CORPORACAO_PROMPT,

    # ── Instituição do Governo ────────────────────────────────────────────────
    "Instituição do Governo": GOVERNO_PROMPT,
    "instituição do governo": GOVERNO_PROMPT,
    "Instituicao do Governo": GOVERNO_PROMPT,
    "instituicao do governo": GOVERNO_PROMPT,
    "Governo": GOVERNO_PROMPT,
    "governo": GOVERNO_PROMPT,
    "Órgão Público": GOVERNO_PROMPT,
    "orgao publico": GOVERNO_PROMPT,
    "Órgão Governamental": GOVERNO_PROMPT,
    "orgao governamental": GOVERNO_PROMPT,
    "Agência": GOVERNO_PROMPT,
    "agência": GOVERNO_PROMPT,
    "agencia": GOVERNO_PROMPT,
    "Ministério": GOVERNO_PROMPT,
    "ministerio": GOVERNO_PROMPT,
    "Prefeitura": GOVERNO_PROMPT,
    "prefeitura": GOVERNO_PROMPT,
    "Secretaria": GOVERNO_PROMPT,
    "secretaria": GOVERNO_PROMPT,

    # ── Aceleradora / Incubadora / Hub ────────────────────────────────────────
    "Aceleradora / Incubadora / Hub de Inovação": ACELERADORA_PROMPT,
    "aceleradora / incubadora / hub de inovação": ACELERADORA_PROMPT,
    "Aceleradora": ACELERADORA_PROMPT,
    "aceleradora": ACELERADORA_PROMPT,
    "Incubadora": ACELERADORA_PROMPT,
    "incubadora": ACELERADORA_PROMPT,
    "Hub de Inovação": ACELERADORA_PROMPT,
    "hub de inovação": ACELERADORA_PROMPT,
    "Hub": ACELERADORA_PROMPT,
    "hub": ACELERADORA_PROMPT,
    "Acelerador": ACELERADORA_PROMPT,
    "acelerador": ACELERADORA_PROMPT,
    "Parque Tecnológico": ACELERADORA_PROMPT,
    "parque tecnologico": ACELERADORA_PROMPT,

    # ── Universidade / Instituição de Pesquisa ────────────────────────────────
    "Universidade ou Instituição de Pesquisa": UNIVERSIDADE_PROMPT,
    "universidade ou instituição de pesquisa": UNIVERSIDADE_PROMPT,
    "Universidade": UNIVERSIDADE_PROMPT,
    "universidade": UNIVERSIDADE_PROMPT,
    "Instituição de Pesquisa": UNIVERSIDADE_PROMPT,
    "instituição de pesquisa": UNIVERSIDADE_PROMPT,
    "Instituicao de Pesquisa": UNIVERSIDADE_PROMPT,
    "instituicao de pesquisa": UNIVERSIDADE_PROMPT,
    "Faculdade": UNIVERSIDADE_PROMPT,
    "faculdade": UNIVERSIDADE_PROMPT,
    "Instituto": UNIVERSIDADE_PROMPT,
    "instituto": UNIVERSIDADE_PROMPT,
    "ICT": UNIVERSIDADE_PROMPT,
    "ict": UNIVERSIDADE_PROMPT,
    "NIT": UNIVERSIDADE_PROMPT,
    "nit": UNIVERSIDADE_PROMPT,

    # ── Mentor ou Consultor ───────────────────────────────────────────────────
    "Mentor ou Consultor": MENTOR_PROMPT,
    "mentor ou consultor": MENTOR_PROMPT,
    "Mentor": MENTOR_PROMPT,
    "mentor": MENTOR_PROMPT,
    "Consultor": MENTOR_PROMPT,
    "consultor": MENTOR_PROMPT,
    "Advisor": MENTOR_PROMPT,
    "advisor": MENTOR_PROMPT,
    "Conselheiro": MENTOR_PROMPT,
    "conselheiro": MENTOR_PROMPT,
    "Especialista": MENTOR_PROMPT,
    "especialista": MENTOR_PROMPT,

    # ── Profissional Especializado ou Técnico ─────────────────────────────────
    "Profissional Especializado ou Técnico": PROFISSIONAL_PROMPT,
    "profissional especializado ou técnico": PROFISSIONAL_PROMPT,
    "Profissional Especializado ou Tecnico": PROFISSIONAL_PROMPT,
    "profissional especializado ou tecnico": PROFISSIONAL_PROMPT,
    "Profissional": PROFISSIONAL_PROMPT,
    "profissional": PROFISSIONAL_PROMPT,
    "Técnico": PROFISSIONAL_PROMPT,
    "técnico": PROFISSIONAL_PROMPT,
    "tecnico": PROFISSIONAL_PROMPT,
    "Desenvolvedor": PROFISSIONAL_PROMPT,
    "desenvolvedor": PROFISSIONAL_PROMPT,
    "Developer": PROFISSIONAL_PROMPT,
    "developer": PROFISSIONAL_PROMPT,
    "Engenheiro": PROFISSIONAL_PROMPT,
    "engenheiro": PROFISSIONAL_PROMPT,
    "Designer": PROFISSIONAL_PROMPT,
    "designer": PROFISSIONAL_PROMPT,
    "Cientista de Dados": PROFISSIONAL_PROMPT,
    "cientista de dados": PROFISSIONAL_PROMPT,
    "Data Scientist": PROFISSIONAL_PROMPT,
    "data scientist": PROFISSIONAL_PROMPT,
}

DEFAULT_PROMPT = INVESTIDOR_PROMPT
