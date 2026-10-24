"""Lancamentos manuais (admin/socia). Automaticos vem de consultas realizadas."""

from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.auth import require_permission
from app.database import get_db
from app.models import EstornoFinanceiro, LancamentoFinanceiro, Psicologo, TipoLancamento, Usuario
from app.escopo import profissional_restrito
from app.transacoes import bloquear_agendamento, transacao
from app.schemas import EstornoRead, LancamentoCreate, LancamentoRead

router = APIRouter(prefix="/api/financeiro", tags=["financeiro"])


@router.get("/estornos", response_model=list[EstornoRead])
def listar_estornos(
    db: Session = Depends(get_db),
    _: Usuario = Depends(require_permission("financeiro:consultar")),
    agendamento_id: int | None = Query(None),
):
    """Consulta autoria, motivo e vínculos entre originais e compensações."""
    query = db.query(EstornoFinanceiro)
    pid = profissional_restrito(_)
    if agendamento_id is not None or pid is not None:
        query = query.join(
            LancamentoFinanceiro,
            LancamentoFinanceiro.id == EstornoFinanceiro.lancamento_original_id,
        )
    if pid is not None:
        query = query.filter(LancamentoFinanceiro.psicologo_id == pid)
    if agendamento_id is not None:
        query = query.filter(LancamentoFinanceiro.agendamento_id == agendamento_id)
    return query.order_by(EstornoFinanceiro.criado_em.desc(), EstornoFinanceiro.id.desc()).all()


@router.get("/lancamentos", response_model=list[LancamentoRead])
def listar_lancamentos(
    db: Session = Depends(get_db),
    _: Usuario = Depends(require_permission("financeiro:consultar")),
    data_inicio: datetime | None = Query(None),
    data_fim: datetime | None = Query(None),
    psicologo_id: int | None = Query(None),
    tipo: TipoLancamento | None = Query(None),
):
    query = db.query(LancamentoFinanceiro)
    pid = profissional_restrito(_)
    if pid is not None:
        query = query.filter(LancamentoFinanceiro.psicologo_id == pid)
    if data_inicio:
        query = query.filter(LancamentoFinanceiro.data_lancamento >= data_inicio)
    if data_fim:
        query = query.filter(LancamentoFinanceiro.data_lancamento <= data_fim)
    if psicologo_id is not None:
        query = query.filter(LancamentoFinanceiro.psicologo_id == psicologo_id)
    if tipo is not None:
        query = query.filter(LancamentoFinanceiro.tipo == tipo)
    return query.order_by(LancamentoFinanceiro.data_lancamento.desc()).all()


@router.post("/lancamentos", response_model=LancamentoRead, status_code=status.HTTP_201_CREATED)
def criar_lancamento_manual(
    payload: LancamentoCreate,
    db: Session = Depends(get_db),
    _: Usuario = Depends(require_permission("financeiro:gerenciar")),
):
    data = payload.model_dump()
    pid = profissional_restrito(_)
    with transacao(db):
        if pid is not None and data["psicologo_id"] not in (None, pid):
            raise HTTPException(403, "Acesso negado ao financeiro de outro profissional.")
        if data["agendamento_id"] is not None:
            ag = bloquear_agendamento(db, data["agendamento_id"])
            if pid is not None and ag.psicologo_id != pid:
                raise HTTPException(403, "Acesso negado a este atendimento.")
            if data["psicologo_id"] is not None and data["psicologo_id"] != ag.psicologo_id:
                raise HTTPException(422, "O profissional do lançamento deve ser o mesmo do atendimento.")
            data["psicologo_id"] = ag.psicologo_id
        elif pid is not None:
            data["psicologo_id"] = pid
        if data["psicologo_id"] is not None and db.get(Psicologo, data["psicologo_id"]) is None:
            raise HTTPException(422, "Profissional não encontrado.")
        if data.get("data_lancamento") is None:
            data["data_lancamento"] = datetime.utcnow()
        lanc = LancamentoFinanceiro(**data, automatico=False)
        db.add(lanc)
    db.refresh(lanc)
    return lanc
