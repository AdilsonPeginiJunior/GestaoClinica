/**
 * Layout principal: menu lateral conforme perfil e área de conteúdo.
 */
import { NavLink, Outlet } from "react-router-dom";
import { useAuth } from "../context/AuthContext";

const ROTULO_PERFIL: Record<string, string> = {
  recepcionista: "Recepção",
  psicologo: "Psicólogo",
  socia: "Sócia administradora",
  admin: "Administrador",
};

export default function Layout() {
  const { usuario, logout } = useAuth();

  const temPermissao = (...permissoes: string[]) =>
    permissoes.some((permissao) => usuario?.permissoes.includes(permissao));

  return (
    <div className="app-shell">
      <aside className="sidebar">
        <h1>Gestão Clínica</h1>
        <p className="subtitulo">Protótipo v0.2</p>
        <nav>
          {temPermissao("dashboard:acessar") && (
            <NavLink to="/" end className={({ isActive }) => (isActive ? "ativo" : "")}>
              Dashboard
            </NavLink>
          )}
          {temPermissao("pacientes:consultar") && (
            <NavLink to="/pacientes" className={({ isActive }) => (isActive ? "ativo" : "")}>
              Pacientes
            </NavLink>
          )}
          {temPermissao("psicologos:consultar") && (
            <NavLink to="/psicologos" className={({ isActive }) => (isActive ? "ativo" : "")}>
              Psicólogos
            </NavLink>
          )}
          {temPermissao("agenda:consultar") && (
            <NavLink to="/agenda" className={({ isActive }) => (isActive ? "ativo" : "")}>
              Agenda
            </NavLink>
          )}
          {temPermissao("relatorios:consultar_proprio", "relatorios:consultar_todos") && (
            <NavLink to="/relatorios" className={({ isActive }) => (isActive ? "ativo" : "")}>
              Relatórios
            </NavLink>
          )}
          {temPermissao("prontuario:ler_proprio", "prontuario:ler_todos", "prontuario:criar") && (
            <NavLink to="/prontuario" className={({ isActive }) => (isActive ? "ativo" : "")}>
              Prontuário
            </NavLink>
          )}
          {usuario?.perfil === "admin" && (
            <NavLink to="/cargos" className={({ isActive }) => (isActive ? "ativo" : "")}>
              Cargos e acessos
            </NavLink>
          )}
        </nav>
        <div className="usuario">
          <div>{usuario?.nome}</div>
          <div>{usuario?.cargo_nome ?? (usuario ? ROTULO_PERFIL[usuario.perfil] : "")}</div>
          <button
            type="button"
            className="btn btn-ghost btn-sm"
            style={{ marginTop: "0.5rem" }}
            onClick={logout}
          >
            Sair
          </button>
        </div>
      </aside>
      <main className="conteudo">
        <Outlet />
      </main>
    </div>
  );
}
