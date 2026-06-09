/**
 * Agenda operacional: listar, criar e alterar status (gera financeiro ao marcar realizado).
 */
import { useEffect, useState, type FormEvent } from "react";
import {
  createAgendamento,
  fetchAgendamentos,
  fetchPacientes,
  fetchPsicologos,
  updateAgendamento,
} from "../api";
import type { Agendamento, Paciente, Psicologo, StatusAgendamento } from "../types";

function badgeClass(status: StatusAgendamento) {
  return `badge badge-${status}`;
}

function formatarData(iso: string) {
  return new Date(iso).toLocaleString("pt-BR", {
    day: "2-digit",
    month: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
  });
}

export default function Agenda() {
  const [agendamentos, setAgendamentos] = useState<Agendamento[]>([]);
  const [pacientes, setPacientes] = useState<Paciente[]>([]);
  const [psicologos, setPsicologos] = useState<Psicologo[]>([]);
  const [psicologoFiltro, setPsicologoFiltro] = useState<number | "">("");
  const [mostrarForm, setMostrarForm] = useState(false);
  const [erro, setErro] = useState<string | null>(null);

  const [pacienteId, setPacienteId] = useState<number>(0);
  const [psicologoId, setPsicologoId] = useState<number>(0);
  const [dataHora, setDataHora] = useState("");
  const [sucesso, setSucesso] = useState<string | null>(null);

  const dadosProntos = pacientes.length > 0 && psicologos.length > 0 && pacienteId > 0 && psicologoId > 0;

  function carregar() {
    const params: { psicologo_id?: number } = {};
    if (psicologoFiltro) params.psicologo_id = psicologoFiltro;
    fetchAgendamentos(params)
      .then(setAgendamentos)
      .catch(() => setErro("Erro ao carregar agenda."));
  }

  useEffect(() => {
    Promise.all([fetchPacientes(), fetchPsicologos()])
      .then(([pacs, psis]) => {
        setPacientes(pacs);
        setPsicologos(psis);
        if (pacs[0]) setPacienteId(pacs[0].id);
        if (psis[0]) setPsicologoId(psis[0].id);
      })
      .catch(() => setErro("Erro ao carregar cadastros auxiliares."));
    carregar();
  }, []);

  useEffect(() => {
    carregar();
  }, [psicologoFiltro]);

  async function handleNovo(e: FormEvent) {
    e.preventDefault();
    if (!dataHora || !dadosProntos) return;
    // datetime-local vem sem fuso; montamos Date local e enviamos ISO para a API
    const inicio = new Date(dataHora);
    const fim = new Date(inicio.getTime() + 50 * 60 * 1000);
    setErro(null);
    setSucesso(null);
    try {
      await createAgendamento({
        paciente_id: pacienteId,
        psicologo_id: psicologoId,
        inicio: inicio.toISOString(),
        fim: fim.toISOString(),
        status: "agendado",
      });
      setMostrarForm(false);
      setDataHora("");
      setSucesso("Agendamento criado com sucesso.");
      carregar();
    } catch (err) {
      const msg = err instanceof Error ? err.message : "Nao foi possivel criar agendamento.";
      setErro(msg);
    }
  }

  async function mudarStatus(id: number, status: StatusAgendamento) {
    setErro(null);
    setSucesso(null);
    try {
      await updateAgendamento(id, { status });
      setSucesso(`Status atualizado para "${status}".`);
      carregar();
    } catch (err) {
      const msg = err instanceof Error ? err.message : "Nao foi possivel atualizar status.";
      setErro(msg);
    }
  }

  return (
    <>
      <header className="page-header">
        <h2>Agenda</h2>
        <p>Marque como <strong>realizado</strong> para gerar receita e repasse automaticos.</p>
      </header>
      {erro && <p className="erro">{erro}</p>}
      {sucesso && <p style={{ color: "var(--cor-sucesso)", fontSize: "0.9rem" }}>{sucesso}</p>}
      <div className="filtros">
        <label>
          Filtrar psicologo
          <select
            value={psicologoFiltro}
            onChange={(e) =>
              setPsicologoFiltro(e.target.value ? Number(e.target.value) : "")
            }
          >
            <option value="">Todos</option>
            {psicologos.map((p) => (
              <option key={p.id} value={p.id}>
                {p.nome}
              </option>
            ))}
          </select>
        </label>
        <button type="button" className="btn btn-primary" onClick={() => setMostrarForm(!mostrarForm)}>
          {mostrarForm ? "Cancelar" : "Novo agendamento"}
        </button>
      </div>
      {mostrarForm && (
        <form onSubmit={handleNovo} className="card form-grid" style={{ marginBottom: "1rem" }}>
          <label>
            Paciente
            <select value={pacienteId} onChange={(e) => setPacienteId(Number(e.target.value))}>
              {pacientes.map((p) => (
                <option key={p.id} value={p.id}>
                  {p.nome}
                </option>
              ))}
            </select>
          </label>
          <label>
            Psicologo
            <select value={psicologoId} onChange={(e) => setPsicologoId(Number(e.target.value))}>
              {psicologos.map((p) => (
                <option key={p.id} value={p.id}>
                  {p.nome}
                </option>
              ))}
            </select>
          </label>
          <label>
            Data e hora
            <input
              type="datetime-local"
              required
              value={dataHora}
              onChange={(e) => setDataHora(e.target.value)}
            />
          </label>
          <button type="submit" className="btn btn-primary" disabled={!dadosProntos}>
            Agendar
          </button>
        </form>
      )}
      <div className="tabela-wrapper">
      <table className="tabela">
        <thead>
          <tr>
            <th>Data</th>
            <th>Paciente</th>
            <th>Psicologo</th>
            <th>Status</th>
            <th>Acoes</th>
          </tr>
        </thead>
        <tbody>
          {agendamentos.map((a) => (
            <tr key={a.id}>
              <td>{formatarData(a.inicio)}</td>
              <td>{a.paciente_nome}</td>
              <td>{a.psicologo_nome}</td>
              <td>
                <span className={badgeClass(a.status)}>{a.status}</span>
              </td>
              <td className="acoes-linha">
                {a.status !== "confirmado" && a.status !== "realizado" && (
                  <button
                    type="button"
                    className="btn btn-sm btn-secondary"
                    onClick={() => mudarStatus(a.id, "confirmado")}
                  >
                    Confirmar
                  </button>
                )}
                {a.status !== "realizado" && (
                  <button
                    type="button"
                    className="btn btn-sm btn-primary"
                    onClick={() => mudarStatus(a.id, "realizado")}
                  >
                    Realizado
                  </button>
                )}
                {a.status !== "cancelado" && a.status !== "realizado" && (
                  <button
                    type="button"
                    className="btn btn-sm btn-ghost"
                    onClick={() => mudarStatus(a.id, "cancelado")}
                  >
                    Anular
                  </button>
                )}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
      </div>
    </>
  );
}
