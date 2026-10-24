/**
 * Agenda operacional: listar, criar e alterar status (gera financeiro ao marcar realizado).
 */
import { useCallback, useEffect, useState, type FormEvent } from "react";
import axios from "axios";
import {
  createAgendamento,
  fetchAgendamentos,
  fetchPacientes,
  fetchPsicologos,
  updateAgendamento,
  reagendarAgendamento,
  criarRecorrencia,
  fetchRecorrencias,
  gerarSessoesRecorrentes,
} from "../api";
import RecorrenciasAgenda from "../components/RecorrenciasAgenda";
import Modal from "../components/Modal";
import { useAuth } from "../context/AuthContext";
import { useRelogioAgenda } from "../context/useRelogioAgenda";
import { erroHorario, FUSO_CLINICA, instanteDaClinica, minimoFuturoClinica } from "../agendaHorarios";
import type { Agendamento, Paciente, Psicologo, StatusAgendamento, Recorrencia } from "../types";

function badgeClass(status: StatusAgendamento) {
  return `badge badge-${status}`;
}

function formatarData(iso: string) {
  return new Date(iso).toLocaleString("pt-BR", {
    timeZone: FUSO_CLINICA,
    day: "2-digit",
    month: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
  });
}

function mensagemErro(err: unknown) {
  const detalhe = axios.isAxiosError(err) ? err.response?.data?.detail : null;
  return typeof detalhe === "string"
    ? detalhe
    : err instanceof Error ? err.message : "Não foi possível atualizar o atendimento.";
}

