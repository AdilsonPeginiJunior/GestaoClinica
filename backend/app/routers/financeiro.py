"""Lancamentos manuais (admin/socia). Automaticos vem de consultas realizadas."""

from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.auth import require_permission
from app.database import get_db
from app.models import LancamentoFinanceiro, TipoLancamento, Usuario
from app.schemas import LancamentoCreate, LancamentoRead

router = APIRouter(prefix="/api/financeiro", tags=["financeiro"])


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
    if data.get("data_lancamento") is None:
        data["data_lancamento"] = datetime.utcnow()
    lanc = LancamentoFinanceiro(**data, automatico=False)
    db.add(lanc)
    db.commit()
    db.refresh(lanc)
    return lanc
