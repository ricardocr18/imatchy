-- ============================================================
-- iMatchy — schema Supabase
-- Execute no SQL Editor do seu projeto Supabase
-- ============================================================

-- Tabela principal de conversas
create table if not exists conversations (
  id          text primary key,
  phone       text not null,
  name        text,
  email       text,
  profile     text,
  status      text not null default 'active',  -- 'active' | 'closed'
  created_at  timestamptz not null default now(),
  updated_at  timestamptz not null default now()
);

-- Mensagens de cada conversa
create table if not exists messages (
  id               bigserial primary key,
  conversation_id  text not null references conversations(id) on delete cascade,
  role             text not null,  -- 'user' | 'assistant'
  content          text not null,
  created_at       timestamptz not null default now()
);

-- Registro dos PDFs enviados
create table if not exists pdf_files (
  id               bigserial primary key,
  conversation_id  text not null references conversations(id) on delete cascade,
  filename         text not null,
  storage_url      text not null,
  created_at       timestamptz not null default now()
);

-- Índice para busca rápida por conversa
create index if not exists messages_conversation_id_idx on messages(conversation_id);
create index if not exists pdf_files_conversation_id_idx on pdf_files(conversation_id);

-- Atualiza updated_at automaticamente
create or replace function update_updated_at()
returns trigger language plpgsql as $$
begin
  new.updated_at = now();
  return new;
end;
$$;

create or replace trigger conversations_updated_at
  before update on conversations
  for each row execute procedure update_updated_at();

-- Bucket de storage para PDFs (execute separadamente no painel Supabase
-- Storage > New bucket > name: imatchy-pdfs > public: true)
-- ou via API:
-- insert into storage.buckets (id, name, public) values ('imatchy-pdfs', 'imatchy-pdfs', true);
