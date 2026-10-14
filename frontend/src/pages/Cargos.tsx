import { useCallback, useEffect, useState, type FormEvent } from "react";
import axios from "axios";
import {
  assignCargo,
  createCargo,
  deleteCargo,
  fetchCargos,
  fetchPermissoes,
  fetchUsuariosCargos,
  updateCargo,
} from "../api";
import type { Cargo, Permissao, UsuarioCargo } from "../types";

export default function Cargos() {
  const [cargos, setCargos] = useState<Cargo[]>([]);
  const [permissoes, setPermissoes] = useState<Permissao[]>([]);
  const [usuarios, setUsuarios] = useState<UsuarioCargo[]>([]);
  const [cargoId, setCargoId] = useState<number | null>(null);
  const [nome, setNome] = useState("");
  const [descricao, setDescricao] = useState("");
  const [permissaoIds, setPermissaoIds] = useState<number[]>([]);
  const [erro, setErro] = useState<string | null>(null);
  const [sucesso, setSucesso] = useState<string | null>(null);
  const [salvando, setSalvando] = useState(false);

  const carregar = useCallback(async () => {
    const [listaCargos, listaPermissoes, listaUsuarios] = await Promise.all([
      fetchCargos(),
      fetchPermissoes(),
      fetchUsuariosCargos(),
    ]);
    setCargos(listaCargos);
    setPermissoes(listaPermissoes);
    setUsuarios(listaUsuarios);
  }, []);

  useEffect(() => {
    carregar().catch((err: unknown) => {
      setErro(mensagemErro(err, "Nao foi possivel carregar cargos e permissoes."));
    });
  }, [carregar]);

  function selecionarCargo(cargo: Cargo | null) {
    setCargoId(cargo?.id ?? null);
    setNome(cargo?.nome ?? "");
    setDescricao(cargo?.descricao ?? "");
    setPermissaoIds(cargo?.permissoes.map((permissao) => permissao.id) ?? []);
    setErro(null);
    setSucesso(null);
  }

  function alternarPermissao(id: number) {
    setPermissaoIds((selecionadas) =>
      selecionadas.includes(id)
        ? selecionadas.filter((item) => item !== id)
        : [...selecionadas, id],
    );
  }

  async function salvarCargo(event: FormEvent) {
    event.preventDefault();
    setErro(null);
    setSucesso(null);
    setSalvando(true);
    try {
      const payload = { nome: nome.trim(), descricao: descricao.trim(), permissao_ids: permissaoIds };
      if (cargoId === null) await createCargo(payload);
      else await updateCargo(cargoId, payload);
      await carregar();
      selecionarCargo(null);
      setSucesso("Cargo salvo. A API aplica as permissoes nas proximas requisicoes; atualize a sessao para renovar o menu.");
    } catch (err) {
      setErro(mensagemErro(err, "Nao foi possivel salvar o cargo."));
    } finally {
      setSalvando(false);
    }
  }

  async function removerCargo(cargo: Cargo) {
    if (!window.confirm(`Excluir o cargo "${cargo.nome}"?`)) return;
    setErro(null);
    setSucesso(null);
    try {
      await deleteCargo(cargo.id);
      await carregar();
      selecionarCargo(null);
      setSucesso("Cargo excluido.");
    } catch (err) {
      setErro(mensagemErro(err, "Nao foi possivel excluir o cargo."));
    }
  }

  async function mudarCargoUsuario(usuario: UsuarioCargo, value: string) {
    if (!value) return;
    setErro(null);
    setSucesso(null);
    try {
      await assignCargo(usuario.id, Number(value));
      await carregar();
      setSucesso(`Cargo atualizado para ${usuario.nome}.`);
    } catch (err) {
      setErro(mensagemErro(err, "Nao foi possivel atribuir o cargo."));
    }
  }

  return (
    <>
      <header className="page-header">
        <h2>Cargos e acessos</h2>
        <p>Cadastre cargos, selecione as funcoes permitidas e atribua cargos aos usuarios.</p>
      </header>
      {erro && <p className="erro">{erro}</p>}
      {sucesso && <p style={{ color: "var(--cor-sucesso)" }}>{sucesso}</p>}

      <section className="card" style={{ marginBottom: "1.25rem" }}>
        <h3>Usuarios e cargos</h3>
        <div className="tabela-wrapper">
          <table className="tabela">
            <thead>
              <tr><th>Usuario</th><th>Perfil base</th><th>Cargo autorizado</th></tr>
            </thead>
            <tbody>
              {usuarios.map((usuario) => (
                <tr key={usuario.id}>
                  <td>{usuario.nome}<br /><small>{usuario.email}</small></td>
                  <td>{usuario.perfil}</td>
                  <td>
                    <select
                      aria-label={`Cargo de ${usuario.nome}`}
                      value={usuario.cargo_id ?? ""}
                      onChange={(event) => mudarCargoUsuario(usuario, event.target.value)}
                    >
                      <option value="" disabled>Selecione um cargo</option>
                      {cargos.map((cargo) => (
                        <option key={cargo.id} value={cargo.id}>{cargo.nome}</option>
                      ))}
                    </select>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      <div className="filtros">
        <button type="button" className="btn btn-secondary" onClick={() => selecionarCargo(null)}>
          Novo cargo
        </button>
        {cargos.map((cargo) => (
          <button
            type="button"
            className="btn btn-secondary"
            key={cargo.id}
            onClick={() => selecionarCargo(cargo)}
          >
            {cargo.nome}
          </button>
        ))}
      </div>

      <form className="card" onSubmit={salvarCargo}>
        <h3>{cargoId === null ? "Novo cargo" : `Editar cargo: ${nome}`}</h3>
        <div className="form-grid" style={{ maxWidth: "none", gridTemplateColumns: "repeat(auto-fit, minmax(240px, 1fr))" }}>
          <label>
            Nome
            <input required minLength={2} maxLength={80} value={nome} onChange={(event) => setNome(event.target.value)} />
          </label>
          <label>
            Descricao
            <input maxLength={255} value={descricao} onChange={(event) => setDescricao(event.target.value)} />
          </label>
        </div>
        <h4>Funcoes autorizadas</h4>
        <div className="permissoes-grid">
          {permissoes.map((permissao) => (
            <label className="permissao-item" key={permissao.id}>
              <input
                type="checkbox"
                checked={permissaoIds.includes(permissao.id)}
                onChange={() => alternarPermissao(permissao.id)}
              />
              <span><strong>{permissao.nome}</strong><br /><small>{permissao.descricao}</small></span>
            </label>
          ))}
        </div>
        <div className="acoes-linha" style={{ marginTop: "1rem" }}>
          <button type="submit" className="btn btn-primary" disabled={salvando}>
            {salvando ? "Salvando..." : "Salvar cargo"}
          </button>
          {cargoId !== null && (
            <button type="button" className="btn btn-secondary" onClick={() => {
              const selected = cargos.find((cargo) => cargo.id === cargoId);
              if (selected) void removerCargo(selected);
            }}>
              Excluir cargo
            </button>
          )}
        </div>
      </form>
    </>
  );
}

function mensagemErro(error: unknown, fallback: string): string {
  if (axios.isAxiosError(error) && error.response?.data?.detail) {
    return String(error.response.data.detail);
  }
  return error instanceof Error ? error.message : fallback;
}
