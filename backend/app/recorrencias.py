"""Reservas recorrentes em Brasília, materialização idempotente e versões auditáveis."""
from datetime import timedelta
from zoneinfo import ZoneInfo

from fastapi import HTTPException
from sqlalchemy import or_, update
from sqlalchemy.orm import Session

from app import horarios
from app.models import (Agendamento, OcorrenciaRecorrencia, Paciente, Psicologo,
                        PerfilUsuario, Reagendamento, Recorrencia, StatusAgendamento, Usuario)
from app.transacoes import transacao
from app.validacao_agenda import STATUS_QUE_OCUPAM_HORARIO, validar_reserva
from app.escopo import validar_paciente

FUSO = ZoneInfo("America/Sao_Paulo")
HORIZONTE_DIAS = 90


def vinculo_da_sessao(db, agendamento):
    """Reagendamentos pontuais continuam pertencendo à reserva do tratamento."""
    if agendamento.ocorrencia:
        return agendamento.ocorrencia
    visitados = set()
    ident = agendamento.id
    while ident not in visitados:
        visitados.add(ident)
        ident = db.query(Reagendamento.agendamento_original_id).filter_by(novo_agendamento_id=ident).scalar()
        if ident is None:
            return None
        vinculo = db.query(OcorrenciaRecorrencia).filter_by(agendamento_id=ident).first()
        if vinculo:
            return vinculo
    raise HTTPException(409, "Histórico de reagendamento inconsistente. Revise os vínculos.")


def local(instante):
    return horarios.utc_com_fuso(instante).astimezone(FUSO)


