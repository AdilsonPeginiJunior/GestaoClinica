import { useCallback, useEffect, useState, type FormEvent } from "react";
import axios from "axios";
import { useAuth } from "../context/AuthContext";
import {
  createProntuario,
  fetchAtendimentosSemEvolucao,
  fetchProntuarios,
} from "../api";
import type { Agendamento, Prontuario as Evolucao } from "../types";

function dataHora(value: string) {
  return new Date(value).toLocaleString("pt-BR", {
    dateStyle: "short",
    timeStyle: "short",
  });
}

function mensagemErro(error: unknown, fallback: string): string {
  if (axios.isAxiosError(error) && error.response?.data?.detail) {
    return String(error.response.data.detail);
  }
  return error instanceof Error ? error.message : fallback;
}

export default function Prontuario() {
  const { usuario } = useAuth();
  const podeLer = Boolean(
    usuario?.permissoes.some((item) =>
      ["prontuario:ler_proprio", "prontuario:ler_todos"].includes(item),
    ),
  );
  const podeCriar = Boolean(usuario?.permissoes.includes("prontuario:criar"));
  const [evolucoes, setEvolucoes] = useState<Evolucao[]>([]);
  const [atendimentos, setAtendimentos] = useState<Agendamento[]>([]);
  const [agendamentoId, setAgendamentoId] = useState("");
  const [evolucao, setEvolucao] = useState("");
  const [erro, setErro] = useState<string | null>(null);
  const [sucesso, setSucesso] = useState<string | null>(null);
  const [salvando, setSalvando] = useState(false);

  const carregar = useCallback(async () => {
    const [registros, disponiveis] = await Promise.all([
      podeLer ? fetchProntuarios() : Promise.resolve([]),
      podeCriar ? fetchAtendimentosSemEvolucao() : Promise.resolve([]),
    ]);
    setEvolucoes(registros);
    setAtendimentos(disponiveis);
    setAgendamentoId((atual) =>
      disponiveis.some((item) => String(item.id) === atual)
        ? atual
        : disponiveis[0] ? String(disponiveis[0].id) : "",
    );
  }, [podeCriar, podeLer]);

  useEffect(() => {
    carregar().catch((error: unknown) => {
      setErro(mensagemErro(error, "Nao foi possivel carregar o prontuario."));
    });
  }, [carregar]);

  async function salvar(event: FormEvent) {
    event.preventDefault();
    if (!agendamentoId) return;
    setErro(null);
    setSucesso(null);
    setSalvando(true);
    try {
      await createProntuario({
        agendamento_id: Number(agendamentoId),
        evolucao: evolucao.trim(),
      });
      setEvolucao("");
      await carregar();
      setSucesso("Evolucao registrada.");
    } catch (error) {
      setErro(mensagemErro(error, "Nao foi possivel registrar a evolucao."));
    } finally {
      setSalvando(false);
    }
  }

  return (
    <>
      <header className="page-header">
        <h2>Prontuario eletronico</h2>
        <p>Registros clinicos vinculados a atendimentos realizados.</p>
      </header>
      <p className="aviso-clinico">
        Prototipo inicial: utilize somente dados ficticios. As evolucoes registradas nao podem ser editadas ou excluidas.
      </p>
      {erro && <p className="erro">{erro}</p>}
      {sucesso && <p style={{ color: "var(--cor-sucesso)" }}>{sucesso}</p>}

      {podeCriar && (
        <form className="card" onSubmit={salvar} style={{ marginBottom: "1.25rem" }}>
          <h3>Registrar evolucao</h3>
          {atendimentos.length === 0 ? (
            <p>Nao ha atendimentos realizados disponiveis para registrar.</p>
          ) : (
            <>
              <label>
                Atendimento realizado
                <select required value={agendamentoId} onChange={(event) => setAgendamentoId(event.target.value)}>
                  {atendimentos.map((item) => (
                    <option key={item.id} value={item.id}>
                      {dataHora(item.inicio)} — {item.paciente_nome}
                    </option>
                  ))}
                </select>
              </label>
              <label style={{ marginTop: "0.75rem" }}>
                Evolucao clinica
                <textarea
                  required
                  minLength={1}
                  maxLength={20000}
                  rows={7}
                  value={evolucao}
                  onChange={(event) => setEvolucao(event.target.value)}
                  placeholder="Registre a evolucao do atendimento..."
                />
              </label>
              <button
                type="submit"
                className="btn btn-primary"
                disabled={salvando || !evolucao.trim() || !agendamentoId}
                style={{ marginTop: "0.75rem" }}
              >
                {salvando ? "Salvando..." : "Registrar evolucao"}
              </button>
            </>
          )}
        </form>
      )}

      {podeLer && (
        <section>
          <h3>Historico de evolucoes</h3>
          {evolucoes.length === 0 ? (
            <p>Nenhuma evolucao registrada.</p>
          ) : (
            <div className="lista-prontuario">
              {evolucoes.map((item) => (
                <article className="card" key={item.id}>
                  <header className="prontuario-cabecalho">
                    <div>
                      <h4>{item.paciente_nome}</h4>
                      <small>{dataHora(item.criado_em)} · {item.psicologo_nome}</small>
                    </div>
                    <small>Atendimento #{item.agendamento_id}</small>
                  </header>
                  <p className="prontuario-texto">{item.evolucao}</p>
                </article>
              ))}
            </div>
          )}
        </section>
      )}
    </>
  );
}
