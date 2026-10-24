"""
Modelos ORM — espelham o domínio da clínica (agenda + financeiro por psicólogo).

Melhoria futura: separar tabela de convênios/planos e histórico de repasse.
"""

import enum
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Enum, Float, ForeignKey, Index, Integer, String, Table, Text, Column, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

VALOR_PARTICULAR = 220.0
VALOR_CONVENIO = 160.0

cargo_permissoes = Table(
    "cargo_permissoes",
    Base.metadata,
    Column("cargo_id", ForeignKey("cargos.id"), primary_key=True),
    Column("permissao_id", ForeignKey("permissoes.id"), primary_key=True),
)


class PerfilUsuario(str, enum.Enum):
    recepcionista = "recepcionista"
    psicologo = "psicologo"
    socia = "socia"
    admin = "admin"


class TipoAtendimento(str, enum.Enum):
    particular = "particular"
    convenio = "convenio"


class StatusAgendamento(str, enum.Enum):
    agendado = "agendado"
    confirmado = "confirmado"
    cancelado = "cancelado"
    realizado = "realizado"
    falta = "falta"


class TipoLancamento(str, enum.Enum):
    receita = "receita"
    repasse = "repasse"


class Usuario(Base):
    __tablename__ = "usuarios"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    nome: Mapped[str] = mapped_column(String(120), nullable=False)
    email: Mapped[str] = mapped_column(String(120), unique=True, index=True, nullable=False)
    senha_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    perfil: Mapped[PerfilUsuario] = mapped_column(Enum(PerfilUsuario), nullable=False)
    ativo: Mapped[bool] = mapped_column(Boolean, default=True)
    psicologo_id: Mapped[int | None] = mapped_column(ForeignKey("psicologos.id"), nullable=True)
    cargo_id: Mapped[int | None] = mapped_column(ForeignKey("cargos.id"), nullable=True)

    psicologo: Mapped["Psicologo | None"] = relationship(back_populates="usuario")
    cargo: Mapped["Cargo | None"] = relationship(back_populates="usuarios")


class Cargo(Base):
    __tablename__ = "cargos"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    nome: Mapped[str] = mapped_column(String(80), unique=True, nullable=False)
    descricao: Mapped[str | None] = mapped_column(String(255))
    usuarios: Mapped[list["Usuario"]] = relationship(back_populates="cargo")
    permissoes: Mapped[list["Permissao"]] = relationship(
        secondary=cargo_permissoes, back_populates="cargos"
    )


class Permissao(Base):
    __tablename__ = "permissoes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    chave: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    nome: Mapped[str] = mapped_column(String(100), nullable=False)
    descricao: Mapped[str] = mapped_column(String(255), nullable=False)
    cargos: Mapped[list[Cargo]] = relationship(
        secondary=cargo_permissoes, back_populates="permissoes"
    )


class Prontuario(Base):
    __tablename__ = "prontuarios"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    paciente_id: Mapped[int] = mapped_column(ForeignKey("pacientes.id"), nullable=False, index=True)
    agendamento_id: Mapped[int] = mapped_column(
        ForeignKey("agendamentos.id"), unique=True, nullable=False, index=True
    )
    psicologo_id: Mapped[int] = mapped_column(ForeignKey("psicologos.id"), nullable=False, index=True)
    evolucao: Mapped[str] = mapped_column(Text, nullable=False)
    criado_em: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    paciente: Mapped["Paciente"] = relationship()
    agendamento: Mapped["Agendamento"] = relationship(back_populates="prontuario")
    psicologo: Mapped["Psicologo"] = relationship()


class Psicologo(Base):
    __tablename__ = "psicologos"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    nome: Mapped[str] = mapped_column(String(120), nullable=False)
    crp: Mapped[str] = mapped_column(String(20), nullable=False)
    email: Mapped[str] = mapped_column(String(120), unique=True, index=True)
    telefone: Mapped[str | None] = mapped_column(String(30))
    percentual_repasse: Mapped[float] = mapped_column(Float, default=60.0)
    ativo: Mapped[bool] = mapped_column(Boolean, default=True)

    usuario: Mapped["Usuario | None"] = relationship(back_populates="psicologo", uselist=False)
    agendamentos: Mapped[list["Agendamento"]] = relationship(back_populates="psicologo")
    lancamentos: Mapped[list["LancamentoFinanceiro"]] = relationship(back_populates="psicologo")


class Paciente(Base):
    __tablename__ = "pacientes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    nome: Mapped[str] = mapped_column(String(120), nullable=False)
    cpf: Mapped[str | None] = mapped_column(String(14), unique=True, index=True)
    telefone: Mapped[str | None] = mapped_column(String(30))
    email: Mapped[str | None] = mapped_column(String(120))
    tipo_atendimento: Mapped[TipoAtendimento] = mapped_column(
        Enum(TipoAtendimento), default=TipoAtendimento.particular
    )
    observacoes: Mapped[str | None] = mapped_column(Text)
    ativo: Mapped[bool] = mapped_column(Boolean, default=True)

    agendamentos: Mapped[list["Agendamento"]] = relationship(back_populates="paciente")


