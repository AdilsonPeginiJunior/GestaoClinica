"""
Carga inicial do banco para demonstração ao cliente.

Executado automaticamente no startup (main.py) quando não há usuários.
Senha padrão de todos os perfis demo: demo123
"""

from datetime import datetime, timedelta

from sqlalchemy.orm import Session

from app.auth import get_password_hash
from app.models import (
    Agendamento,
    Paciente,
    PerfilUsuario,
    Psicologo,
    StatusAgendamento,
    TipoAtendimento,
    Usuario,
)


def seed_database(db: Session) -> None:
    """Popula psicólogos, pacientes, usuários e agendamentos apenas na primeira execução."""
    if db.query(Usuario).count() > 0:
        return

    psicologos_data = [
        ("Dra. Ana Silva", "06/12345", "ana.silva@clinica.com", "(11) 90001-0001", 55.0),
        ("Dr. Bruno Costa", "06/23456", "bruno.costa@clinica.com", "(11) 90001-0002", 60.0),
        ("Dra. Carla Mendes", "06/34567", "carla.mendes@clinica.com", "(11) 90001-0003", 50.0),
        ("Dr. Daniel Rocha", "06/45678", "daniel.rocha@clinica.com", "(11) 90001-0004", 65.0),
    ]
    psicologos: list[Psicologo] = []
    for nome, crp, email, tel, pct in psicologos_data:
        psicologos.append(
            Psicologo(
                nome=nome,
                crp=crp,
                email=email,
                telefone=tel,
                percentual_repasse=pct,
            )
        )
    db.add_all(psicologos)
    db.flush()

    pacientes_data = [
        ("Maria Oliveira", "111.111.111-11", TipoAtendimento.particular),
        ("Joao Santos", "222.222.222-22", TipoAtendimento.convenio),
        ("Paula Ferreira", "333.333.333-33", TipoAtendimento.particular),
        ("Ricardo Lima", "444.444.444-44", TipoAtendimento.convenio),
        ("Fernanda Alves", "555.555.555-55", TipoAtendimento.particular),
        ("Lucas Pereira", "666.666.666-66", TipoAtendimento.convenio),
    ]
    pacientes: list[Paciente] = []
    for i, (nome, cpf, tipo) in enumerate(pacientes_data):
        pacientes.append(
            Paciente(
                nome=nome,
                cpf=cpf,
                telefone=f"(11) 9888-000{i+1}",
                email=f"paciente{i+1}@email.com",
                tipo_atendimento=tipo,
            )
        )
    db.add_all(pacientes)
    db.flush()

    demo_password = get_password_hash("demo123")
    users = [
        ("Recepcionista Demo", "recepcao@demo.com", PerfilUsuario.recepcionista, None),
        ("Psicologo Demo", "psicologo@demo.com", PerfilUsuario.psicologo, psicologos[0].id),
        ("Socia Demo", "socia@demo.com", PerfilUsuario.socia, None),
        ("Admin Demo", "admin@demo.com", PerfilUsuario.admin, None),
    ]
    for nome, email, perfil, psic_id in users:
        db.add(
            Usuario(
                nome=nome,
                email=email,
                senha_hash=demo_password,
                perfil=perfil,
                psicologo_id=psic_id,
            )
        )
    db.flush()

    # Horários de demonstração: passado (realizado) e futuro (agendado/confirmado)
    base = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    agendamentos = [
        (pacientes[0], psicologos[0], base + timedelta(days=1, hours=9), StatusAgendamento.confirmado),
        (pacientes[1], psicologos[1], base + timedelta(days=1, hours=11), StatusAgendamento.agendado),
        (pacientes[2], psicologos[0], base - timedelta(days=2, hours=10), StatusAgendamento.realizado),
        (pacientes[3], psicologos[2], base - timedelta(days=1, hours=14), StatusAgendamento.realizado),
        (pacientes[4], psicologos[3], base + timedelta(days=2, hours=15), StatusAgendamento.agendado),
        (pacientes[5], psicologos[1], base + timedelta(hours=16), StatusAgendamento.confirmado),
    ]

    for paciente, psicologo, inicio, status in agendamentos:
        db.add(
            Agendamento(
                paciente_id=paciente.id,
                psicologo_id=psicologo.id,
                inicio=inicio,
                fim=inicio + timedelta(hours=1),
                status=status,
            )
        )
    db.commit()

    from app.services import criar_lancamentos_agendamento_realizado

    realizados = (
        db.query(Agendamento)
        .filter(Agendamento.status == StatusAgendamento.realizado)
        .all()
    )
    for ag in realizados:
        criar_lancamentos_agendamento_realizado(db, ag)
