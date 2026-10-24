"""
Indicadores do painel inicial e relatorio financeiro por psicologo.
"""

from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func
from sqlalchemy.orm import Session, joinedload

from app.auth import has_permission, require_permission
from app.database import get_db
from app.escopo import filtrar_pacientes, profissional_restrito
from app.models import (
    Agendamento,
    LancamentoFinanceiro,
    Paciente,
    PerfilUsuario,
    Psicologo,
    StatusAgendamento,
    TipoLancamento,
    Usuario,
)
from app.schemas import AgendamentoRead, DashboardStats, LancamentoRead, RelatorioPsicologo
from app.services import filtro_parcela_clinica_legada

router = APIRouter(prefix="/api", tags=["dashboard"])


def _agendamento_read(ag: Agendamento) -> AgendamentoRead:
    return AgendamentoRead(
        id=ag.id,
        paciente_id=ag.paciente_id,
        psicologo_id=ag.psicologo_id,
        inicio=ag.inicio,
        fim=ag.fim,
        status=ag.status,
        observacoes=ag.observacoes,
        criado_em=ag.criado_em,
        paciente_nome=ag.paciente.nome if ag.paciente else None,
        psicologo_nome=ag.psicologo.nome if ag.psicologo else None,
    )


@router.get("/dashboard", response_model=DashboardStats)
def dashboard(
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_permission("dashboard:acessar")),
):
    hoje_ini = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    hoje_fim = hoje_ini + timedelta(days=1)
    mes_ini = hoje_ini.replace(day=1)

    ag_query = db.query(Agendamento)
    lanc_query = db.query(LancamentoFinanceiro).filter(LancamentoFinanceiro.data_lancamento >= mes_ini)
    pacientes_query = filtrar_pacientes(db.query(Paciente).filter(Paciente.ativo.is_(True)), current_user)

    extras: dict = {}

    pid = profissional_restrito(current_user)
    if pid is not None:
        ag_query = ag_query.filter(Agendamento.psicologo_id == pid)
        lanc_query = lanc_query.filter(LancamentoFinanceiro.psicologo_id == pid)
        extras["meu_psicologo_id"] = pid

    total_pacientes = pacientes_query.count()
    total_agendamentos = ag_query.count()
    agendamentos_hoje = ag_query.filter(Agendamento.inicio >= hoje_ini, Agendamento.inicio < hoje_fim).count()
    agendamentos_realizados = ag_query.filter(Agendamento.status == StatusAgendamento.realizado).count()

    # Versões antigas gravavam também a parcela da clínica como receita.
    # Preservamos esses registros, sem somá-los novamente ao faturamento bruto.
    # O conjunto completo evita excluir receitas manuais ou sem profissional.
    receita_periodo = (
        lanc_query.filter(
            LancamentoFinanceiro.tipo == TipoLancamento.receita,
            ~filtro_parcela_clinica_legada(),
        )
        .with_entities(func.coalesce(func.sum(LancamentoFinanceiro.valor), 0.0))
        .scalar()
        or 0.0
    )
    repasse_periodo = (
        lanc_query.filter(LancamentoFinanceiro.tipo == TipoLancamento.repasse)
        .with_entities(func.coalesce(func.sum(LancamentoFinanceiro.valor), 0.0))
        .scalar()
        or 0.0
    )
    if not has_permission(current_user, "financeiro:consultar"):
        receita_periodo = 0.0
        repasse_periodo = 0.0

    if current_user.perfil in {PerfilUsuario.admin, PerfilUsuario.socia}:
        extras["psicologos_ativos"] = db.query(Psicologo).filter(Psicologo.ativo.is_(True)).count()

    return DashboardStats(
        perfil=current_user.perfil,
        total_pacientes=total_pacientes,
        total_agendamentos=total_agendamentos,
        agendamentos_hoje=agendamentos_hoje,
        agendamentos_realizados=agendamentos_realizados,
        receita_periodo=float(receita_periodo),
        repasse_periodo=float(repasse_periodo),
        extras=extras,
    )


@router.get("/relatorios/psicologo/{psicologo_id}", response_model=RelatorioPsicologo)
def relatorio_psicologo(
    psicologo_id: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(
        require_permission("relatorios:consultar_proprio", "relatorios:consultar_todos")
    ),
    data_inicio: datetime | None = Query(None),
    data_fim: datetime | None = Query(None),
):
    profissional_restrito(current_user)
    if has_permission(current_user, "relatorios:consultar_todos"):
        pass
    elif (
        has_permission(current_user, "relatorios:consultar_proprio")
        and current_user.psicologo_id == psicologo_id
    ):
        pass
    else:
        raise HTTPException(status_code=403, detail="Acesso negado")

    psicologo = db.get(Psicologo, psicologo_id)
    if not psicologo:
        raise HTTPException(status_code=404, detail="Psicologo nao encontrado")

    inicio = data_inicio or datetime.utcnow().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    fim = data_fim or datetime.utcnow()

    agendamentos = (
        db.query(Agendamento)
        .options(joinedload(Agendamento.paciente), joinedload(Agendamento.psicologo))
        .filter(
            Agendamento.psicologo_id == psicologo_id,
            Agendamento.inicio >= inicio,
            Agendamento.inicio <= fim,
        )
        .order_by(Agendamento.inicio)
        .all()
    )

    lancamentos = (
        db.query(LancamentoFinanceiro)
        .filter(
            LancamentoFinanceiro.psicologo_id == psicologo_id,
            LancamentoFinanceiro.data_lancamento >= inicio,
            LancamentoFinanceiro.data_lancamento <= fim,
        )
        .order_by(LancamentoFinanceiro.data_lancamento)
        .all()
    )

    realizados = [a for a in agendamentos if a.status == StatusAgendamento.realizado]
    receita_bruta = sum(l.valor for l in lancamentos if l.tipo == TipoLancamento.receita)
    repasse_total = sum(l.valor for l in lancamentos if l.tipo == TipoLancamento.repasse)

    return RelatorioPsicologo(
        psicologo_id=psicologo.id,
        psicologo_nome=psicologo.nome,
        periodo_inicio=inicio,
        periodo_fim=fim,
        total_sessoes=len(agendamentos),
        sessoes_realizadas=len(realizados),
        receita_bruta=float(receita_bruta),
        repasse_total=float(repasse_total),
        agendamentos=[_agendamento_read(a) for a in agendamentos],
        lancamentos=[LancamentoRead.model_validate(l) for l in lancamentos],
    )
