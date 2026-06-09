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

  const podeRelatorios =
    usuario?.perfil === "admin" ||
    usuario?.perfil === "socia" ||
    usuario?.perfil === "psicologo";

  return (
    <div className="app-shell">
      <aside className="sidebar">
        <h1>Gestão Clínica</h1>
        <p className="subtitulo">Protótipo v0.1</p>
        <nav>
          <NavLink to="/" end className={({ isActive }) => (isActive ? "ativo" : "")}>
            Dashboard
          </NavLink>
          <NavLink to="/pacientes" className={({ isActive }) => (isActive ? "ativo" : "")}>
            Pacientes
          </NavLink>
          <NavLink to="/psicologos" className={({ isActive }) => (isActive ? "ativo" : "")}>
            Psicólogos
          </NavLink>
          <NavLink to="/agenda" className={({ isActive }) => (isActive ? "ativo" : "")}>
            Agenda
          </NavLink>
          {podeRelatorios && (
            <NavLink to="/relatorios" className={({ isActive }) => (isActive ? "ativo" : "")}>
              Relatórios
            </NavLink>
          )}
        </nav>
        <div className="usuario">
          <div>{usuario?.nome}</div>
          <div>{usuario ? ROTULO_PERFIL[usuario.perfil] : ""}</div>
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

