# iMatchy — ChatBot WhatsApp

Chatbot WhatsApp para a plataforma **Conecta Cientista**, powered by:
- **Twilio** (WhatsApp gateway)
- **OpenAI GPT-4o-mini** (LLM do agente)
- **OpenAI Whisper** (transcrição de áudio)
- **LangGraph** (orquestração do fluxo do agente)
- **Supabase** (histórico de conversas + Storage de PDFs)
- **FastAPI** (backend webhook)
- **Lovable** (Frontend React, repositório conectado via GitHub)

---

## Estrutura do Projeto

```
imatchy/
├── app/
│   ├── main.py                  # FastAPI entry point
│   ├── api/
│   │   └── webhook.py           # POST /webhook/whatsapp
│   ├── agents/
│   │   ├── graph.py             # LangGraph — grafo da conversa
│   │   └── prompts.py           # System prompts de cada persona
│   ├── core/
│   │   ├── config.py            # Configurações (.env)
│   │   └── supabase_client.py   # CRUD no Supabase
│   └── utils/
│       └── media.py             # Whisper + validação PDF
├── frontend/
│   └── ImatchyForm.jsx          # Componente React (copie para o Lovable)
├── scripts/
│   └── supabase_schema.sql      # DDL das tabelas Supabase
├── tests/
├── .env.example
├── requirements.txt
└── README.md
```

---

## Configuração Local

### 1. Clone e instale dependências

```bash
git clone https://github.com/SEU_USUARIO/imatchy.git
cd imatchy
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
```

### 2. Configure as variáveis de ambiente

```bash
cp .env.example .env
# Edite .env com suas chaves reais
```

### 3. Crie as tabelas no Supabase

Acesse **SQL Editor** no painel Supabase e execute:
```bash
scripts/supabase_schema.sql
```

Depois crie o bucket de storage:
- Supabase > Storage > New bucket
- Nome: `imatchy-pdfs`
- Public: ✅

### 4. Suba o servidor local com ngrok

```bash
# Terminal 1 — backend
uvicorn app.main:app --reload --port 8000

# Terminal 2 — túnel público
ngrok http 8000
```

Copie a URL HTTPS do ngrok (ex: `https://abc123.ngrok-free.app`).

### 5. Configure o webhook no Twilio

1. Acesse [Twilio Console](https://console.twilio.com) > Phone Numbers > Active Numbers
2. Clique no número `+1 978 381 8754`
3. Em **Messaging** > Webhook URL: `https://abc123.ngrok-free.app/webhook/whatsapp`
4. Método: **HTTP POST**
5. Salve.

---

## Testando

Envie no WhatsApp para o número Twilio:
```
Oi iMatchy, sou João Silva.
E-mail: joao@exemplo.com
Telefone: +5511999999999
Perfil: Investidor
```

---

## Deploy Produção

### Backend (ex: Railway / Render / Fly.io)

```bash
# Variável de ambiente obrigatória
BASE_URL=https://seu-dominio.com
```

No Twilio, atualize o webhook para a URL de produção.

### Frontend → Lovable

1. Suba este repositório no GitHub
2. Em **Lovable**: Settings > GitHub > Connect Repository
3. Copie `frontend/ImatchyForm.jsx` para o projeto Lovable
4. O componente usa o número Twilio hardcoded — altere `IMATCHY_NUMBER` se necessário

---

## Fluxo da Conversa

```
Usuário clica "Continuar pelo WhatsApp"
  ↓ deep link abre WhatsApp com mensagem pré-formatada
  ↓ Twilio recebe a mensagem
  ↓ POST /webhook/whatsapp
  ↓ LangGraph: histórico + system prompt do agente selecionado
  ↓ GPT-4o-mini gera resposta
  ↓ Twilio envia resposta
  ↓ Salva no Supabase (mensagem + PDF quando enviado)
  ↓ Quando detecta ENCERRAMENTO → fecha conversa no Supabase
```

## Regras de Negócio

- **Áudio**: recebido via WhatsApp → Whisper transcreve → LLM processa → responde em texto
- **PDF**: aceito apenas quando o agente solicitar explicitamente (Pergunta 5)
  - Extensão: somente `.pdf`
  - Tamanho: máximo 3 MB
  - Salvo no Supabase Storage em `imatchy-pdfs/{conversation_id}/`
- **Encerramento**: após frase de encerramento, conversa marcada como `closed` — nenhuma resposta adicional

## Adicionando Novos Agentes

Edite `app/agents/prompts.py` e adicione a nova persona ao dicionário `AGENT_PROMPTS`:

```python
AGENT_PROMPTS: dict[str, str] = {
    "Investidor": INVESTOR_PROMPT,
    "Startup": STARTUP_PROMPT,          # adicione aqui
    "Pesquisador ou Cientista": ...,    # e aqui
}
```
