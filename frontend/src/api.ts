/**
 * Cliente HTTP da API — token JWT anexado automaticamente em cada requisicao.
 */
import axios from "axios";
import type {
  Agendamento,
  Cargo,
  DashboardStats,
  Paciente,
  PacienteCreate,
  Permissao,
  Prontuario,
  Psicologo,
  RelatorioPsicologo,
  StatusAgendamento,
  TokenResponse,
  Usuario,
  UsuarioCargo,
} from "./types";

const TOKEN_KEY = "gestao_clinica_token";

export const api = axios.create({
  // Em dev o Vite faz proxy de /api -> localhost:8000 (vite.config.ts)
  baseURL: import.meta.env.DEV ? "/api" : "http://localhost:8000/api",
  headers: { "Content-Type": "application/json" },
  timeout: 15000,
});

// Mensagem amigavel quando a API nao responde (backend parado ou travado)
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.code === "ECONNABORTED") {
      return Promise.reject(new Error("API demorou para responder. Verifique se o backend esta rodando."));
    }
    if (!error.response) {
      return Promise.reject(new Error("Nao foi possivel conectar a API. Execute scripts/iniciar-backend.ps1"));
    }
    return Promise.reject(error);
  },
);

// Injeta Bearer token quando o usuario ja fez login
api.interceptors.request.use((config) => {
  const token = localStorage.getItem(TOKEN_KEY);
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

export function setAuthToken(token: string | null) {
  if (token) localStorage.setItem(TOKEN_KEY, token);
  else localStorage.removeItem(TOKEN_KEY);
}

export function getStoredToken(): string | null {
  return localStorage.getItem(TOKEN_KEY);
}

export async function login(email: string, password: string): Promise<TokenResponse> {
  const { data } = await api.post<TokenResponse>("/auth/login", { email, password });
  return data;
}

export async function fetchMe(): Promise<Usuario> {
  const { data } = await api.get<Usuario>("/auth/me");
  return data;
}

export async function fetchDashboard(): Promise<DashboardStats> {
  const { data } = await api.get<DashboardStats>("/dashboard");
  return data;
}

export async function fetchPacientes(q?: string): Promise<Paciente[]> {
  const { data } = await api.get<Paciente[]>("/pacientes", { params: q ? { q } : {} });
  return data;
}

export async function createPaciente(payload: PacienteCreate): Promise<Paciente> {
  const { data } = await api.post<Paciente>("/pacientes", payload);
  return data;
}

export async function fetchPsicologos(): Promise<Psicologo[]> {
  const { data } = await api.get<Psicologo[]>("/psicologos");
  return data;
}

export async function fetchAgendamentos(params: {
  data_inicio?: string;
  data_fim?: string;
  psicologo_id?: number;
  status?: StatusAgendamento;
}): Promise<Agendamento[]> {
  const { data } = await api.get<Agendamento[]>("/agendamentos", { params });
  return data;
}

/** Novo horario na agenda (recepcao / gestao). */
export async function createAgendamento(payload: {
  paciente_id: number;
  psicologo_id: number;
  inicio: string;
  fim: string;
  status?: StatusAgendamento;
  observacoes?: string | null;
}): Promise<Agendamento> {
  const { data } = await api.post<Agendamento>("/agendamentos", payload);
  return data;
}

/** Alterar status dispara regra financeira quando status = realizado. */
export async function updateAgendamento(
  id: number,
  payload: { status?: StatusAgendamento },
): Promise<Agendamento> {
  const { data } = await api.patch<Agendamento>(`/agendamentos/${id}`, payload);
  return data;
}

export async function fetchRelatorioPsicologo(
  psicologoId: number,
  data_inicio?: string,
  data_fim?: string,
): Promise<RelatorioPsicologo> {
  const { data } = await api.get<RelatorioPsicologo>(
    `/relatorios/psicologo/${psicologoId}`,
    { params: { data_inicio, data_fim } },
  );
  return data;
}

export async function fetchProntuarios(): Promise<Prontuario[]> {
  const { data } = await api.get<Prontuario[]>("/prontuario");
  return data;
}

export async function fetchAtendimentosSemEvolucao(): Promise<Agendamento[]> {
  const { data } = await api.get<Agendamento[]>("/prontuario/atendimentos-disponiveis");
  return data;
}

export async function createProntuario(payload: {
  agendamento_id: number;
  evolucao: string;
}): Promise<Prontuario> {
  const { data } = await api.post<Prontuario>("/prontuario", payload);
  return data;
}

export async function fetchCargos(): Promise<Cargo[]> {
  const { data } = await api.get<Cargo[]>("/admin/cargos");
  return data;
}

export async function fetchPermissoes(): Promise<Permissao[]> {
  const { data } = await api.get<Permissao[]>("/admin/permissoes");
  return data;
}

export async function createCargo(payload: {
  nome: string;
  descricao: string;
  permissao_ids: number[];
}): Promise<Cargo> {
  const { data } = await api.post<Cargo>("/admin/cargos", payload);
  return data;
}

export async function updateCargo(
  id: number,
  payload: { nome: string; descricao: string; permissao_ids: number[] },
): Promise<Cargo> {
  const { data } = await api.patch<Cargo>(`/admin/cargos/${id}`, payload);
  return data;
}

export async function deleteCargo(id: number): Promise<void> {
  await api.delete(`/admin/cargos/${id}`);
}

export async function fetchUsuariosCargos(): Promise<UsuarioCargo[]> {
  const { data } = await api.get<UsuarioCargo[]>("/admin/usuarios");
  return data;
}

export async function assignCargo(usuarioId: number, cargoId: number): Promise<UsuarioCargo> {
  const { data } = await api.patch<UsuarioCargo>(`/admin/usuarios/${usuarioId}/cargo`, {
    cargo_id: cargoId,
  });
  return data;
}
