/**
 * ImatchyForm.jsx
 * 
 * Componente standalone do formulário iMatchy.
 * Cole dentro do seu projeto Lovable / React.
 * 
 * Ao clicar "Continuar pelo WhatsApp" abre o app com a mensagem pré-formatada:
 *   Oi iMatchy, sou {Nome}.
 *   E-mail: {email}
 *   Telefone: {whatsapp}
 *   Perfil: {perfil}
 * 
 * O número destino é o Twilio: 551151947349
 */

import { useState } from "react";

const PROFILES = [
  "Pesquisador ou Cientista",
  "Startup",
  "Investidor",
  "Corporação",
  "Profissional Especializado ou Técnico",
  "Instituição do Governo",
  "Aceleradora / Incubadora / Hub de Inovação",
  "Universidade ou Instituição de Pesquisa",
  "Mentor ou Consultor",
];

// Número do Twilio que receberá as mensagens
const IMATCHY_NUMBER = "551151947349";

function buildWhatsAppURL(nome, email, whatsapp, perfil) {
  const clean = whatsapp.replace(/\D/g, "");
  const msg = [
    `Oi iMatchy, sou ${nome}.`,
    `E-mail: ${email}`,
    `Telefone: +${clean}`,
    `Perfil: ${perfil}`,
  ].join("\n");

  return `https://api.whatsapp.com/send/?phone=${IMATCHY_NUMBER}&text=${encodeURIComponent(msg)}&type=phone_number&app_absent=0`;
}

export default function ImatchyForm() {
  const [form, setForm] = useState({ nome: "", whatsapp: "", email: "", perfil: "" });
  const [errors, setErrors] = useState({});

  function validate() {
    const e = {};
    if (!form.nome.trim()) e.nome = "Informe seu nome completo";
    if (!form.whatsapp.trim()) e.whatsapp = "Informe seu WhatsApp";
    if (!form.email.trim() || !form.email.includes("@")) e.email = "E-mail inválido";
    if (!form.perfil) e.perfil = "Selecione seu perfil";
    setErrors(e);
    return Object.keys(e).length === 0;
  }

  function handleWhatsApp() {
    if (!validate()) return;
    const url = buildWhatsAppURL(form.nome, form.email, form.whatsapp, form.perfil);
    window.open(url, "_blank", "noopener,noreferrer");
  }

  function set(field) {
    return (e) => {
      setForm((prev) => ({ ...prev, [field]: e.target.value }));
      setErrors((prev) => ({ ...prev, [field]: undefined }));
    };
  }

  return (
    <div style={styles.card}>
      <h2 style={styles.title}>Conversa com o iMatchy</h2>
      <p style={styles.desc}>
        Para entender melhor sua experiência e interesses, você pode conversar com o
        iMatchy — o agente inteligente que vai coletar informações para o melhor match.
      </p>

      <div style={styles.grid}>
        <Field label="Nome" error={errors.nome}>
          <input
            style={styles.input}
            placeholder="Digite seu nome completo"
            value={form.nome}
            onChange={set("nome")}
          />
        </Field>

        <Field label="WhatsApp" error={errors.whatsapp}>
          <input
            style={styles.input}
            placeholder="+55 11 98765-4321"
            value={form.whatsapp}
            onChange={set("whatsapp")}
          />
        </Field>

        <Field label="E-mail" error={errors.email}>
          <input
            style={styles.input}
            placeholder="seu@email.com"
            value={form.email}
            onChange={set("email")}
            type="email"
          />
        </Field>

        <Field label="Perfil" error={errors.perfil}>
          <select style={{ ...styles.input, ...styles.select }} value={form.perfil} onChange={set("perfil")}>
            <option value="">Selecione seu perfil</option>
            {PROFILES.map((p) => (
              <option key={p} value={p}>{p}</option>
            ))}
          </select>
        </Field>
      </div>

      <div style={styles.divider}>
        <span style={styles.dividerText}>Escolha como deseja continuar</span>
      </div>

      <div style={styles.actions}>
        <button style={{ ...styles.btn, ...styles.btnSecondary }} disabled>
          {/* Botão reservado para canal alternativo */}
          Continuar pelo Chat
        </button>
        <button style={{ ...styles.btn, ...styles.btnWhatsApp }} onClick={handleWhatsApp}>
          <WhatsAppIcon />
          Continuar pelo WhatsApp
        </button>
      </div>
    </div>
  );
}

