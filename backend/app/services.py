"""
Regras de negócio compartilhadas (valores de sessão e lançamentos automáticos).

Quando um agendamento passa para status 'realizado', geramos lançamentos de
receita e repasse conforme tipo de atendimento do paciente e % do psicólogo.
"""

from fastapi import HTTPException
from sqlalchemy import String, and_, cast
from sqlalchemy.orm import Session

from app.auth import has_permission
from app import horarios

from app.models import (
    VALOR_CONVENIO,
    VALOR_PARTICULAR,
    Agendamento,
    EstornoFinanceiro,
    LancamentoFinanceiro,
    Paciente,
    PerfilUsuario,
    Psicologo,
    Prontuario,
    Reagendamento,
    StatusAgendamento,
    TipoAtendimento,
    TipoLancamento,
    Usuario,
)
from app.transacoes import bloquear_agendamento, transacao
from app.validacao_agenda import CAMPOS_DA_RESERVA, STATUS_QUE_OCUPAM_HORARIO, normalizar_horarios, validar_reserva


TRANSICOES_AGENDAMENTO = {
    StatusAgendamento.agendado: set(StatusAgendamento),
    StatusAgendamento.confirmado: set(StatusAgendamento),
    StatusAgendamento.realizado: {StatusAgendamento.realizado, StatusAgendamento.cancelado},
    StatusAgendamento.cancelado: {StatusAgendamento.cancelado, StatusAgendamento.agendado},
    StatusAgendamento.falta: {StatusAgendamento.falta, StatusAgendamento.agendado},
}


def filtro_parcela_clinica_legada():
    """Identifica apenas a receita duplicada criada pelo gerador antigo."""
    return and_(
        LancamentoFinanceiro.tipo == TipoLancamento.receita,
        LancamentoFinanceiro.automatico.is_(True),
        LancamentoFinanceiro.psicologo_id.is_(None),
        LancamentoFinanceiro.agendamento_id.is_not(None),
        LancamentoFinanceiro.descricao == (
            "Receita clinica sessao #" + cast(LancamentoFinanceiro.agendamento_id, String)
        ),
    )


def validar_alteracao_agendamento(
    db: Session, agendamento: Agendamento, novo_status: StatusAgendamento,
    alteracoes: dict, usuario: Usuario | None = None, motivo: str | None = None,
) -> None:
    """Recusa transições e alterações históricas antes de modificar o atendimento."""
    if novo_status not in TRANSICOES_AGENDAMENTO[agendamento.status]:
        raise HTTPException(status_code=409, detail="Transição de status não permitida. Reabra como agendado quando disponível.")
    tem_prontuario = db.query(Prontuario.id).filter(Prontuario.agendamento_id == agendamento.id).first() is not None
    tem_financeiro = db.query(LancamentoFinanceiro.id).filter(
        LancamentoFinanceiro.agendamento_id == agendamento.id,
        LancamentoFinanceiro.automatico.is_(True),
    ).first() is not None
    campos_historicos = {"paciente_id", "psicologo_id", "inicio", "fim"}
    mudou_vinculo = any(
        campo in alteracoes and alteracoes[campo] != getattr(agendamento, campo)
        for campo in campos_historicos
    )
    if (mudou_vinculo or novo_status != agendamento.status) and db.query(Reagendamento.id).filter(
        Reagendamento.agendamento_original_id == agendamento.id
    ).first():
        raise HTTPException(status_code=409, detail="Este atendimento já foi reagendado. Utilize o novo agendamento.")
    if mudou_vinculo and (agendamento.status == StatusAgendamento.realizado or tem_prontuario or tem_financeiro):
        raise HTTPException(status_code=409, detail="Paciente, profissional e horários de atendimento com histórico não podem ser alterados.")
    if novo_status == agendamento.status:
        return
    if tem_prontuario:
        raise HTTPException(status_code=409, detail="Atendimento com evolução clínica não pode mudar de status. O prontuário deve ser preservado.")
    if tem_financeiro and agendamento.status != StatusAgendamento.realizado:
        raise HTTPException(status_code=409, detail="Atendimento com histórico financeiro não pode ser reaberto. Crie um novo agendamento.")
    if agendamento.status == StatusAgendamento.realizado:
        if usuario is None or not has_permission(usuario, "financeiro:gerenciar"):
            raise HTTPException(status_code=403, detail="Cancelar atendimento realizado exige permissão para gerenciar o financeiro.")
        if not motivo or not motivo.strip() or len(motivo.strip()) > 500:
            raise HTTPException(status_code=422, detail="Informe o motivo do cancelamento, com até 500 caracteres.")


