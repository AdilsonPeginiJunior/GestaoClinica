/**
 * Listagem e cadastro rapido de pacientes (recepcao / gestao).
 */
import { useCallback, useEffect, useState, type FormEvent } from "react";
import { createPaciente, fetchPacientes } from "../api";
import axios from "axios";
import type { Paciente, PacienteCreate, TipoAtendimento } from "../types";
import { useAuth } from "../context/AuthContext";

export default function Pacientes() {
  const { usuario } = useAuth();
  const podeGerenciar = Boolean(usuario?.permissoes.includes("pacientes:gerenciar") && usuario.perfil !== "psicologo");
  const [lista, setLista] = useState<Paciente[]>([]);
  const [busca, setBusca] = useState("");
  const [mostrarForm, setMostrarForm] = useState(false);
  const [form, setForm] = useState<PacienteCreate>({
    nome: "",
    tipo_atendimento: "particular",
  });
  const [erro, setErro] = useState<string | null>(null);
  const [sucesso, setSucesso] = useState<string | null>(null);

  const carregar = useCallback((q?: string) => {
    fetchPacientes(q)
      .then(setLista)
      .catch(() => setErro("Erro ao carregar pacientes."));
  }, []);

  useEffect(() => {
    carregar();
  }, [carregar]);

  function handleBusca(e: FormEvent) {
    e.preventDefault();
    carregar(busca || undefined);
  }

  async function handleCriar(e: FormEvent) {
    e.preventDefault();
    setErro(null);
    setSucesso(null);
    try {
      await createPaciente(form);
      setForm({ nome: "", tipo_atendimento: "particular" });
      setMostrarForm(false);
      setSucesso(`Paciente "${form.nome}" cadastrado.`);
      carregar();
    } catch (err) {
      const detail =
        axios.isAxiosError(err) && err.response?.data?.detail
          ? String(err.response.data.detail)
          : err instanceof Error
            ? err.message
            : "Nao foi possivel cadastrar.";
      setErro(detail);
    }
  }

  return (
    <>
      <header className="page-header">
        <h2>Pacientes</h2>
        <p>Cadastro administrativo — sem dados clinicos sigilosos neste prototipo.</p>
        {usuario?.perfil === "psicologo" && <p>Pacientes vinculados à sua agenda ou recorrência. Novos pacientes são direcionados pela recepção ou gestão.</p>}
      </header>
      {erro && <p className="erro">{erro}</p>}
      {sucesso && <p style={{ color: "var(--cor-sucesso)", fontSize: "0.9rem" }}>{sucesso}</p>}
      <div className="filtros">
        <form onSubmit={handleBusca} style={{ display: "flex", gap: "0.5rem" }}>
          <input
            placeholder="Buscar por nome..."
            value={busca}
            onChange={(e) => setBusca(e.target.value)}
          />
          <button type="submit" className="btn btn-secondary">
            Buscar
          </button>
        </form>
        {podeGerenciar && (
          <button type="button" className="btn btn-primary" onClick={() => setMostrarForm(!mostrarForm)}>
            {mostrarForm ? "Cancelar" : "Novo paciente"}
          </button>
        )}
      </div>
      {mostrarForm && podeGerenciar && (
        <form onSubmit={handleCriar} className="card form-grid" style={{ marginBottom: "1rem" }}>
          <label>
            Nome completo
            <input
              required
              value={form.nome}
              onChange={(e) => setForm({ ...form, nome: e.target.value })}
            />
          </label>
          <label>
            CPF
            <input
              value={form.cpf ?? ""}
              onChange={(e) => setForm({ ...form, cpf: e.target.value })}
            />
          </label>
          <label>
            Telefone
            <input
              value={form.telefone ?? ""}
              onChange={(e) => setForm({ ...form, telefone: e.target.value })}
            />
          </label>
          <label>
            Tipo padrao
            <select
              value={form.tipo_atendimento}
              onChange={(e) =>
                setForm({ ...form, tipo_atendimento: e.target.value as TipoAtendimento })
              }
            >
              <option value="particular">Particular</option>
              <option value="convenio">Convenio</option>
            </select>
          </label>
          <button type="submit" className="btn btn-primary">
            Salvar
          </button>
        </form>
      )}
      <div className="tabela-wrapper">
      <table className="tabela">
        <thead>
          <tr>
            <th>Nome</th>
            <th>CPF</th>
            <th>Telefone</th>
            <th>Tipo</th>
            <th>Status</th>
          </tr>
        </thead>
        <tbody>
          {lista.map((p) => (
            <tr key={p.id}>
              <td>{p.nome}</td>
              <td>{p.cpf ?? "—"}</td>
              <td>{p.telefone ?? "—"}</td>
              <td>{p.tipo_atendimento}</td>
              <td>{p.ativo ? "Ativo" : "Inativo"}</td>
            </tr>
          ))}
        </tbody>
      </table>
      </div>
    </>
  );
}
