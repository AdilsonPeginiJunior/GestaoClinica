"""Conversões de instantes para o armazenamento UTC usado pelo protótipo."""

from datetime import datetime, timezone


def agora_utc() -> datetime:
    """Relógio único para regras temporais, em UTC sem fuso como no banco."""
    return datetime.now(timezone.utc).replace(tzinfo=None)


def utc_sem_fuso(instante: datetime) -> datetime:
    """Datas sem fuso seguem a convenção UTC existente; offsets são convertidos."""
    if instante.tzinfo is None:
        return instante
    return instante.astimezone(timezone.utc).replace(tzinfo=None)


def utc_com_fuso(instante: datetime) -> datetime:
    """Identifica UTC explicitamente nas respostas, para exibição local correta."""
    return utc_sem_fuso(instante).replace(tzinfo=timezone.utc)
