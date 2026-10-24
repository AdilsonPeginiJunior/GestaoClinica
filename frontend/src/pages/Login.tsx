/**
 * Tela de login com atalhos para usuários de demonstração.
 */
import { useState, type FormEvent } from "react";
import { Navigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import { useAmbiente } from "../context/useAmbiente";
import type { DemoUser } from "../types";

const USUARIOS_DEMO: DemoUser[] = [
  { label: "Recepção", email: "recepcao@demo.com", password: "demo123", perfil: "recepcionista" },
  { label: "Psicólogo (Dra. Ana)", email: "psicologo@demo.com", password: "demo123", perfil: "psicologo" },
  { label: "Sócia administradora", email: "socia@demo.com", password: "demo123", perfil: "socia" },
  { label: "Administrador", email: "admin@demo.com", password: "demo123", perfil: "admin" },
];

export default function Login() {
  const { usuario, login, carregando } = useAuth();
  const ambiente = useAmbiente();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [erro, setErro] = useState<string | null>(null);
  const [enviando, setEnviando] = useState(false);

  if (!carregando && usuario) {
    return <Navigate to="/" replace />;
  }

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setErro(null);
    setEnviando(true);
    try {
      await login(email, password);
    } catch (err) {
      setErro(err instanceof Error ? err.message : "Nao foi possivel entrar. Verifique e-mail e senha.");
    } finally {
      setEnviando(false);
    }
  }

  async function entrarComo(demo: DemoUser) {
    setEmail(demo.email);
    setPassword(demo.password);
    setErro(null);
    setEnviando(true);
    try {
      await login(demo.email, demo.password);
    } catch (err) {
      setErro(err instanceof Error ? err.message : "API indisponivel. Inicie o backend na porta 8000.");
    } finally {
      setEnviando(false);
    }
  }

  return (
    <div className="login-page">
      <div className="login-card">
        <h1>Gestão Clínica</h1>
        <p style={{ color: "var(--cor-texto-suave)", marginBottom: "1.25rem" }}>
          {ambiente?.ambiente === "demo" ? "Demonstração — dados fictícios" : "Acesso ao sistema"}
        </p>
        <form onSubmit={handleSubmit} className="form-grid">
          <label>
            E-mail
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
              autoComplete="username"
            />
          </label>
          <label>
            Senha
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
              autoComplete="current-password"
            />
          </label>
          {erro && <p className="erro">{erro}</p>}
          <button type="submit" className="btn btn-primary" disabled={enviando}>
            {enviando ? "Entrando…" : "Entrar"}
          </button>
        </form>
        {ambiente?.ambiente === "demo" && ambiente.demo_habilitada === true && <>
        <p style={{ marginTop: "1.25rem", fontSize: "0.85rem", fontWeight: 600 }}>Acesso rápido (demo)</p>
        <div className="demo-users">
          {USUARIOS_DEMO.map((u) => (
            <button key={u.email} type="button" onClick={() => entrarComo(u)} disabled={enviando}>
              {u.label} — {u.email}
            </button>
          ))}
        </div>
        </>}
      </div>
    </div>
  );
}
