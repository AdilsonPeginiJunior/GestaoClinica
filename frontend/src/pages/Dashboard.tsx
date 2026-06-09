/**
 * Painel inicial — indicadores variam conforme perfil (filtro feito na API).
 */
import { useEffect, useState } from "react";
import { fetchDashboard } from "../api";
import { useAuth } from "../context/AuthContext";
import type { DashboardStats } from "../types";

export default function Dashboard() {
  const { usuario } = useAuth();
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [erro, setErro] = useState<string | null>(null);

  useEffect(() => {
    fetchDashboard()
      .then(setStats)
      .catch(() => setErro("Nao foi possivel carregar o dashboard."));
  }, []);

  const formatMoeda = (v: number) =>
    v.toLocaleString("pt-BR", { style: "currency", currency: "BRL" });

  return (
    <>
      <header className="page-header">
        <h2>Dashboard</h2>
        <p>
          Olá, {usuario?.nome}. Visão{" "}
          {usuario?.perfil === "psicologo" ? "do seu consultório" : "da clínica"}.
        </p>
      </header>
      {erro && <p className="erro">{erro}</p>}
      {stats && (
        <div className="grid-stats">
          <div className="card">
            <div className="valor">{stats.agendamentos_hoje}</div>
            <div className="rotulo">Agendamentos hoje</div>
          </div>
          <div className="card">
            <div className="valor">{stats.total_pacientes}</div>
            <div className="rotulo">Pacientes ativos</div>
          </div>
          <div className="card">
            <div className="valor">{stats.agendamentos_realizados}</div>
            <div className="rotulo">Consultas realizadas</div>
          </div>
          <div className="card">
            <div className="valor">{formatMoeda(stats.receita_periodo)}</div>
            <div className="rotulo">Receita no mês</div>
          </div>
          <div className="card">
            <div className="valor">{formatMoeda(stats.repasse_periodo)}</div>
            <div className="rotulo">Repasse no mês</div>
          </div>
        </div>
      )}
      <div className="card">
        <h3 style={{ marginTop: 0 }}>Roteiro para demonstração ao cliente</h3>
        <ol style={{ margin: 0, paddingLeft: "1.2rem", color: "var(--cor-texto-suave)" }}>
          <li>Cadastre ou busque um paciente em Pacientes.</li>
          <li>Agende horario em Agenda e marque como realizada.</li>
          <li>Confira lancamentos automaticos em Relatorios (perfil socia/admin).</li>
          <li>Troque de perfil pelo login rapido para mostrar restricoes de acesso.</li>
        </ol>
      </div>
    </>
  );
}