def _preparar_estornos(db: Session, agendamento: Agendamento, usuario: Usuario, motivo: str) -> None:
    """Adiciona compensações exatas na transação do cancelamento."""
    originais = db.query(LancamentoFinanceiro).filter(
        LancamentoFinanceiro.agendamento_id == agendamento.id,
        LancamentoFinanceiro.automatico.is_(True),
        ~filtro_parcela_clinica_legada(),
    ).all()
    if (
        len(originais) != 2
        or {l.tipo for l in originais} != {TipoLancamento.receita, TipoLancamento.repasse}
        or any(l.psicologo_id != agendamento.psicologo_id or l.valor < 0 for l in originais)
        or db.query(EstornoFinanceiro.id).filter(
            EstornoFinanceiro.lancamento_original_id.in_([l.id for l in originais])
        ).first()
    ):
        raise HTTPException(status_code=409, detail="Histórico financeiro inconsistente. Revise os lançamentos antes de cancelar.")
    for original in originais:
        compensacao = LancamentoFinanceiro(
            agendamento_id=agendamento.id, psicologo_id=original.psicologo_id,
            descricao=f"Estorno do lançamento #{original.id} - atendimento #{agendamento.id}",
            tipo=original.tipo, valor=-original.valor, automatico=True,
            chave_automatica=f"estorno:{original.id}",
        )
        db.add(compensacao)
        db.flush()
        db.add(EstornoFinanceiro(
            lancamento_original_id=original.id, lancamento_estorno_id=compensacao.id,
            usuario_id=usuario.id, motivo=motivo.strip(),
        ))


def valor_sessao_paciente(paciente: Paciente) -> float:
    """Tabela simplificada do protótipo (produção: tabela por convênio/plano)."""
    if paciente.tipo_atendimento == TipoAtendimento.convenio:
        return VALOR_CONVENIO
    return VALOR_PARTICULAR


def criar_lancamentos_agendamento_realizado(db: Session, agendamento: Agendamento) -> None:
    """Prepara o par original, sem commit; exige atendimento travado ou recém-inserido.

    A transação chamadora grava status e lançamentos juntos. O índice único
    protege as chaves mesmo entre processos; histórico incompleto exige revisão.
    """
    if agendamento.status != StatusAgendamento.realizado:
        raise HTTPException(status_code=409, detail="Só atendimentos realizados podem gerar faturamento.")
    existentes = (
        db.query(LancamentoFinanceiro)
        .filter(
            LancamentoFinanceiro.agendamento_id == agendamento.id,
            LancamentoFinanceiro.automatico.is_(True),
            ~filtro_parcela_clinica_legada(),
        )
        .all()
    )
    if existentes:
        if (
            len(existentes) != 2
            or {l.tipo for l in existentes} != {TipoLancamento.receita, TipoLancamento.repasse}
            or any(l.psicologo_id != agendamento.psicologo_id or l.valor < 0 for l in existentes)
        ):
            raise HTTPException(status_code=409, detail="Histórico financeiro inconsistente. Revise os lançamentos antes de realizar.")
        return

    paciente = db.get(Paciente, agendamento.paciente_id)
    psicologo = db.get(Psicologo, agendamento.psicologo_id)
    if not paciente or not psicologo:
        raise HTTPException(status_code=422, detail="Paciente ou profissional não encontrado.")

    valor_bruto = valor_sessao_paciente(paciente)
    repasse = round(valor_bruto * (psicologo.percentual_repasse / 100.0), 2)

    db.add(
        LancamentoFinanceiro(
            agendamento_id=agendamento.id,
            psicologo_id=psicologo.id,
            descricao=f"Receita sessao #{agendamento.id} - {paciente.nome}",
            tipo=TipoLancamento.receita,
            valor=valor_bruto,
            automatico=True,
            chave_automatica="receita",
        )
    )
    db.add(
        LancamentoFinanceiro(
            agendamento_id=agendamento.id,
            psicologo_id=psicologo.id,
            descricao=f"Repasse psicologo #{agendamento.id} - {psicologo.nome}",
            tipo=TipoLancamento.repasse,
            valor=repasse,
            automatico=True,
            chave_automatica="repasse",
        )
    )
    # A parcela da clínica é receita bruta menos repasse, não outra receita.


