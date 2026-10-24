"""Atualização não destrutiva do schema financeiro do protótipo.

Migrações formais de produção permanecem no plano OPS-01.
"""

from sqlalchemy import String, and_, cast, func, inspect, or_, select, text, update

from app.models import EstornoFinanceiro, LancamentoFinanceiro, TipoLancamento


def atualizar_schema_financeiro(engine) -> None:
    lancamentos = LancamentoFinanceiro.__table__
    estornos = EstornoFinanceiro.__table__
    original_reconhecido = and_(
        lancamentos.c.automatico.is_(True),
        lancamentos.c.agendamento_id.is_not(None),
        lancamentos.c.psicologo_id.is_not(None),
        lancamentos.c.valor >= 0,
        or_(
            and_(lancamentos.c.tipo == TipoLancamento.receita,
                 lancamentos.c.descricao.like("Receita sessao #" + cast(lancamentos.c.agendamento_id, String) + " - %")),
            and_(lancamentos.c.tipo == TipoLancamento.repasse,
                 lancamentos.c.descricao.like("Repasse psicologo #" + cast(lancamentos.c.agendamento_id, String) + " - %")),
        ),
    )
    with engine.begin() as conn:
        if conn.dialect.name == "sqlite":
            conn.exec_driver_sql("BEGIN IMMEDIATE")
        elif conn.dialect.name == "postgresql":
            # Serializa esta atualização de schema entre workers PostgreSQL.
            conn.execute(text("SELECT pg_advisory_xact_lock(724031)"))
        duplicados = conn.execute(
            select(lancamentos.c.agendamento_id).where(original_reconhecido)
            .group_by(lancamentos.c.agendamento_id, lancamentos.c.tipo)
            .having(func.count() > 1)
        ).scalars().all()
        if duplicados:
            raise RuntimeError(
                "Faturamento automático duplicado; revise os agendamentos antes de iniciar: "
                + ", ".join(str(i) for i in sorted(set(duplicados)))
            )
        colunas = {c["name"] for c in inspect(conn).get_columns("lancamentos_financeiros")}
        if "chave_automatica" not in colunas:
            conn.execute(text("ALTER TABLE lancamentos_financeiros ADD COLUMN chave_automatica VARCHAR(64)"))
        conn.execute(update(lancamentos).where(
            lancamentos.c.chave_automatica.is_(None), original_reconhecido,
        ).values(chave_automatica=cast(lancamentos.c.tipo, String)))
        original_id = select(estornos.c.lancamento_original_id).where(
            estornos.c.lancamento_estorno_id == lancamentos.c.id
        ).correlate(lancamentos).scalar_subquery()
        conn.execute(update(lancamentos).where(
            lancamentos.c.chave_automatica.is_(None),
            lancamentos.c.id.in_(select(estornos.c.lancamento_estorno_id)),
        ).values(chave_automatica="estorno:" + cast(original_id, String)))
        indice = next(i for i in lancamentos.indexes if i.name == "uq_lancamento_chave_automatica")
        indice.create(conn, checkfirst=True)