class Agendamento(Base):
    __tablename__ = "agendamentos"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    paciente_id: Mapped[int] = mapped_column(ForeignKey("pacientes.id"), nullable=False)
    psicologo_id: Mapped[int] = mapped_column(ForeignKey("psicologos.id"), nullable=False)
    inicio: Mapped[datetime] = mapped_column(DateTime, nullable=False, index=True)
    fim: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    status: Mapped[StatusAgendamento] = mapped_column(
        Enum(StatusAgendamento), default=StatusAgendamento.agendado
    )
    observacoes: Mapped[str | None] = mapped_column(Text)
    criado_em: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    paciente: Mapped["Paciente"] = relationship(back_populates="agendamentos")
    psicologo: Mapped["Psicologo"] = relationship(back_populates="agendamentos")
    lancamentos: Mapped[list["LancamentoFinanceiro"]] = relationship(back_populates="agendamento")
    prontuario: Mapped["Prontuario | None"] = relationship(back_populates="agendamento", uselist=False)
    reagendamento: Mapped["Reagendamento | None"] = relationship(
        foreign_keys="Reagendamento.agendamento_original_id", uselist=False
    )
    origem_reagendamento: Mapped["Reagendamento | None"] = relationship(
        foreign_keys="Reagendamento.novo_agendamento_id", uselist=False
    )
    ocorrencia: Mapped["OcorrenciaRecorrencia | None"] = relationship(back_populates="agendamento", uselist=False)


class Recorrencia(Base):
    """Reserva sem término obrigatório; alteração cria nova versão ligada à anterior."""
    __tablename__ = "recorrencias_agenda"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    paciente_id: Mapped[int] = mapped_column(ForeignKey("pacientes.id"), nullable=False, index=True)
    psicologo_id: Mapped[int] = mapped_column(ForeignKey("psicologos.id"), nullable=False, index=True)
    inicio: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    duracao_minutos: Mapped[int] = mapped_column(Integer, nullable=False)
    intervalo_dias: Mapped[int] = mapped_column(Integer, nullable=False)
    encerrada_em: Mapped[datetime | None] = mapped_column(DateTime)
    motivo_encerramento: Mapped[str | None] = mapped_column(String(500))
    encerrada_por_id: Mapped[int | None] = mapped_column(ForeignKey("usuarios.id"))
    anterior_id: Mapped[int | None] = mapped_column(ForeignKey("recorrencias_agenda.id"), unique=True)
    usuario_id: Mapped[int] = mapped_column(ForeignKey("usuarios.id"), nullable=False)
    criado_em: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)
    paciente: Mapped["Paciente"] = relationship()
    psicologo: Mapped["Psicologo"] = relationship()


class OcorrenciaRecorrencia(Base):
    __tablename__ = "ocorrencias_recorrencia"
    __table_args__ = (UniqueConstraint("recorrencia_id", "inicio_original", name="uq_recorrencia_ocorrencia"),)
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    recorrencia_id: Mapped[int] = mapped_column(ForeignKey("recorrencias_agenda.id"), nullable=False, index=True)
    inicio_original: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    agendamento_id: Mapped[int] = mapped_column(ForeignKey("agendamentos.id"), nullable=False, unique=True)
    recorrencia: Mapped["Recorrencia"] = relationship()
    agendamento: Mapped["Agendamento"] = relationship(back_populates="ocorrencia")


class Reagendamento(Base):
    """Preserva o vínculo do atendimento original com um único sucessor."""

    __tablename__ = "reagendamentos"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    agendamento_original_id: Mapped[int] = mapped_column(ForeignKey("agendamentos.id"), unique=True, nullable=False)
    novo_agendamento_id: Mapped[int] = mapped_column(ForeignKey("agendamentos.id"), unique=True, nullable=False)
    usuario_id: Mapped[int] = mapped_column(ForeignKey("usuarios.id"), nullable=False)
    criado_em: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)


class LancamentoFinanceiro(Base):
    __tablename__ = "lancamentos_financeiros"
    __table_args__ = (
        Index("uq_lancamento_chave_automatica", "agendamento_id", "chave_automatica", unique=True),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    agendamento_id: Mapped[int | None] = mapped_column(ForeignKey("agendamentos.id"), nullable=True)
    psicologo_id: Mapped[int | None] = mapped_column(ForeignKey("psicologos.id"), nullable=True)
    descricao: Mapped[str] = mapped_column(String(255), nullable=False)
    tipo: Mapped[TipoLancamento] = mapped_column(Enum(TipoLancamento), default=TipoLancamento.receita)
    valor: Mapped[float] = mapped_column(Float, nullable=False)
    data_lancamento: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)
    automatico: Mapped[bool] = mapped_column(Boolean, default=False)
    chave_automatica: Mapped[str | None] = mapped_column(String(64), nullable=True)

    agendamento: Mapped["Agendamento | None"] = relationship(back_populates="lancamentos")
    psicologo: Mapped["Psicologo | None"] = relationship(back_populates="lancamentos")


class EstornoFinanceiro(Base):
    """Vínculo auditável entre lançamento original e compensação, sem apagar histórico."""

    __tablename__ = "estornos_financeiros"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    lancamento_original_id: Mapped[int] = mapped_column(
        ForeignKey("lancamentos_financeiros.id"), unique=True, nullable=False
    )
    lancamento_estorno_id: Mapped[int] = mapped_column(
        ForeignKey("lancamentos_financeiros.id"), unique=True, nullable=False
    )
    usuario_id: Mapped[int] = mapped_column(ForeignKey("usuarios.id"), nullable=False)
    motivo: Mapped[str] = mapped_column(String(500), nullable=False)
    criado_em: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
