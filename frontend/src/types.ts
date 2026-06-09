export type PerfilUsuario =
  | "recepcionista"
  | "psicologo"
  | "socia"
  | "admin";

export type TipoAtendimento = "particular" | "convenio";

export type StatusAgendamento =
  | "agendado"
  | "confirmado"
  | "realizado"
  | "cancelado"
  | "falta";

export type TipoLancamento = "receita" | "repasse" | "despesa";

export interface TokenResponse {
  access_token: string;
  token_type?: string;
}

export interface Usuario {
  id: number;
  nome: string;
  email: string;
  perfil: PerfilUsuario;
  ativo: boolean;
  psicologo_id: number | null;
  psicologo_nome?: string | null;
}

export interface Paciente {
  id: number;
  nome: string;
  cpf: string | null;
  telefone: string | null;
  email: string | null;
  tipo_atendimento: TipoAtendimento;
  observacoes: string | null;
  ativo: boolean;
}

export interface PacienteCreate {
  nome: string;
  cpf?: string | null;
  telefone?: string | null;
  email?: string | null;
  tipo_atendimento?: TipoAtendimento;
  observacoes?: string | null;
  ativo?: boolean;
}

export interface Psicologo {
  id: number;
  nome: string;
  crp: string;
  email: string;
  telefone: string | null;
  percentual_repasse: number;
  ativo: boolean;
}

export interface Agendamento {
  id: number;
  paciente_id: number;
  psicologo_id: number;
  inicio: string;
  fim: string;
  status: StatusAgendamento;
  observacoes: string | null;
  criado_em: string;
  paciente_nome?: string | null;
  psicologo_nome?: string | null;
}

export interface DashboardStats {
  perfil: PerfilUsuario;
  total_pacientes: number;
  total_agendamentos: number;
  agendamentos_hoje: number;
  agendamentos_realizados: number;
  receita_periodo: number;
  repasse_periodo: number;
  extras: Record<string, unknown>;
}

export interface Lancamento {
  id: number;
  agendamento_id: number | null;
  psicologo_id: number | null;
  descricao: string;
  tipo: TipoLancamento;
  valor: number;
  data_lancamento: string | null;
  automatico: boolean;
}

export interface RelatorioPsicologo {
  psicologo_id: number;
  psicologo_nome: string;
  periodo_inicio: string;
  periodo_fim: string;
  total_sessoes: number;
  sessoes_realizadas: number;
  receita_bruta: number;
  repasse_total: number;
  agendamentos: Agendamento[];
  lancamentos: Lancamento[];
}

export interface DemoUser {
  label: string;
  email: string;
  password: string;
  perfil: PerfilUsuario;
}