export default function Agenda() {
  const { usuario } = useAuth();
  const podeGerenciar = Boolean(usuario?.permissoes.includes("agenda:gerenciar"));
  const podeEstornar = Boolean(usuario?.permissoes.includes("financeiro:gerenciar"));
  const [agendamentos, setAgendamentos] = useState<Agendamento[]>([]);
  const [pacientes, setPacientes] = useState<Paciente[]>([]);
  const [psicologos, setPsicologos] = useState<Psicologo[]>([]);
  const [psicologoFiltro, setPsicologoFiltro] = useState<number | "">("");
  const [mostrarForm, setMostrarForm] = useState(false);
  const [erro, setErro] = useState<string | null>(null);

  const [pacienteId, setPacienteId] = useState<number>(0);
  const [psicologoId, setPsicologoId] = useState<number>(0);
  const [dataHora, setDataHora] = useState("");
  const [repeticao, setRepeticao] = useState<0 | 7 | 14>(0);
  const [recorrencias, setRecorrencias] = useState<Recorrencia[]>([]);
  const [mostrarRecorrencias, setMostrarRecorrencias] = useState(false);
  const [salvandoRecorrencia, setSalvandoRecorrencia] = useState(false);
  const [sucesso, setSucesso] = useState<string | null>(null);
  const [cancelamento, setCancelamento] = useState<Agendamento | null>(null);
  const [motivoCancelamento, setMotivoCancelamento] = useState("");
  const [salvando, setSalvando] = useState(false);
  const { agora, erro: erroRelogio, sincronizar: sincronizarRelogio } = useRelogioAgenda();
  const [reagendamento, setReagendamento] = useState<Agendamento | null>(null);
  const [novaDataHora, setNovaDataHora] = useState("");
  const [dataHoraTocada, setDataHoraTocada] = useState(false);
  const [novaDataHoraTocada, setNovaDataHoraTocada] = useState(false);
  const minimoFuturo = minimoFuturoClinica(agora);
  const erroNovaReserva = dataHora || dataHoraTocada ? erroHorario(dataHora, agora) : null;
  const erroReagendamento = novaDataHora || novaDataHoraTocada ? erroHorario(novaDataHora, agora) : null;

  const psicologosAtivos = psicologos.filter((p) => p.ativo && (usuario?.perfil !== "psicologo" || p.id === usuario.psicologo_id));
  const psicologosDoFiltro = psicologos.filter((p) => usuario?.perfil !== "psicologo" || p.id === usuario.psicologo_id);
  const dadosProntos = pacientes.some((p) => p.id === pacienteId && p.ativo)
    && psicologosAtivos.some((p) => p.id === psicologoId);

  const carregar = useCallback(() => {
    const params: { psicologo_id?: number } = {};
    if (psicologoFiltro) params.psicologo_id = psicologoFiltro;
    void (async () => {
      if (podeGerenciar) {
        try { await gerarSessoesRecorrentes(); }
        catch (err) { setErro(`Não foi possível atualizar as próximas sessões recorrentes. ${mensagemErro(err)}`); }
      }
      try {
        const [agenda, regras] = await Promise.all([fetchAgendamentos(params), fetchRecorrencias()]);
        setAgendamentos(agenda); setRecorrencias(regras);
      } catch { setErro("Erro ao carregar agenda e recorrências."); }
    })();
  }, [psicologoFiltro, podeGerenciar]);

  useEffect(() => {
    if (!podeGerenciar) return;
    Promise.all([fetchPacientes(), fetchPsicologos()])
      .then(([pacs, psis]) => {
        const pacientesAtivos = pacs.filter((p) => p.ativo);
        setPacientes(pacientesAtivos);
        setPsicologos(psis);
        setPacienteId(pacientesAtivos[0]?.id ?? 0);
        setPsicologoId(psis.find((p) => p.ativo && (usuario?.perfil !== "psicologo" || p.id === usuario.psicologo_id))?.id ?? 0);
      })
      .catch(() => setErro("Erro ao carregar cadastros auxiliares."));
  }, [podeGerenciar, usuario?.perfil, usuario?.psicologo_id]);

  useEffect(() => {
    carregar();
  }, [carregar]);

  async function handleNovo(e: FormEvent) {
    e.preventDefault();
    if (!dataHora || !dadosProntos || salvando) return;
    setSalvando(true);
    setErro(null);
    setSucesso(null);
    try {
      const atual = await sincronizarRelogio();
      const erroData = erroHorario(dataHora, atual);
      if (erroData) { setErro(erroData); return; }
      const inicio = new Date(instanteDaClinica(dataHora));
      const fim = new Date(inicio.getTime() + 50 * 60 * 1000);
      const reserva = {
        paciente_id: pacienteId,
        psicologo_id: psicologoId,
        inicio: inicio.toISOString(),
        fim: fim.toISOString(),
      };
      if (repeticao) await criarRecorrencia({ ...reserva, intervalo_dias: repeticao });
      else await createAgendamento({ ...reserva, status: "agendado" });
      setMostrarForm(false);
      setDataHora("");
      setDataHoraTocada(false);
      setSucesso(repeticao ? "Recorrência criada. O horário está reservado até alteração ou encerramento; as próximas sessões já estão na agenda."
        : "Agendamento criado com sucesso.");
      setRepeticao(0);
      carregar();
    } catch (err) {
      setErro(mensagemErro(err));
    } finally {
      setSalvando(false);
    }
  }

  async function mudarStatus(id: number, status: StatusAgendamento) {
    if (salvando) return;
    setSalvando(true);
    setErro(null);
    setSucesso(null);
    try {
      await updateAgendamento(id, { status });
      setSucesso(`Status atualizado para "${status}".`);
      carregar();
    } catch (err) {
      setErro(mensagemErro(err));
    } finally {
      setSalvando(false);
    }
  }

  async function cancelarRealizado(e: FormEvent) {
    e.preventDefault();
    if (!cancelamento || !motivoCancelamento.trim() || salvando) return;
    setSalvando(true);
    setErro(null);
    setSucesso(null);
    try {
      await updateAgendamento(cancelamento.id, {
        status: "cancelado", motivo_cancelamento: motivoCancelamento.trim(),
      });
      setCancelamento(null);
      setMotivoCancelamento("");
      setSucesso("Atendimento cancelado. Receita e repasse foram estornados; os lançamentos originais foram preservados.");
      carregar();
    } catch (err) {
      setErro(mensagemErro(err));
    } finally {
      setSalvando(false);
    }
  }

  async function confirmarReagendamento(e: FormEvent) {
    e.preventDefault();
    if (!reagendamento || salvando) return;
    setSalvando(true);
    setErro(null);
    setSucesso(null);
    try {
      const atual = await sincronizarRelogio();
      const erroData = erroHorario(novaDataHora, atual);
      if (erroData) { setErro(erroData); return; }
      const inicio = new Date(instanteDaClinica(novaDataHora));
      const duracaoAnterior = new Date(reagendamento.fim).getTime() - new Date(reagendamento.inicio).getTime();
      const duracao = Number.isFinite(duracaoAnterior) && duracaoAnterior > 0 ? duracaoAnterior : 50 * 60000;
      const fim = new Date(inicio.getTime() + duracao);
      await reagendarAgendamento(reagendamento.id, inicio.toISOString(), fim.toISOString());
      setReagendamento(null);
      setNovaDataHora("");
      setNovaDataHoraTocada(false);
      setSucesso("Novo agendamento criado. O registro anterior foi preservado no histórico.");
      carregar();
    } catch (err) {
      setErro(mensagemErro(err));
    } finally {
      setSalvando(false);
    }
  }

  return (
    <>
      <header className="page-header">
        <h2>Agenda</h2>
        <p>Marque como <strong>realizado</strong> para gerar receita e repasse automaticos.</p>
      </header>
      <p aria-live="off">
        {agora !== null ? `Horário de Brasília: ${new Date(agora).toLocaleString("pt-BR", { timeZone: FUSO_CLINICA })}.` : "Atualizando horário atual…"}
      </p>
      {erroRelogio && <p className="erro" role="alert">{erroRelogio}{" "}
        <button type="button" className="btn btn-sm btn-secondary" onClick={() => { void sincronizarRelogio().catch(() => {}); }}>
          Atualizar horário
        </button>
      </p>}
      {erro && <p className="erro">{erro}</p>}
      {sucesso && <p style={{ color: "var(--cor-sucesso)", fontSize: "0.9rem" }}>{sucesso}</p>}
      {mostrarRecorrencias && <Modal titulo="Horários recorrentes" amplo ocupado={salvandoRecorrencia}
        onFechar={() => setMostrarRecorrencias(false)}>
        <RecorrenciasAgenda regras={recorrencias.filter(r => !psicologoFiltro || r.psicologo_id === psicologoFiltro)}
          podeGerenciar={podeGerenciar} agora={agora} sincronizar={sincronizarRelogio} atualizar={carregar}
          onOcupadoChange={setSalvandoRecorrencia} />
      </Modal>}
      {reagendamento && podeGerenciar && (
        <Modal titulo="Reagendar atendimento" ocupado={salvando} onFechar={() => { setReagendamento(null); setErro(null); }}>
        <form onSubmit={confirmarReagendamento} className="form-grid">
          {erro && <p className="erro" role="alert">{erro}</p>}
          <p>Reagendar <strong>{reagendamento.paciente_nome}</strong>, com {reagendamento.psicologo_nome}.
            {" "}Será criado um novo agendamento; o registro de {formatarData(reagendamento.inicio)} ficará preservado.
            {reagendamento.recorrencia_id && " Esta mudança afeta somente esta sessão; as seguintes mantêm o horário recorrente."}</p>
          <label htmlFor="nova-data-reagendamento">Nova data e hora
            <input id="nova-data-reagendamento" type="datetime-local" min={minimoFuturo} required
              aria-invalid={Boolean(erroReagendamento)}
              aria-describedby={erroReagendamento ? "reagendamento-horario-ajuda reagendamento-horario-erro" : "reagendamento-horario-ajuda"}
              value={novaDataHora} onChange={(e) => {
                setNovaDataHora(e.target.value); setNovaDataHoraTocada(true); setErro(null); setSucesso(null);
              }} onBlur={() => setNovaDataHoraTocada(true)} disabled={salvando} />
            <small id="reagendamento-horario-ajuda">Horário de Brasília. Selecione uma data e hora futuras.</small>
            {erroReagendamento && <small id="reagendamento-horario-erro" className="erro" role="alert">{erroReagendamento}</small>}
          </label>
          <button type="submit" className="btn btn-primary"
            disabled={salvando || agora === null || Boolean(erroHorario(novaDataHora, agora))}>
            {salvando ? "Salvando..." : "Confirmar reagendamento"}
          </button>
          <button type="button" className="btn btn-secondary" disabled={salvando}
            onClick={() => { setReagendamento(null); setNovaDataHora(""); }}>Voltar</button>
        </form>
        </Modal>
      )}
      {cancelamento && podeGerenciar && podeEstornar && (
        <Modal titulo="Cancelar e estornar" ocupado={salvando} onFechar={() => { setCancelamento(null); setErro(null); }}>
        <form onSubmit={cancelarRealizado} className="form-grid">
          {erro && <p className="erro" role="alert">{erro}</p>}
          <p>
            Cancelar o atendimento de <strong>{cancelamento.paciente_nome}</strong> em {formatarData(cancelamento.inicio)}?
            {" "}A receita e o repasse serão estornados. O agendamento não poderá ser reaberto.
            {" "}Atendimentos com evolução clínica não podem ser cancelados por este fluxo.
          </p>
          <label htmlFor="motivo-cancelamento" translate="no">
            Motivo do cancelamento
            <textarea id="motivo-cancelamento" required maxLength={500} value={motivoCancelamento}
              onChange={(e) => setMotivoCancelamento(e.target.value)} disabled={salvando} />
          </label>
          <button type="submit" className="btn btn-primary" disabled={salvando || !motivoCancelamento.trim()}>
            {salvando ? "Salvando..." : "Confirmar cancelamento e estorno"}
          </button>
          <button type="button" className="btn btn-secondary" disabled={salvando}
            onClick={() => { setCancelamento(null); setMotivoCancelamento(""); }}>
            Voltar
          </button>
        </form>
        </Modal>
      )}
      <div className="filtros">
        {psicologosDoFiltro.length > 0 && (
          <label>
            Filtrar psicologo
            <select
              value={psicologoFiltro}
              onChange={(e) =>
                setPsicologoFiltro(e.target.value ? Number(e.target.value) : "")
              }
            >
              <option value="">Todos</option>
              {psicologosDoFiltro.map((p) => (
                <option key={p.id} value={p.id}>
                  {p.nome}
                </option>
              ))}
            </select>
          </label>
        )}
        {podeGerenciar && (
          <button type="button" className="btn btn-primary" disabled={salvando} onClick={() => {
            setMostrarForm(!mostrarForm); setReagendamento(null); setCancelamento(null);
          }}>
            {mostrarForm ? "Cancelar" : "Novo agendamento"}
          </button>
        )}
        <button type="button" className="btn btn-secondary" onClick={() => setMostrarRecorrencias(true)}>
          Horários recorrentes
        </button>
      </div>
      {mostrarForm && podeGerenciar && (
        <Modal titulo="Novo agendamento" ocupado={salvando} onFechar={() => { setMostrarForm(false); setErro(null); }}>
        <form onSubmit={handleNovo} className="form-grid">
          {erro && <p className="erro" role="alert">{erro}</p>}
          {!dadosProntos && <p role="status">Cadastre ou reative um paciente e um profissional para agendar.</p>}
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
              {psicologosAtivos.map((p) => (
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
              id="novo-horario"
              min={minimoFuturo}
              required
              value={dataHora}
              aria-invalid={Boolean(erroNovaReserva)}
              aria-describedby={erroNovaReserva ? "novo-horario-ajuda novo-horario-erro" : "novo-horario-ajuda"}
              onChange={(e) => { setDataHora(e.target.value); setDataHoraTocada(true); setErro(null); setSucesso(null); }}
              onBlur={() => setDataHoraTocada(true)}
            />
            <small id="novo-horario-ajuda">Horário de Brasília. Selecione uma data e hora futuras.</small>
            {erroNovaReserva && <small id="novo-horario-erro" className="erro" role="alert">{erroNovaReserva}</small>}
          </label>
          <label>Repetição
            <select value={repeticao} disabled={salvando} onChange={e => setRepeticao(Number(e.target.value) as 0 | 7 | 14)}>
              <option value={0}>Não repetir</option><option value={7}>Semanal</option><option value={14}>Quinzenal (a cada 14 dias)</option>
            </select>
            {repeticao !== 0 && <small>Mesmo dia da semana e horário de Brasília, até alterar ou encerrar a recorrência. Cada sessão terá 50 minutos.</small>}
          </label>
          <button type="submit" className="btn btn-primary" disabled={!dadosProntos || salvando || agora === null || Boolean(erroHorario(dataHora, agora))}>
            {salvando ? "Salvando..." : repeticao ? "Agendar sequência" : "Agendar"}
          </button>
        </form>
        </Modal>
      )}
      {recorrencias.length > 0 && <p>As sessões recorrentes são atualizadas para os próximos 90 dias ao abrir ou atualizar a agenda.
        {" "}A reserva do horário continua além desse período, até o encerramento.
        {podeGerenciar && <button className="btn btn-sm btn-secondary" type="button" disabled={salvando} onClick={carregar}>Atualizar agenda</button>}</p>}
      <div className="tabela-wrapper">
      <table className="tabela">
        <thead>
          <tr>
            <th>Data</th>
            <th>Paciente</th>
            <th>Psicologo</th>
            <th>Status</th>
            {podeGerenciar && <th>Ações</th>}
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
                {a.reagendado_para_id && <small style={{ display: "block" }}>Reagendado</small>}
                {a.recorrencia_id && <small style={{ display: "block" }}>Sessão recorrente</small>}
              </td>
              {podeGerenciar && <td className="acoes-linha">
                {a.status === "agendado" && agora !== null && new Date(a.inicio).getTime() > agora && (
                  <button
                    type="button"
                    className="btn btn-sm btn-secondary"
                    disabled={salvando}
                    onClick={() => mudarStatus(a.id, "confirmado")}
                  >
                    Confirmar
                  </button>
                )}
                {(a.status === "agendado" || a.status === "confirmado") && (
                  <button
                    type="button"
                    className="btn btn-sm btn-primary"
                    disabled={salvando}
                    onClick={() => mudarStatus(a.id, "realizado")}
                  >
                    Realizado
                  </button>
                )}
                {(a.status === "agendado" || a.status === "confirmado") && (
                  <button type="button" className="btn btn-sm btn-secondary" disabled={salvando}
                    onClick={() => mudarStatus(a.id, "falta")}>
                    Falta
                  </button>
                )}
                {a.pode_reabrir && agora !== null && new Date(a.inicio).getTime() > agora && (
                  <button type="button" className="btn btn-sm btn-secondary" disabled={salvando}
                    onClick={() => mudarStatus(a.id, "agendado")}>
                    Reabrir como agendado
                  </button>
                )}
                {a.pode_reagendar && (
                  <button type="button" className="btn btn-sm btn-secondary" disabled={salvando}
                    onClick={() => {
                      setReagendamento(a); setNovaDataHora(""); setNovaDataHoraTocada(false); setMostrarForm(false);
                      setCancelamento(null); setErro(null); setSucesso(null);
                    }}>Reagendar</button>
                )}
                {a.status === "realizado" && podeEstornar && (
                  <button type="button" className="btn btn-sm btn-ghost" disabled={salvando}
                    onClick={() => {
                      setCancelamento(a); setReagendamento(null); setMostrarForm(false);
                      setMotivoCancelamento(""); setErro(null); setSucesso(null);
                    }}>
                    Cancelar e estornar
                  </button>
                )}
                {(a.status === "agendado" || a.status === "confirmado") && (
                  <button
                    type="button"
                    className="btn btn-sm btn-ghost"
                    disabled={salvando}
                    onClick={() => mudarStatus(a.id, "cancelado")}
                  >
                    {a.recorrencia_id ? "Cancelar só esta sessão" : "Anular"}
                  </button>
                )}
              </td>}
            </tr>
          ))}
        </tbody>
      </table>
      </div>
    </>
  );
}
