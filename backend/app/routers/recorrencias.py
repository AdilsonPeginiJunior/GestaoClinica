"""Operações explícitas de recorrência; GET apenas consulta, sem gravações."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload

from app import recorrencias
from app.auth import require_permission
from app.database import get_db
from app.models import PerfilUsuario, Recorrencia, Usuario
from app.schemas import RecorrenciaAlterar, RecorrenciaCreate, RecorrenciaEncerrar, RecorrenciaRead

router = APIRouter(prefix="/api/recorrencias", tags=["recorrencias"])


def serializar(regra):
    return RecorrenciaRead(id=regra.id, paciente_id=regra.paciente_id, psicologo_id=regra.psicologo_id,
                          paciente_nome=regra.paciente.nome, psicologo_nome=regra.psicologo.nome,
                          inicio=regra.inicio, duracao_minutos=regra.duracao_minutos,
                          intervalo_dias=regra.intervalo_dias, encerrada_em=regra.encerrada_em,
                          motivo_encerramento=regra.motivo_encerramento, anterior_id=regra.anterior_id)


@router.get("", response_model=list[RecorrenciaRead])
def listar(db: Session = Depends(get_db), usuario: Usuario = Depends(require_permission("agenda:consultar"))):
    query = db.query(Recorrencia).options(joinedload(Recorrencia.paciente), joinedload(Recorrencia.psicologo))
    if usuario.perfil == PerfilUsuario.psicologo:
        if not usuario.psicologo_id:
            raise HTTPException(403, "Profissional sem vínculo cadastrado.")
        query = query.filter(Recorrencia.psicologo_id == usuario.psicologo_id)
    return [serializar(r) for r in query.order_by(Recorrencia.inicio).all()]


@router.post("", response_model=RecorrenciaRead, status_code=201)
def criar(payload: RecorrenciaCreate, db: Session = Depends(get_db),
          usuario: Usuario = Depends(require_permission("agenda:gerenciar"))):
    return serializar(recorrencias.criar(db, payload, usuario))


@router.post("/gerar")
def gerar(db: Session = Depends(get_db), usuario: Usuario = Depends(require_permission("agenda:gerenciar"))):
    return {"sessoes_criadas": recorrencias.gerar_proximas(db, usuario), "horizonte_dias": recorrencias.HORIZONTE_DIAS}


@router.post("/{regra_id}/encerrar", response_model=RecorrenciaRead)
def encerrar(regra_id: int, payload: RecorrenciaEncerrar, db: Session = Depends(get_db),
             usuario: Usuario = Depends(require_permission("agenda:gerenciar"))):
    return serializar(recorrencias.encerrar(db, regra_id, payload, usuario))


@router.post("/{regra_id}/alterar", response_model=RecorrenciaRead)
def alterar(regra_id: int, payload: RecorrenciaAlterar, db: Session = Depends(get_db),
            usuario: Usuario = Depends(require_permission("agenda:gerenciar"))):
    return serializar(recorrencias.alterar(db, regra_id, payload, usuario))
