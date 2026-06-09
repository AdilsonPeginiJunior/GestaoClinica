"""Testa fluxo completo do perfil recepcao."""
import json
import urllib.error
import urllib.request

BASE = "http://127.0.0.1:8000/api"


def req(method, path, token=None, body=None):
    data = json.dumps(body).encode() if body is not None else None
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    request = urllib.request.Request(f"{BASE}{path}", data=data, headers=headers, method=method)
    with urllib.request.urlopen(request, timeout=10) as resp:
        return json.loads(resp.read().decode())


def main():
    login = req("POST", "/auth/login", body={"email": "recepcao@demo.com", "password": "demo123"})
    token = login["access_token"]
    print("LOGIN OK")

    me = req("GET", "/auth/me", token=token)
    assert me["perfil"] == "recepcionista", me
    print("ME OK:", me["nome"])

    dash = req("GET", "/dashboard", token=token)
    print("DASH OK:", dash["agendamentos_hoje"], "hoje")

    pacientes = req("GET", "/pacientes", token=token)
    print("PACIENTES OK:", len(pacientes))

    novo = req(
        "POST",
        "/pacientes",
        token=token,
        body={"nome": "Paciente Teste Recepcao", "cpf": "888.888.888-88", "tipo_atendimento": "particular"},
    )
    print("CREATE PACIENTE OK:", novo["id"])

    psis = req("GET", "/psicologos", token=token)
    ag = req(
        "POST",
        "/agendamentos",
        token=token,
        body={
            "paciente_id": novo["id"],
            "psicologo_id": psis[0]["id"],
            "inicio": "2026-06-15T14:00:00",
            "fim": "2026-06-15T15:00:00",
            "status": "agendado",
        },
    )
    print("CREATE AGENDAMENTO OK:", ag["id"])

    updated = req("PATCH", f"/agendamentos/{ag['id']}", token=token, body={"status": "realizado"})
    print("STATUS REALIZADO OK:", updated["status"])

    try:
        req("GET", f"/relatorios/psicologo/{psis[0]['id']}", token=token)
        print("ERRO: recepcao nao deveria acessar relatorio")
    except urllib.error.HTTPError as e:
        assert e.code == 403
        print("RELATORIO BLOQUEADO OK (403)")

    print("\nTodos os testes de recepcao passaram.")


if __name__ == "__main__":
    main()
