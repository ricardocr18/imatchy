# iMatchy — ChatBot WhatsApp · Conecta Cientista

Chatbot WhatsApp inteligente para a plataforma **Conecta Cientista**, com suporte a **3 idiomas (PT, EN, ES)** e **9 perfis de agentes**.

## Stack

| Camada | Tecnologia |
|---|---|
| Backend | Python · FastAPI · LangGraph |
| LLM | OpenAI GPT-4o-mini |
| Transcrição de áudio | OpenAI Whisper |
| WhatsApp gateway | Twilio |
| Banco de dados + Storage | Supabase |
| Frontend | React via Lovable |

---

## Estrutura do Projeto

```
imatchy/
├── app/
│   ├── main.py                        # FastAPI entry point
│   ├── api/
│   │   └── webhook.py                 # POST /webhook/whatsapp
│   ├── agents/
│   │   ├── graph.py                   # LangGraph — grafo + roteamento PT/EN/ES
│   │   ├── prompts.py                 # Re-exporta AGENT_PROMPTS
│   │   └── personas/
│   │       ├── __init__.py            # Mapa perfil+idioma → prompt
│   │       ├── shared_rules.py        # Regras absolutas PT · EN · ES
│   │       ├── investidor.py
│   │       ├── pesquisador.py
│   │       ├── startup.py
│   │       ├── corporacao.py
│   │       ├── governo.py
│   │       ├── aceleradora.py
│   │       ├── universidade.py
│   │       ├── mentor.py
│   │       └── profissional.py
│   ├── core/
│   │   ├── config.py                  # Configurações via .env
│   │   └── supabase_client.py         # CRUD Supabase (em memória no modo teste)
│   └── utils/
│       └── media.py                   # Whisper + validação PDF
├── frontend/
│   └── ImatchyForm.jsx                # Componente React — botão "Continuar pelo WhatsApp"
├── scripts/
│   └── supabase_schema.sql            # DDL das tabelas + bucket Storage
├── tests/
│   └── test_webhook.py
├── .env.example
├── requirements.txt
└── README.md
```

---

## Variáveis de Ambiente

Copie `.env.example` para `.env` e preencha:

```env
# Twilio
TWILIO_ACCOUNT_SID=ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
TWILIO_AUTH_TOKEN=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
TWILIO_WHATSAPP_NUMBER=+19783818754

# OpenAI
OPENAI_API_KEY=sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
OPENAI_MODEL=gpt-4o-mini
WHISPER_MODEL=whisper-1

# Supabase
SUPABASE_URL=https://xxxxxxxxxxx.supabase.co
SUPABASE_SERVICE_KEY=eyJxxxxxxx   # chave service_role (não a anon)

# App
APP_ENV=development
APP_SECRET=string-aleatoria-longa
BASE_URL=http://localhost:8000
PDF_MAX_BYTES=3145728
```

---

## Setup Local

```bash
# 1. Clone e instale
git clone https://github.com/ricardocr18/imatchy.git
cd imatchy
python -m venv .venv
.venv\Scripts\activate        # Windows
# source .venv/bin/activate   # Mac/Linux
pip install -r requirements.txt

# 2. Configure o .env
cp .env.example .env

# 3. Suba o servidor
uvicorn app.main:app --reload --port 8000

# 4. Exponha com ngrok (outro terminal)
ngrok http 8000
```

---

## Configuração Supabase

Execute `scripts/supabase_schema.sql` no **SQL Editor** do seu projeto Supabase.

Crie o bucket de storage:
- Supabase → Storage → New bucket
- Nome: `imatchy-pdfs` · Public: ✅

Tabelas criadas:
- `conversations` — registro de cada conversa (nome, telefone, perfil, idioma, status)
- `messages` — histórico completo de mensagens
- `pdf_files` — registro dos PDFs enviados com URL no Storage

---

## Configuração Twilio

1. Acesse [Twilio Console](https://console.twilio.com) → Messaging → Senders → WhatsApp Senders
2. Clique em **Edit Sender** no número `+1 978 381 8754`
3. Em **Webhook URL for incoming messages**: cole a URL do ngrok + `/webhook/whatsapp`
4. Método: **HTTP POST** → Salve

---

## Agentes Disponíveis

| Perfil | PT | EN | ES |
|---|---|---|---|
| Investidor | ✅ | ✅ | ✅ |
| Pesquisador ou Cientista | ✅ | ✅ | ✅ |
| Startup | ✅ | ✅ | ✅ |
| Corporação | ✅ | ✅ | ✅ |
| Instituição do Governo | ✅ | ✅ | ✅ |
| Aceleradora / Incubadora / Hub | ✅ | ✅ | ✅ |
| Universidade ou Inst. de Pesquisa | ✅ | ✅ | ✅ |
| Mentor ou Consultor | ✅ | ✅ | ✅ |
| Profissional Especializado ou Técnico | ✅ | ✅ | ✅ |

---

## Payload do Botão "Continuar pelo WhatsApp"

O frontend deve gerar um deep link com a mensagem pré-formatada:

```
Oi iMatchy, sou {Nome completo}.
E-mail: {email}
Telefone: {whatsapp}
Perfil: {perfil selecionado}
Language: {PT | EN | ES}
```

**Número destino (fixo):** `551151947349`

**Formato da URL:**
```
https://api.whatsapp.com/send/?phone=551151947349&text={mensagem codificada em URL}&type=phone_number&app_absent=0
```

**Exemplo real:**
```
https://api.whatsapp.com/send/?phone=551151947349&text=Oi+iMatchy%2C+sou+Ricardo+Ribeiro.%0AE-mail%3A+ricardo%40gmail.com%0ATelefone%3A+%2B5561993981536%0APerfil%3A+Investidor%0ALanguage%3A+PT&type=phone_number&app_absent=0
```

O componente React pronto está em `frontend/ImatchyForm.jsx`.

---

## Regras de Negócio

- **Áudio**: recebido → Whisper transcreve → LLM processa → responde em texto
- **PDF**: aceito apenas quando o agente solicitar explicitamente (última pergunta)
  - Extensão: `.pdf` obrigatório
  - Tamanho: máximo 3 MB
  - Storage: `imatchy-pdfs/{conversation_id}/`
  - Encerramento automático após recebimento
- **Idioma**: PT tem validação de respostas inválidas com 2 tentativas. EN e ES aceitam qualquer resposta e avançam
- **Encerramento**: após mensagem final, conversa marcada como `closed` no Supabase

---

## Adicionando Novos Agentes

1. Crie `app/agents/personas/novo_agente.py` seguindo o padrão dos existentes (com versões `_PT`, `_EN`, `_ES`)
2. Importe e adicione ao mapa em `app/agents/personas/__init__.py`

---

## Branches

| Branch | Descrição |
|---|---|
| `main` | Versão estável para produção / Lovable |
| `botTexto_V3` | Desenvolvimento atual |