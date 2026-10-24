/** Fixture local de interação: API inteiramente simulada, sem banco/contas reais. */
import React from "react";
import { createRoot } from "react-dom/client";
import { MemoryRouter } from "react-router-dom";
import { api } from "../src/api";
import { AuthProvider } from "../src/context/AuthContext";
import Agenda from "../src/pages/Agenda";
import Login from "../src/pages/Login";
import Pacientes from "../src/pages/Pacientes";
import { dataHoraClinica } from "../src/agendaHorarios";
import "../src/index.css";

const inicio = Date.now() + 7 * 86400000;
const parametros = new URLSearchParams(window.location.search);
const telaLogin = parametros.get("tela") === "login";
const regra = { id: 1, paciente_id: 1, psicologo_id: 1, paciente_nome: "Paciente fictício",
  psicologo_nome: "Profissional de teste", inicio: new Date(inicio).toISOString(), duracao_minutos: 50,
  intervalo_dias: 7, encerrada_em: null, motivo_encerramento: null, anterior_id: null };
const agendamento = { id: 1, paciente_id: 1, psicologo_id: 1, inicio: regra.inicio,
  fim: new Date(inicio + 50 * 60000).toISOString(), status: "agendado", observacoes: null,
  criado_em: new Date().toISOString(), paciente_nome: regra.paciente_nome, psicologo_nome: regra.psicologo_nome,
  possui_historico_financeiro: false, pode_reabrir: false, pode_reagendar: true,
  reagendado_de_id: null, reagendado_para_id: null, recorrencia_id: 1 };
const teste = window as typeof window & { __resolver?: () => void; __salvando?: boolean;
  __futuro?: string; __passado?: string; __gravacoes?: string[] };
teste.__futuro = dataHoraClinica(inicio + 86400000);
teste.__passado = dataHoraClinica(Date.now() - 3600000);
teste.__gravacoes = [];
if (telaLogin) localStorage.removeItem("gestao_clinica_token");
else localStorage.setItem("gestao_clinica_token", "fixture-sem-acesso-real");
api.defaults.adapter = async config => {
  const responder = (data: unknown) => ({ data, status: 200, statusText: "OK", headers: {}, config });
  const url = config.url;
  if (url === "/config/publico") {
    const controle = window as typeof window & { __configConsultada?: boolean; __resolverConfig?: () => void };
    controle.__configConsultada = true;
    const modo = parametros.get("ambiente") || "demo";
    if (modo === "erro") throw new Error("Falha simulada de configuração");
    if (modo === "malformado") return responder({ ambiente: "invalido", demo_habilitada: true });
    if (modo === "inconsistente") return responder({ ambiente: "production", demo_habilitada: true });
    if (modo === "aguardando") await new Promise<void>(resolve => { controle.__resolverConfig = resolve; });
    return responder({ ambiente: modo === "production" ? "production" : "demo",
      demo_habilitada: modo !== "production" && parametros.get("seed") !== "false" });
  }
  if (url === "/auth/me") return responder({ id: 1, perfil: parametros.get("perfil") || "admin", nome: "Teste",
    psicologo_id: parametros.get("perfil") === "psicologo" ? 1 : null,
    permissoes: ["agenda:consultar", "agenda:gerenciar", "financeiro:gerenciar", "pacientes:consultar", "pacientes:gerenciar"] });
  if (url === "/agendamentos/relogio") return responder({ agora: new Date().toISOString(), fuso_horario: "America/Sao_Paulo" });
  if (url === "/recorrencias/gerar") return responder({ sessoes_criadas: 0 });
  if (url === "/pacientes") return responder([{ id: 1, nome: regra.paciente_nome, ativo: true }]);
  if (url === "/psicologos") return responder([{ id: 1, nome: regra.psicologo_nome, ativo: true },
    { id: 2, nome: "Outro profissional fictício", ativo: true }]);
  if (url === "/agendamentos" && config.method === "get") return responder([agendamento,
    { ...agendamento, id: 2, status: "realizado", possui_historico_financeiro: true, pode_reagendar: false }]);
  if (url === "/recorrencias" && config.method === "get") return responder([regra,
    { ...regra, id: 2, encerrada_em: new Date(Date.now() - 86400000).toISOString(), motivo_encerramento: "Teste encerrado" }]);
  if (url === "/agendamentos/1/reagendar") {
    teste.__gravacoes!.push(url);
    teste.__salvando = true;
    await new Promise<void>(resolve => { teste.__resolver = resolve; });
    teste.__salvando = false;
    return responder({ ...agendamento, id: 3 });
  }
  throw new Error(`Requisição inesperada no teste: ${config.method} ${url}`);
};

createRoot(document.getElementById("root")!).render(<React.StrictMode><MemoryRouter><AuthProvider>
  {telaLogin ? <Login /> : <main className="conteudo">{parametros.get("tela") === "pacientes" ? <Pacientes /> : <Agenda />}</main>}
</AuthProvider></MemoryRouter></React.StrictMode>);