def aplicar_status_agendamento(
    db: Session, agendamento: Agendamento | int, novo_status: StatusAgendamento | None,
    usuario: Usuario | None = None, motivo: str | None = None,
    alteracoes: dict | None = None,
) -> Agendamento:
    alteracoes = alteracoes or {}
    agendamento_id = agendamento if isinstance(agendamento, int) else agendamento.id
    with transacao(db):
        agendamento = bloquear_agendamento(db, agendamento_id)
        alteracoes = normalizar_horarios(alteracoes)
        # Autorizar após a releitura: o profissional pode ter mudado enquanto
        # outra operação aguardava a trava, inclusive em outra sessão/worker.
        if usuario and usuario.perfil == PerfilUsuario.psicologo and usuario.psicologo_id != agendamento.psicologo_id:
            raise HTTPException(status_code=403, detail="Acesso negado a este atendimento.")
        status_solicitado = novo_status
        novo_status = novo_status or agendamento.status
        validar_alteracao_agendamento(db, agendamento, novo_status, alteracoes, usuario, motivo)
        mudou_reserva = any(
            campo in alteracoes and alteracoes[campo] != getattr(agendamento, campo)
            for campo in CAMPOS_DA_RESERVA
        )
        from app.recorrencias import vinculo_da_sessao
        vinculo_recorrente = vinculo_da_sessao(db, agendamento)
        if vinculo_recorrente:
            regra = vinculo_recorrente.recorrencia
            db.refresh(regra)
            if mudou_reserva:
                raise HTTPException(409, detail="Use Reagendar para mudar somente esta sessão ou Alterar próximas sessões para mudar a sequência.")
            if (novo_status in {StatusAgendamento.agendado, StatusAgendamento.confirmado}
                    and regra.encerrada_em is not None and agendamento.inicio >= regra.encerrada_em):
                raise HTTPException(409, detail="Esta sessão pertence ao período encerrado da recorrência. Crie outro agendamento.")
        volta_a_agenda = status_solicitado in {StatusAgendamento.agendado, StatusAgendamento.confirmado}
        if (mudou_reserva or volta_a_agenda) and agendamento.inicio <= horarios.agora_utc():
            raise HTTPException(status_code=409, detail="Horário vencido. Use Reagendar para criar um novo atendimento futuro.")
        if mudou_reserva or (novo_status != agendamento.status and novo_status in STATUS_QUE_OCUPAM_HORARIO):
            reserva = {campo: alteracoes.get(campo, getattr(agendamento, campo)) for campo in CAMPOS_DA_RESERVA}
            validar_reserva(db, **reserva, status=novo_status, ignorar_agendamento_id=agendamento.id,
                            exigir_futuro=mudou_reserva or volta_a_agenda)
        if agendamento.status == StatusAgendamento.realizado and novo_status == StatusAgendamento.cancelado:
            _preparar_estornos(db, agendamento, usuario, motivo)
        for campo, valor in alteracoes.items():
            setattr(agendamento, campo, valor)
        agendamento.status = novo_status
        db.add(agendamento)
        db.flush()
        if novo_status == StatusAgendamento.realizado:
            criar_lancamentos_agendamento_realizado(db, agendamento)
    db.refresh(agendamento)
    return agendamento


def reagendar_atendimento(db: Session, agendamento_id: int, inicio, fim, usuario: Usuario) -> Agendamento:
    """Cria sucessor futuro e vínculo auditável sem sobrescrever a reserva antiga."""
    with transacao(db):
        original = bloquear_agendamento(db, agendamento_id)
        if usuario.perfil == PerfilUsuario.psicologo and usuario.psicologo_id != original.psicologo_id:
            raise HTTPException(status_code=403, detail="Acesso negado a este atendimento.")
        if original.status == StatusAgendamento.realizado or original.prontuario or any(l.automatico for l in original.lancamentos):
            raise HTTPException(status_code=409, detail="Atendimento com histórico clínico ou financeiro não pode ser reagendado por este fluxo.")
        if original.reagendamento:
            raise HTTPException(status_code=409, detail="Este atendimento já foi reagendado. Utilize o novo agendamento.")
        dados = normalizar_horarios(dict(inicio=inicio, fim=fim))
        validar_reserva(db, original.paciente_id, original.psicologo_id, **dados,
                        status=StatusAgendamento.agendado, ignorar_agendamento_id=original.id, exigir_futuro=True)
        from app.recorrencias import vinculo_da_sessao
        vinculo = vinculo_da_sessao(db, original)
        if vinculo:
            regra = vinculo.recorrencia
            db.refresh(regra)
            if regra.encerrada_em is not None and dados["inicio"] >= regra.encerrada_em:
                raise HTTPException(status_code=409, detail="A recorrência está encerrada nesse período. Crie um novo agendamento avulso, se necessário.")
        novo = Agendamento(paciente_id=original.paciente_id, psicologo_id=original.psicologo_id,
                            **dados, status=StatusAgendamento.agendado, observacoes=original.observacoes)
        # Uma falta permanece como falta. Reservas abertas são canceladas.
        if original.status in {StatusAgendamento.agendado, StatusAgendamento.confirmado}:
            original.status = StatusAgendamento.cancelado
        db.add(novo)
        db.flush()
        db.add(Reagendamento(agendamento_original_id=original.id, novo_agendamento_id=novo.id,
                             usuario_id=usuario.id, criado_em=horarios.agora_utc()))
    db.refresh(novo)
    return novo
