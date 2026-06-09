"""
Regras de negócio compartilhadas (valores de sessão e lançamentos automáticos).

Quando um agendamento passa para status 'realizado', geramos lançamentos de
receita e repasse conforme tipo de atendimento do paciente e % do psicólogo.
"""

from sqlalchemy.orm import Session

from app.models import (
    VALOR_CONVENIO,
    VALOR_PARTICULAR,
    Agendamento,
    LancamentoFinanceiro,
    Paciente,
    Psicologo,
    StatusAgendamento,
    TipoAtendimento,
    TipoLancamento,
)


def valor_sessao_paciente(paciente: Paciente) -> float:
    """Tabela simplificada do protótipo (produção: tabela por convênio/plano)."""
    if paciente.tipo_atendimento == TipoAtendimento.convenio:
        return VALOR_CONVENIO
    return VALOR_PARTICULAR


def criar_lancamentos_agendamento_realizado(db: Session, agendamento: Agendamento) -> None:
    """Idempotente: não duplica lançamentos automáticos do mesmo agendamento."""
    existente = (
        db.query(LancamentoFinanceiro)
        .filter(
            LancamentoFinanceiro.agendamento_id == agendamento.id,
            LancamentoFinanceiro.automatico.is_(True),
        )
        .first()
    )
    if existente:
        return

    paciente = agendamento.paciente or db.get(Paciente, agendamento.paciente_id)
    psicologo = agendamento.psicologo or db.get(Psicologo, agendamento.psicologo_id)
    if not paciente or not psicologo:
        return

    valor_bruto = valor_sessao_paciente(paciente)
    repasse = round(valor_bruto * (psicologo.percentual_repasse / 100.0), 2)
    clinica = round(valor_bruto - repasse, 2)

    db.add(
        LancamentoFinanceiro(
            agendamento_id=agendamento.id,
            psicologo_id=psicologo.id,
            descricao=f"Receita sessao #{agendamento.id} - {paciente.nome}",
            tipo=TipoLancamento.receita,
            valor=valor_bruto,
            automatico=True,
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
        )
    )
    if clinica > 0:
        db.add(
            LancamentoFinanceiro(
                agendamento_id=agendamento.id,
                psicologo_id=None,
                descricao=f"Receita clinica sessao #{agendamento.id}",
                tipo=TipoLancamento.receita,
                valor=clinica,
                automatico=True,
            )
        )
    db.commit()


def aplicar_status_agendamento(db: Session, agendamento: Agendamento, novo_status: StatusAgendamento) -> None:
    agendamento.status = novo_status
    db.add(agendamento)
    db.commit()
    db.refresh(agendamento)
    if novo_status == StatusAgendamento.realizado:
        criar_lancamentos_agendamento_realizado(db, agendamento)
