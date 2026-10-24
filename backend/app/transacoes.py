"""Transações e bloqueio compartilhado das alterações de um atendimento."""

from contextlib import contextmanager

from fastapi import HTTPException
from sqlalchemy import update
from sqlalchemy.exc import IntegrityError, OperationalError
from sqlalchemy.orm import Session

from app.models import Agendamento


@contextmanager
def transacao(db: Session):
    """Confirma uma unidade de trabalho ou desfaz todos os seus efeitos."""
    try:
        yield
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=409, detail="Conflito de integridade. Atualize os dados antes de tentar novamente.") from exc
    except OperationalError as exc:
        db.rollback()
        codigo = getattr(exc.orig, "sqlstate", None) or getattr(exc.orig, "pgcode", None)
        codigo_sqlite = getattr(exc.orig, "sqlite_errorcode", 0)
        if (codigo_sqlite & 0xFF) in {5, 6} or codigo in {"40001", "40P01", "55P03"}:
            raise HTTPException(status_code=409, detail="Atendimento em atualização. Aguarde e tente novamente.") from exc
        raise
    except Exception:
        db.rollback()
        raise


def bloquear_agendamento(db: Session, agendamento_id: int) -> Agendamento:
    """Obtém trava no banco antes de reler e validar o estado atual.

    UPDATE sem alteração de valor: trava de escrita no SQLite e da linha no
    PostgreSQL. A trava dura até commit/rollback da transação chamadora.
    Não usamos mutex de processo: a proteção também vale entre workers.
    """
    with db.no_autoflush:
        resultado = db.execute(
            update(Agendamento).where(Agendamento.id == agendamento_id)
            .values(id=Agendamento.id).execution_options(synchronize_session=False)
        )
        if resultado.rowcount != 1:
            raise HTTPException(status_code=404, detail="Agendamento não encontrado.")
        agendamento = db.get(Agendamento, agendamento_id, populate_existing=True)
        # Descarta relacionamentos que possam ter sido lidos antes de outra
        # transação trocar paciente/profissional ou concluir o atendimento.
        db.expire(agendamento, ["paciente", "psicologo", "lancamentos", "prontuario", "reagendamento", "origem_reagendamento", "ocorrencia"])
        return agendamento
