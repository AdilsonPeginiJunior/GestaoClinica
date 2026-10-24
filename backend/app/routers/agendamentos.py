"""
Endpoints de agendamento — nucleo operacional da recepcao.

Ao mudar status para 'realizado', services.aplicar_status_agendamento
dispara lancamentos financeiros automaticos.
"""

from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session, joinedload, selectinload, object_session

from app.auth import require_permission
from app import horarios, services
from app.database import get_db
from app.models import Agendamento, PerfilUsuario, StatusAgendamento, Usuario
from app.schemas import AgendamentoCreate, AgendamentoRead, AgendamentoUpdate, ReagendamentoCreate, RelogioAgendaRead
from app.services import aplicar_status_agendamento
from app.transacoes import transacao
from app.validacao_agenda import normalizar_horarios, validar_reserva
from app.horarios import utc_sem_fuso
from app.escopo import validar_paciente

router = APIRouter(prefix="/api/agendamentos", tags=["agendamentos"])


@router.get("/relogio", response_model=RelogioAgendaRead)
def relogio_agenda(_: Usuario = Depends(require_permission("agenda:consultar"))):
    """Referência temporal UTC para validação/exibição da agenda em Brasília."""
    return RelogioAgendaRead(agora=horarios.utc_com_fuso(horarios.agora_utc()))


def _serialize(ag: Agendamento) -> AgendamentoRead:
    from app.recorrencias import vinculo_da_sessao
    vinculo = ag.ocorrencia or vinculo_da_sessao(object_session(ag), ag)
    tem_financeiro = any(l.automatico for l in ag.lancamentos)
    sem_historico = not tem_financeiro and ag.prontuario is None and ag.reagendamento is None
    fora_da_serie = (vinculo is not None and vinculo.recorrencia.encerrada_em is not None
                    and ag.inicio >= vinculo.recorrencia.encerrada_em)
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
        possui_historico_financeiro=tem_financeiro,
        pode_reabrir=sem_historico and not fora_da_serie and ag.inicio > horarios.agora_utc() and ag.status in {
            StatusAgendamento.cancelado, StatusAgendamento.falta, StatusAgendamento.confirmado,
        },
        pode_reagendar=sem_historico and not fora_da_serie and ag.status != StatusAgendamento.realizado,
        reagendado_de_id=ag.origem_reagendamento.agendamento_original_id if ag.origem_reagendamento else None,
        reagendado_para_id=ag.reagendamento.novo_agendamento_id if ag.reagendamento else None,
        recorrencia_id=vinculo.recorrencia_id if vinculo else None,
    )


@router.get("", response_model=list[AgendamentoRead])
def listar_agendamentos(
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_permission("agenda:consultar")),
    data_inicio: datetime | None = Query(None),
    data_fim: datetime | None = Query(None),
    psicologo_id: int | None = Query(None),
    status_filtro: StatusAgendamento | None = Query(None, alias="status"),
):
    query = db.query(Agendamento).options(
        joinedload(Agendamento.paciente), joinedload(Agendamento.psicologo),
        selectinload(Agendamento.lancamentos),
        selectinload(Agendamento.prontuario), selectinload(Agendamento.reagendamento),
        selectinload(Agendamento.origem_reagendamento),
        selectinload(Agendamento.ocorrencia),
    )
    if current_user.perfil == PerfilUsuario.psicologo:
        if not current_user.psicologo_id:
            raise HTTPException(403, "Profissional sem vínculo cadastrado.")
        query = query.filter(Agendamento.psicologo_id == current_user.psicologo_id)
    elif psicologo_id is not None:
        query = query.filter(Agendamento.psicologo_id == psicologo_id)
    if data_inicio:
        query = query.filter(Agendamento.inicio >= utc_sem_fuso(data_inicio))
    if data_fim:
        query = query.filter(Agendamento.inicio <= utc_sem_fuso(data_fim))
    if status_filtro:
        query = query.filter(Agendamento.status == status_filtro)
    items = query.order_by(Agendamento.inicio).all()
    return [_serialize(a) for a in items]


@router.post("", response_model=AgendamentoRead, status_code=status.HTTP_201_CREATED)
def criar_agendamento(
    payload: AgendamentoCreate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_permission("agenda:gerenciar")),
):
    if (
        current_user.perfil == PerfilUsuario.psicologo
        and current_user.psicologo_id != payload.psicologo_id
    ):
        raise HTTPException(status_code=403, detail="Acesso negado")
    ag = Agendamento(**normalizar_horarios(payload.model_dump()))
    with transacao(db):
        validar_reserva(db, ag.paciente_id, ag.psicologo_id, ag.inicio, ag.fim, ag.status, exigir_futuro=True)
        if current_user.perfil == PerfilUsuario.psicologo:
            validar_paciente(db, current_user, ag.paciente_id)
        db.add(ag)
        db.flush()
        if ag.status == StatusAgendamento.realizado:
            # A inserção mantém a trava até o commit de todo o atendimento.
            services.criar_lancamentos_agendamento_realizado(db, ag)
    db.refresh(ag)
    ag = (
        db.query(Agendamento)
        .options(joinedload(Agendamento.paciente), joinedload(Agendamento.psicologo),
                 selectinload(Agendamento.lancamentos))
        .filter(Agendamento.id == ag.id)
        .first()
    )
    return _serialize(ag)


@router.post("/{agendamento_id}/reagendar", response_model=AgendamentoRead, status_code=status.HTTP_201_CREATED)
def reagendar_agendamento(
    agendamento_id: int, payload: ReagendamentoCreate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_permission("agenda:gerenciar")),
):
    novo = services.reagendar_atendimento(db, agendamento_id, payload.inicio, payload.fim, current_user)
    return _serialize(novo)


@router.patch("/{agendamento_id}", response_model=AgendamentoRead)
def atualizar_agendamento(
    agendamento_id: int,
    payload: AgendamentoUpdate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_permission("agenda:gerenciar")),
):
    data = payload.model_dump(exclude_unset=True)
    if current_user.perfil == PerfilUsuario.psicologo and set(data) - {"status", "motivo_cancelamento"}:
        raise HTTPException(status_code=403, detail="Psicologos so podem atualizar o status do proprio atendimento.")
    if "status" in data and data["status"] is None:
        raise HTTPException(status_code=422, detail="Status não pode ser nulo.")
    novo_status = data.pop("status", None)
    motivo = data.pop("motivo_cancelamento", None)
    if any(
        data.get(campo, True) is None
        for campo in ("paciente_id", "psicologo_id", "inicio", "fim")
    ):
        raise HTTPException(status_code=422, detail="Status, paciente, profissional e horários não podem ser nulos.")
    ag = aplicar_status_agendamento(db, agendamento_id, novo_status, usuario=current_user, motivo=motivo, alteracoes=data)

    return _serialize(ag)