def ocorrencias(regra, de, ate):
    """Ocorrências que podem tocar a janela, sem percorrer todo o tratamento."""
    ancora = local(regra.inicio)
    passo = timedelta(days=regra.intervalo_dias)
    # Inclui a véspera: duração recorrente limitada a 24h.
    indice = max(0, ((local(de).date() - ancora.date()).days - 1) // regra.intervalo_dias)
    while True:
        try:
            inicio = horarios.utc_sem_fuso(ancora + indice * passo)
            fim = inicio + timedelta(minutes=regra.duracao_minutos)
        except (OverflowError, ValueError):
            return
        if inicio >= ate or (regra.encerrada_em is not None and inicio >= regra.encerrada_em):
            return
        if fim > de:
            yield inicio, fim
        indice += 1


def excecoes(db, regra_id):
    return {inicio for inicio, in db.query(OcorrenciaRecorrencia.inicio_original)
            .join(Agendamento).filter(OcorrenciaRecorrencia.recorrencia_id == regra_id,
                                     Agendamento.status.in_([StatusAgendamento.cancelado, StatusAgendamento.falta])).all()}


def regras_do_recurso(db, paciente_id, psicologo_id):
    return db.query(Recorrencia).filter(or_(Recorrencia.paciente_id == paciente_id,
                                          Recorrencia.psicologo_id == psicologo_id)).all()


def validar_conflito_recorrencias(db, paciente_id, psicologo_id, inicio, fim,
                                  ignorar_agendamento_id=None, ignorar_recorrencia_id=None):
    propria = db.query(OcorrenciaRecorrencia).filter_by(agendamento_id=ignorar_agendamento_id).first() if ignorar_agendamento_id else None
    for regra in regras_do_recurso(db, paciente_id, psicologo_id):
        if regra.id == ignorar_recorrencia_id:
            continue
        livres = excecoes(db, regra.id)
        for reservado, final in ocorrencias(regra, inicio, fim):
            if propria and propria.recorrencia_id == regra.id and propria.inicio_original == reservado:
                continue
            if reservado not in livres and reservado < fim and final > inicio:
                recurso = "profissional" if regra.psicologo_id == psicologo_id else "paciente"
                raise HTTPException(409, f"O {recurso} possui horário reservado por uma recorrência.")


def autorizar(usuario: Usuario, psicologo_id):
    if usuario.perfil == PerfilUsuario.psicologo and (not usuario.psicologo_id or usuario.psicologo_id != psicologo_id):
        raise HTTPException(403, "Acesso negado à recorrência deste profissional.")


def bloquear_regra(db, regra_id, usuario):
    with db.no_autoflush:
        existe = db.execute(update(Recorrencia).where(Recorrencia.id == regra_id)
                            .values(id=Recorrencia.id).execution_options(synchronize_session=False))
        if existe.rowcount != 1:
            raise HTTPException(404, "Recorrência não encontrada.")
        regra = db.get(Recorrencia, regra_id, populate_existing=True)
        autorizar(usuario, regra.psicologo_id)
        return regra


def validar_regra(db, regra):
    """Valida todo o futuro, inclusive contra reservas ainda não materializadas."""
    validar_reserva(db, regra.paciente_id, regra.psicologo_id, regra.inicio,
                    regra.inicio + timedelta(minutes=regra.duracao_minutos), StatusAgendamento.agendado,
                    exigir_futuro=True)
    # Sessões avulsas e já geradas, em qualquer data futura.
    reservas = db.query(Agendamento).filter(
        Agendamento.status.in_(STATUS_QUE_OCUPAM_HORARIO), Agendamento.fim > regra.inicio,
        or_(Agendamento.paciente_id == regra.paciente_id, Agendamento.psicologo_id == regra.psicologo_id)).all()
    for ag in reservas:
        if any(i < ag.fim and f > ag.inicio for i, f in ocorrencias(regra, ag.inicio, ag.fim)):
            raise HTTPException(409, "A sequência conflita com um atendimento já agendado. Nenhuma sessão foi criada.")
    for outra in regras_do_recurso(db, regra.paciente_id, regra.psicologo_id):
        de = max(regra.inicio, outra.inicio)
        livres = excecoes(db, outra.id)
        # Ambas repetem em ciclo de 14 dias. Após a última exceção finita,
        # dois ciclos bastam para verificar a fase, mesmo sem término.
        ate = max([de, *livres]) + timedelta(days=29)
        if outra.encerrada_em is not None:
            ate = min(ate, outra.encerrada_em + timedelta(days=1))
        for i, f in ocorrencias(regra, de - timedelta(days=1), ate):
            if any(j not in livres and i < g and f > j for j, g in ocorrencias(outra, i, f)):
                raise HTTPException(409, "A sequência conflita com outra recorrência do profissional ou paciente.")


def preparar_regra(paciente_id, psicologo_id, inicio, fim, intervalo_dias, usuario, anterior_id=None):
    inicio, fim = horarios.utc_sem_fuso(inicio), horarios.utc_sem_fuso(fim)
    segundos = (fim - inicio).total_seconds()
    if intervalo_dias not in (7, 14) or segundos <= 0 or segundos > 86400 or segundos % 60:
        raise HTTPException(422, "Use frequência semanal ou quinzenal e duração entre 1 minuto e 24 horas, em minutos inteiros.")
    autorizar(usuario, psicologo_id)
    return Recorrencia(paciente_id=paciente_id, psicologo_id=psicologo_id, inicio=inicio,
                       duracao_minutos=int(segundos // 60), intervalo_dias=intervalo_dias,
                       usuario_id=usuario.id, anterior_id=anterior_id, criado_em=horarios.agora_utc())


def materializar(db, regra, ate):
    """Chamador mantém trava da regra/recursos; nunca fatura nem recria exceções."""
    # Cadastro inativo não expande a agenda, mas não apaga a reserva existente.
    if not db.query(Paciente.ativo).filter_by(id=regra.paciente_id).scalar() or not db.query(Psicologo.ativo).filter_by(id=regra.psicologo_id).scalar():
        return 0
    validar_reserva(db, regra.paciente_id, regra.psicologo_id, regra.inicio,
                    regra.inicio + timedelta(minutes=regra.duracao_minutos), StatusAgendamento.cancelado)
    existentes = {i for i, in db.query(OcorrenciaRecorrencia.inicio_original).filter_by(recorrencia_id=regra.id)}
    criadas = 0
    for inicio, fim in ocorrencias(regra, horarios.agora_utc(), ate):
        if inicio <= horarios.agora_utc() or inicio in existentes:
            continue
        validar_reserva(db, regra.paciente_id, regra.psicologo_id, inicio, fim, StatusAgendamento.agendado,
                        exigir_futuro=True, ignorar_recorrencia_id=regra.id)
        ag = Agendamento(paciente_id=regra.paciente_id, psicologo_id=regra.psicologo_id,
                         inicio=inicio, fim=fim, status=StatusAgendamento.agendado)
        db.add(ag)
        db.flush()
        db.add(OcorrenciaRecorrencia(recorrencia_id=regra.id, inicio_original=inicio, agendamento_id=ag.id))
        db.flush()
        criadas += 1
    return criadas


def criar(db, payload, usuario):
    regra = preparar_regra(payload.paciente_id, payload.psicologo_id, payload.inicio, payload.fim,
                           payload.intervalo_dias, usuario)
    with transacao(db):
        validar_regra(db, regra)
        if usuario.perfil == PerfilUsuario.psicologo:
            validar_paciente(db, usuario, regra.paciente_id)
        db.add(regra)
        db.flush()
        materializar(db, regra, max(regra.inicio, horarios.agora_utc()) + timedelta(days=HORIZONTE_DIAS))
    return regra


def encerrar_na_transacao(db, regra, a_partir_de, motivo, usuario):
    agora = horarios.agora_utc()
    corte = horarios.utc_sem_fuso(a_partir_de) if a_partir_de is not None else agora
    if corte < agora:
        raise HTTPException(422, "O encerramento deve ocorrer agora ou em uma data futura.")
    if regra.encerrada_em is not None:
        raise HTTPException(409, "Esta recorrência já foi encerrada ou substituída.")
    # Mesmas travas dos recursos, antes de reler sessões e alterar a reserva.
    for modelo, ident in ((Psicologo, regra.psicologo_id), (Paciente, regra.paciente_id)):
        db.execute(update(modelo).where(modelo.id == ident).values(ativo=modelo.ativo)
                   .execution_options(synchronize_session=False))
    ids = [ident for ident, in db.query(OcorrenciaRecorrencia.agendamento_id)
           .filter(OcorrenciaRecorrencia.recorrencia_id == regra.id)]
    todos = set(ids)
    fronteira = ids
    while fronteira:
        descendentes = {ident for ident, in db.query(Reagendamento.novo_agendamento_id)
                        .filter(Reagendamento.agendamento_original_id.in_(fronteira))} - todos
        todos.update(descendentes)
        fronteira = list(descendentes)
    from app.transacoes import bloquear_agendamento
    for ident in sorted(todos):
        ag = bloquear_agendamento(db, ident)
        if ag.inicio < corte:
            continue
        if ag.status == StatusAgendamento.realizado or ag.prontuario or ag.lancamentos:
            raise HTTPException(409, "Há sessão com histórico no período afetado. Escolha uma data posterior a ela.")
        if ag.status in {StatusAgendamento.agendado, StatusAgendamento.confirmado}:
            ag.status = StatusAgendamento.cancelado
    regra.encerrada_em = corte
    regra.motivo_encerramento = motivo.strip()
    regra.encerrada_por_id = usuario.id
    db.flush()


def encerrar(db, regra_id, payload, usuario):
    with transacao(db):
        regra = bloquear_regra(db, regra_id, usuario)
        encerrar_na_transacao(db, regra, payload.a_partir_de, payload.motivo, usuario)
    return regra


def alterar(db, regra_id, payload, usuario):
    with transacao(db):
        antiga = bloquear_regra(db, regra_id, usuario)
        corte = horarios.utc_sem_fuso(payload.a_partir_de)
        nova = preparar_regra(antiga.paciente_id, antiga.psicologo_id, payload.inicio, payload.fim,
                              payload.intervalo_dias, usuario, antiga.id)
        if nova.inicio < corte:
            raise HTTPException(422, "A nova primeira sessão deve ocorrer a partir da data da alteração.")
        encerrar_na_transacao(db, antiga, corte, payload.motivo, usuario)
        validar_regra(db, nova)
        db.add(nova)
        db.flush()
        materializar(db, nova, max(nova.inicio, horarios.agora_utc()) + timedelta(days=HORIZONTE_DIAS))
    return nova


def gerar_proximas(db, usuario):
    query = db.query(Recorrencia.id).filter(or_(Recorrencia.encerrada_em.is_(None),
                                              Recorrencia.encerrada_em > horarios.agora_utc()))
    if usuario.perfil == PerfilUsuario.psicologo:
        autorizar(usuario, usuario.psicologo_id)
        query = query.filter(Recorrencia.psicologo_id == usuario.psicologo_id)
    ids = [ident for ident, in query.order_by(Recorrencia.id)]
    total = 0
    with transacao(db):
        for ident in ids:
            regra = bloquear_regra(db, ident, usuario)
            total += materializar(db, regra, horarios.agora_utc() + timedelta(days=HORIZONTE_DIAS))
    return total
