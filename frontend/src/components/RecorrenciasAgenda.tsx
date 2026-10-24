import { useEffect, useState, type FormEvent } from "react";
import axios from "axios";
import { alterarRecorrencia, encerrarRecorrencia } from "../api";
import { erroHorario, FUSO_CLINICA, instanteDaClinica, minimoFuturoClinica } from "../agendaHorarios";
import type { Recorrencia } from "../types";

function data(iso: string) {
  return new Date(iso).toLocaleString("pt-BR", { timeZone: FUSO_CLINICA, weekday: "long",
    day: "2-digit", month: "2-digit", year: "numeric", hour: "2-digit", minute: "2-digit" });
}

export default function RecorrenciasAgenda({ regras, podeGerenciar, agora, sincronizar, atualizar, onOcupadoChange }: {
  regras: Recorrencia[]; podeGerenciar: boolean; agora: number | null;
  sincronizar: () => Promise<number>; atualizar: () => void;
  onOcupadoChange: (ocupado: boolean) => void;
}) {
  const [selecao, setSelecao] = useState<{ regra: Recorrencia; acao: "alterar" | "encerrar" } | null>(null);
  const [encerradas, setEncerradas] = useState(false);
  const [corte, setCorte] = useState("");
  const [inicio, setInicio] = useState("");
  const [frequencia, setFrequencia] = useState<7 | 14>(7);
  const [motivo, setMotivo] = useState("");
  const [salvando, setSalvando] = useState(false);
  const [erro, setErro] = useState<string | null>(null);
  const [sucesso, setSucesso] = useState<string | null>(null);
  const erroCorte = corte ? erroHorario(corte, agora) : null;
  const erroInicio = inicio ? erroHorario(inicio, agora) : null;
  useEffect(() => {
    onOcupadoChange(salvando);
    return () => onOcupadoChange(false);
  }, [salvando, onOcupadoChange]);

  function abrir(regra: Recorrencia, acao: "alterar" | "encerrar") {
    setSelecao({ regra, acao }); setCorte(""); setInicio(""); setMotivo("");
    setFrequencia(regra.intervalo_dias); setErro(null); setSucesso(null);
  }

  async function salvar(e: FormEvent) {
    e.preventDefault();
    if (!selecao || salvando || !motivo.trim()) return;
    setSalvando(true); setErro(null); setSucesso(null);
    try {
      const atual = await sincronizar();
      if (corte && erroHorario(corte, atual)) throw new Error(erroHorario(corte, atual)!);
      const aPartir = corte ? new Date(instanteDaClinica(corte)).toISOString() : null;
      if (selecao.acao === "encerrar") {
        await encerrarRecorrencia(selecao.regra.id, { a_partir_de: aPartir, motivo: motivo.trim() });
        setSucesso("Recorrência encerrada a partir da data escolhida. O histórico foi preservado.");
      } else {
        const falha = erroHorario(inicio, atual);
        if (falha) throw new Error(falha);
        if (!aPartir) throw new Error("Informe a partir de quando alterar a sequência.");
        const instante = instanteDaClinica(inicio);
        if (instante < instanteDaClinica(corte)) throw new Error("A primeira sessão deve ocorrer a partir da alteração.");
        await alterarRecorrencia(selecao.regra.id, { a_partir_de: aPartir, motivo: motivo.trim(),
          inicio: new Date(instante).toISOString(),
          fim: new Date(instante + selecao.regra.duracao_minutos * 60000).toISOString(), intervalo_dias: frequencia });
        setSucesso("Próximas sessões alteradas. A sequência anterior foi preservada no histórico.");
      }
      setSelecao(null); atualizar();
    } catch (err) {
      const detalhe = axios.isAxiosError(err) ? err.response?.data?.detail : null;
      setErro(typeof detalhe === "string" ? detalhe : err instanceof Error ? err.message : "Não foi possível salvar a recorrência.");
    } finally { setSalvando(false); }
  }

  const visiveis = regras.filter(r => encerradas || !r.encerrada_em || agora === null || new Date(r.encerrada_em).getTime() > agora);
  return <section aria-label="Gerenciar horários recorrentes">
    {!selecao && <>
      <p>Reservas semanais ou quinzenais até alteração ou encerramento. Cancelar ou reagendar uma sessão mantém as seguintes.</p>
      <label className="campo-checkbox"><input type="checkbox" checked={encerradas} onChange={e => setEncerradas(e.target.checked)} /> Mostrar encerradas</label>
    </>}
    {erro && <p className="erro" role="alert">{erro}</p>}
    {sucesso && <p role="status">{sucesso}</p>}
    {selecao && <form onSubmit={salvar} className="form-grid" style={{ margin: "1rem 0" }}>
      <p><strong>{selecao.acao === "alterar" ? "Alterar próximas sessões" : "Encerrar recorrência"}</strong> de {selecao.regra.paciente_nome}.
        {" "}As sessões agendadas ou confirmadas a partir da data escolhida serão canceladas, preservando o histórico.
        {selecao.acao === "encerrar" && " Isso encerra a reserva de horário; não registra alta clínica."}</p>
      <label htmlFor="recorrencia-corte">A partir de (Brasília)
        <input id="recorrencia-corte" type="datetime-local" value={corte} min={minimoFuturoClinica(agora)}
          required={selecao.acao === "alterar"} disabled={salvando} aria-invalid={Boolean(erroCorte)}
          aria-describedby="recorrencia-corte-ajuda" onChange={e => { setCorte(e.target.value); setErro(null); }} />
        <small id="recorrencia-corte-ajuda">{erroCorte || (selecao.acao === "encerrar" ? "Deixe vazio para encerrar agora." : "Informe a data a partir da qual substituir a sequência.")}</small>
      </label>
      {selecao.acao === "alterar" && <>
        <label htmlFor="recorrencia-inicio">Primeira sessão no novo horário (Brasília)
          <input id="recorrencia-inicio" type="datetime-local" value={inicio} min={minimoFuturoClinica(agora)} required disabled={salvando}
            aria-invalid={Boolean(erroInicio)} aria-describedby="recorrencia-inicio-ajuda"
            onChange={e => { setInicio(e.target.value); setErro(null); }} />
          <small id="recorrencia-inicio-ajuda">{erroInicio || "A partir desta data, no mesmo dia da semana e horário."}</small>
        </label>
        <label>Repetição<select value={frequencia} disabled={salvando} onChange={e => setFrequencia(Number(e.target.value) as 7 | 14)}>
          <option value={7}>Semanal</option><option value={14}>Quinzenal (a cada 14 dias)</option>
        </select></label>
      </>}
      <label>Motivo<textarea value={motivo} required maxLength={500} disabled={salvando} onChange={e => setMotivo(e.target.value)} /></label>
      <button className="btn btn-primary" type="submit" disabled={salvando || agora === null || !motivo.trim() || Boolean(erroCorte)
        || (selecao.acao === "alterar" && (!corte || !inicio || Boolean(erroInicio)))}>
        {salvando ? "Salvando…" : selecao.acao === "alterar" ? "Confirmar alteração da sequência" : "Confirmar encerramento"}
      </button>
      <button className="btn btn-secondary" type="button" disabled={salvando} onClick={() => setSelecao(null)}>Voltar</button>
    </form>}
    {!selecao && <>
    {visiveis.length === 0 ? <p>Nenhum horário recorrente nesta seleção.</p> : <div className="tabela-wrapper"><table className="tabela">
      <thead><tr><th>Paciente / profissional</th><th>Primeira sessão e repetição</th><th>Situação</th>{podeGerenciar && <th>Ações</th>}</tr></thead>
      <tbody>{visiveis.map(r => <tr key={r.id}>
        <td>{r.paciente_nome}<small style={{ display: "block" }}>{r.psicologo_nome}</small></td>
        <td>{data(r.inicio)}<small style={{ display: "block" }}>{r.intervalo_dias === 7 ? "Semanal" : "A cada 14 dias"} · {r.duracao_minutos} minutos</small></td>
        <td>{r.encerrada_em ? <>Encerramento: {data(r.encerrada_em)}<small style={{ display: "block" }}>{r.motivo_encerramento}</small></> : "Sem término definido"}</td>
        {podeGerenciar && <td className="acoes-linha">{!r.encerrada_em && <>
          <button type="button" className="btn btn-sm btn-secondary" disabled={salvando} onClick={() => abrir(r, "alterar")}>Alterar próximas sessões</button>
          <button type="button" className="btn btn-sm btn-ghost" disabled={salvando} onClick={() => abrir(r, "encerrar")}>Encerrar recorrência</button>
        </>}</td>}
      </tr>)}</tbody>
    </table></div>}
    </>}
  </section>;
}
