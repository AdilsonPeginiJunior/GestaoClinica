from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.models import (
    PerfilUsuario,
    StatusAgendamento,
    TipoAtendimento,
    TipoLancamento,
)


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    sub: str | None = None


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class UsuarioBase(BaseModel):
    nome: str
    email: EmailStr
    perfil: PerfilUsuario
    ativo: bool = True
    psicologo_id: int | None = None


class UsuarioCreate(UsuarioBase):
    password: str = Field(min_length=6)


class UsuarioRead(UsuarioBase):
    model_config = ConfigDict(from_attributes=True)
    id: int


class UsuarioMe(UsuarioRead):
    psicologo_nome: str | None = None
    cargo_id: int | None = None
    cargo_nome: str | None = None
    permissoes: list[str] = Field(default_factory=list)


class PermissaoRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    chave: str
    nome: str
    descricao: str


class CargoRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    nome: str
    descricao: str | None
    permissoes: list[PermissaoRead]


class CargoCreate(BaseModel):
    nome: str = Field(min_length=2, max_length=80)
    descricao: str | None = Field(default=None, max_length=255)
    permissao_ids: list[int] = Field(default_factory=list)


class CargoUpdate(BaseModel):
    nome: str | None = Field(default=None, min_length=2, max_length=80)
    descricao: str | None = Field(default=None, max_length=255)
    permissao_ids: list[int] | None = None


class UsuarioCargoRead(BaseModel):
    id: int
    nome: str
    email: EmailStr
    perfil: PerfilUsuario
    cargo_id: int | None
    cargo_nome: str | None


class UsuarioCargoUpdate(BaseModel):
    cargo_id: int


class ProntuarioCreate(BaseModel):
    agendamento_id: int
    evolucao: str = Field(min_length=1, max_length=20000)


class ProntuarioRead(BaseModel):
    id: int
    paciente_id: int
    paciente_nome: str
    agendamento_id: int
    psicologo_id: int
    psicologo_nome: str
    evolucao: str
    criado_em: datetime


class PsicologoBase(BaseModel):
    nome: str
    crp: str
    email: EmailStr
    telefone: str | None = None
    percentual_repasse: float = Field(ge=0, le=100, default=60.0)
    ativo: bool = True


class PsicologoCreate(PsicologoBase):
    pass


class PsicologoUpdate(BaseModel):
    nome: str | None = None
    crp: str | None = None
    email: EmailStr | None = None
    telefone: str | None = None
    percentual_repasse: float | None = Field(default=None, ge=0, le=100)
    ativo: bool | None = None


class PsicologoRead(PsicologoBase):
    model_config = ConfigDict(from_attributes=True)
    id: int


class PacienteBase(BaseModel):
    nome: str
    cpf: str | None = None
    telefone: str | None = None
    email: EmailStr | None = None
    tipo_atendimento: TipoAtendimento = TipoAtendimento.particular
    observacoes: str | None = None
    ativo: bool = True


class PacienteCreate(PacienteBase):
    pass


class PacienteUpdate(BaseModel):
    nome: str | None = None
    cpf: str | None = None
    telefone: str | None = None
    email: EmailStr | None = None
    tipo_atendimento: TipoAtendimento | None = None
    observacoes: str | None = None
    ativo: bool | None = None


class PacienteRead(PacienteBase):
    model_config = ConfigDict(from_attributes=True)
    id: int


class AgendamentoBase(BaseModel):
    paciente_id: int
    psicologo_id: int
    inicio: datetime
    fim: datetime
    status: StatusAgendamento = StatusAgendamento.agendado
    observacoes: str | None = None


class AgendamentoCreate(AgendamentoBase):
    pass


class AgendamentoUpdate(BaseModel):
    paciente_id: int | None = None
    psicologo_id: int | None = None
    inicio: datetime | None = None
    fim: datetime | None = None
    status: StatusAgendamento | None = None
    observacoes: str | None = None


class AgendamentoRead(AgendamentoBase):
    model_config = ConfigDict(from_attributes=True)
    id: int
    criado_em: datetime
    paciente_nome: str | None = None
    psicologo_nome: str | None = None


class LancamentoBase(BaseModel):
    agendamento_id: int | None = None
    psicologo_id: int | None = None
    descricao: str
    tipo: TipoLancamento = TipoLancamento.receita
    valor: float
    data_lancamento: datetime | None = None


class LancamentoCreate(LancamentoBase):
    pass


class LancamentoRead(LancamentoBase):
    model_config = ConfigDict(from_attributes=True)
    id: int
    automatico: bool


class DashboardStats(BaseModel):
    perfil: PerfilUsuario
    total_pacientes: int
    total_agendamentos: int
    agendamentos_hoje: int
    agendamentos_realizados: int
    receita_periodo: float
    repasse_periodo: float
    extras: dict[str, Any] = Field(default_factory=dict)


class RelatorioPsicologo(BaseModel):
    psicologo_id: int
    psicologo_nome: str
    periodo_inicio: datetime
    periodo_fim: datetime
    total_sessoes: int
    sessoes_realizadas: int
    receita_bruta: float
    repasse_total: float
    agendamentos: list[AgendamentoRead]
    lancamentos: list[LancamentoRead]
