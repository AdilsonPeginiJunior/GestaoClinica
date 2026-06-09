"""
Modelos ORM — espelham o domínio da clínica (agenda + financeiro por psicólogo).

Melhoria futura: separar tabela de convênios/planos e histórico de repasse.
"""

import enum
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Enum, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

VALOR_PARTICULAR = 220.0
VALOR_CONVENIO = 160.0


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

    psicologo: Mapped["Psicologo | None"] = relationship(back_populates="usuario")


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


class LancamentoFinanceiro(Base):
    __tablename__ = "lancamentos_financeiros"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    agendamento_id: Mapped[int | None] = mapped_column(ForeignKey("agendamentos.id"), nullable=True)
    psicologo_id: Mapped[int | None] = mapped_column(ForeignKey("psicologos.id"), nullable=True)
    descricao: Mapped[str] = mapped_column(String(255), nullable=False)
    tipo: Mapped[TipoLancamento] = mapped_column(Enum(TipoLancamento), default=TipoLancamento.receita)
    valor: Mapped[float] = mapped_column(Float, nullable=False)
    data_lancamento: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)
    automatico: Mapped[bool] = mapped_column(Boolean, default=False)

    agendamento: Mapped["Agendamento | None"] = relationship(back_populates="lancamentos")
    psicologo: Mapped["Psicologo | None"] = relationship(back_populates="lancamentos")
