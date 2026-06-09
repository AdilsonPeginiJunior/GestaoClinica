/**
 * Rotas da aplicacao e protecao por autenticacao.
 */
import type { ReactNode } from "react";
import { BrowserRouter, Navigate, Route, Routes } from "react-router-dom";
import Layout from "./components/Layout";
import { AuthProvider, useAuth } from "./context/AuthContext";
import Agenda from "./pages/Agenda";
import Dashboard from "./pages/Dashboard";
import Login from "./pages/Login";
import Pacientes from "./pages/Pacientes";
import Psicologos from "./pages/Psicologos";
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
            <Route index element={<Dashboard />} />
            <Route path="pacientes" element={<Pacientes />} />
            <Route path="psicologos" element={<Psicologos />} />
            <Route path="agenda" element={<Agenda />} />
            <Route path="relatorios" element={<Relatorios />} />
          </Route>
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </BrowserRouter>
    </AuthProvider>
  );
}
