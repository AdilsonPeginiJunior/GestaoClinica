"""Escopo operacional por profissional, independente do nome do cargo."""
from fastapi import HTTPException
from sqlalchemy import or_, select

from app.models import Agendamento, Paciente, PerfilUsuario, Recorrencia


def profissional_restrito(usuario):
    if usuario.perfil != PerfilUsuario.psicologo:
        return None
    if not usuario.psicologo_id:
        raise HTTPException(403, "Profissional sem vínculo cadastrado.")
    return usuario.psicologo_id


def filtrar_pacientes(query, usuario):
    pid = profissional_restrito(usuario)
    if pid is not None:
        query = query.filter(or_(
            Paciente.id.in_(select(Agendamento.paciente_id).where(Agendamento.psicologo_id == pid)),
            Paciente.id.in_(select(Recorrencia.paciente_id).where(Recorrencia.psicologo_id == pid)),
        ))
    return query


def validar_paciente(db, usuario, paciente_id):
    if not filtrar_pacientes(db.query(Paciente.id), usuario).filter(Paciente.id == paciente_id).first():
        # Resposta igual para identificador ausente e paciente fora do escopo.
        raise HTTPException(404, "Paciente não encontrado.")