function Field({ label, children, error }) {
  return (
    <div style={styles.field}>
      <label style={styles.label}>{label}</label>
      {children}
      {error && <span style={styles.error}>{error}</span>}
    </div>
  );
}

function WhatsAppIcon() {
  return (
    <svg width="18" height="18" viewBox="0 0 24 24" fill="currentColor" style={{ marginRight: 8 }}>
      <path d="M17.472 14.382c-.297-.149-1.758-.867-2.03-.967-.273-.099-.471-.148-.67.15-.197.297-.767.966-.94 1.164-.173.199-.347.223-.644.075-.297-.15-1.255-.463-2.39-1.475-.883-.788-1.48-1.761-1.653-2.059-.173-.297-.018-.458.13-.606.134-.133.298-.347.446-.52.149-.174.198-.298.298-.497.099-.198.05-.371-.025-.52-.075-.149-.669-1.612-.916-2.207-.242-.579-.487-.5-.669-.51-.173-.008-.371-.01-.57-.01-.198 0-.52.074-.792.372-.272.297-1.04 1.016-1.04 2.479 0 1.462 1.065 2.875 1.213 3.074.149.198 2.096 3.2 5.077 4.487.709.306 1.262.489 1.694.625.712.227 1.36.195 1.871.118.571-.085 1.758-.719 2.006-1.413.248-.694.248-1.289.173-1.413-.074-.124-.272-.198-.57-.347m-5.421 7.403h-.004a9.87 9.87 0 01-5.031-1.378l-.361-.214-3.741.982.998-3.648-.235-.374a9.86 9.86 0 01-1.51-5.26c.001-5.45 4.436-9.884 9.888-9.884 2.64 0 5.122 1.03 6.988 2.898a9.825 9.825 0 012.893 6.994c-.003 5.45-4.437 9.884-9.885 9.884m8.413-18.297A11.815 11.815 0 0012.05 0C5.495 0 .16 5.335.157 11.892c0 2.096.547 4.142 1.588 5.945L.057 24l6.305-1.654a11.882 11.882 0 005.683 1.448h.005c6.554 0 11.89-5.335 11.893-11.893a11.821 11.821 0 00-3.48-8.413z" />
    </svg>
  );
}

const styles = {
  card: {
    background: "#15191e",
    borderRadius: 16,
    padding: "28px 24px 24px",
    maxWidth: 560,
    color: "#e4e4e7",
    fontFamily: "system-ui, sans-serif",
  },
  title: { fontSize: 22, fontWeight: 600, margin: "0 0 10px", color: "#f4f4f5" },
  desc: { fontSize: 14, lineHeight: 1.6, color: "#a1a1aa", margin: "0 0 24px" },
  grid: {
    display: "grid",
    gridTemplateColumns: "1fr 1fr",
    gap: "14px 16px",
    marginBottom: 24,
  },
  field: { display: "flex", flexDirection: "column", gap: 4 },
  label: { fontSize: 13, color: "#a1a1aa" },
  input: {
    background: "#1e2530",
    border: "1px solid #2e3540",
    borderRadius: 8,
    color: "#e4e4e7",
    fontSize: 14,
    padding: "10px 12px",
    outline: "none",
    width: "100%",
    boxSizing: "border-box",
  },
  select: { cursor: "pointer" },
  error: { fontSize: 12, color: "#f87171" },
  divider: {
    textAlign: "center",
    borderTop: "1px solid #2e3540",
    paddingTop: 16,
    marginBottom: 16,
  },
  dividerText: { fontSize: 13, color: "#71717a", background: "#15191e", padding: "0 12px" },
  actions: { display: "flex", gap: 12 },
  btn: {
    flex: 1,
    padding: "12px 16px",
    borderRadius: 10,
    fontSize: 14,
    fontWeight: 500,
    cursor: "pointer",
    border: "none",
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
    transition: "opacity .15s",
  },
  btnSecondary: { background: "#1e2530", color: "#71717a", opacity: 0.6, cursor: "not-allowed" },
  btnWhatsApp: { background: "#1a6334", color: "#fff" },
};
