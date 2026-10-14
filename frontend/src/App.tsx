/**
 * Rotas da aplicacao e protecao por autenticacao.
 */
import type { ReactNode } from "react";
import { BrowserRouter, Navigate, Route, Routes } from "react-router-dom";
import Layout from "./components/Layout";
import { AuthProvider, useAuth } from "./context/AuthContext";
import Agenda from "./pages/Agenda";
import Cargos from "./pages/Cargos";
import Dashboard from "./pages/Dashboard";
import Login from "./pages/Login";
import Pacientes from "./pages/Pacientes";
import Psicologos from "./pages/Psicologos";
import ProntuarioPage from "./pages/Prontuario";
import Relatorios from "./pages/Relatorios";

function PrivateRoute({ children }: { children: ReactNode }) {
  const { usuario, carregando } = useAuth();
  if (carregando) {
    return <p style={{ padding: "2rem" }}>Carregando...</p>;
  }
  if (!usuario) {
    return <Navigate to="/login" replace />;
  }
  return <>{children}</>;
}

function PermissionRoute({
  permissions,
  children,
}: {
  permissions: string[];
  children: ReactNode;
}) {
  const { usuario } = useAuth();
  if (!usuario || !permissions.some((permission) => usuario.permissoes.includes(permission))) {
    return <p className="erro" role="alert" style={{ padding: "1rem" }}>Voce nao possui permissao para acessar esta tela.</p>;
  }
  return <>{children}</>;
}

function AdminRoute({ children }: { children: ReactNode }) {
  const { usuario } = useAuth();
  return usuario?.perfil === "admin"
    ? <>{children}</>
    : <p className="erro" role="alert" style={{ padding: "1rem" }}>Apenas administradores podem acessar esta tela.</p>;
}

export default function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <Routes>
          <Route path="/login" element={<Login />} />
          <Route
            path="/"
            element={
              <PrivateRoute>
                <Layout />
              </PrivateRoute>
            }
          >
            <Route
              index
              element={
                <PermissionRoute permissions={["dashboard:acessar"]}>
                  <Dashboard />
                </PermissionRoute>
              }
            />
            <Route
              path="pacientes"
              element={
                <PermissionRoute permissions={["pacientes:consultar"]}>
                  <Pacientes />
                </PermissionRoute>
              }
            />
            <Route
              path="psicologos"
              element={
                <PermissionRoute permissions={["psicologos:consultar"]}>
                  <Psicologos />
                </PermissionRoute>
              }
            />
            <Route
              path="agenda"
              element={
                <PermissionRoute permissions={["agenda:consultar"]}>
                  <Agenda />
                </PermissionRoute>
              }
            />
            <Route
              path="relatorios"
              element={
                <PermissionRoute permissions={["relatorios:consultar_proprio", "relatorios:consultar_todos"]}>
                  <Relatorios />
                </PermissionRoute>
              }
            />
            <Route
              path="prontuario"
              element={
                <PermissionRoute permissions={["prontuario:ler_proprio", "prontuario:ler_todos", "prontuario:criar"]}>
                  <ProntuarioPage />
                </PermissionRoute>
              }
            />
            <Route
              path="cargos"
              element={
                <AdminRoute>
                  <Cargos />
                </AdminRoute>
              }
            />
          </Route>
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </BrowserRouter>
    </AuthProvider>
  );
}
