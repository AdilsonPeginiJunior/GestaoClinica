"""Abre o Gestao Clinica no Windows iniciando a API e a interface web."""

from __future__ import annotations

import subprocess
import sys
import threading
import time
import webbrowser
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SCRIPTS = (
    ("API", ROOT / "scripts" / "iniciar-backend.ps1"),
    ("Interface", ROOT / "scripts" / "iniciar-frontend.ps1"),
)
URL = "http://localhost:5173"


def main() -> int:
    if sys.platform != "win32":
        print("Este atalho inicia os scripts PowerShell e funciona somente no Windows.")
        return 1

    powershell = subprocess.run(
        ["where.exe", "powershell.exe"],
        capture_output=True,
        text=True,
        check=False,
    )
    if powershell.returncode != 0 or not powershell.stdout.strip():
        print("Nao foi possivel localizar o Windows PowerShell.")
        return 1

    shell = powershell.stdout.splitlines()[0].strip()
    for name, script in SCRIPTS:
        if not script.is_file():
            print(f"Script de inicializacao nao encontrado: {script}")
            return 1
        try:
            subprocess.Popen(
                [
                    shell,
                    "-NoExit",
                    "-ExecutionPolicy",
                    "Bypass",
                    "-File",
                    str(script),
                ],
                cwd=ROOT,
                creationflags=subprocess.CREATE_NEW_CONSOLE,
            )
        except OSError as exc:
            print(f"Nao foi possivel iniciar {name}: {exc}")
            return 1
        print(f"{name}: terminal iniciado.")

    print("Abrindo a interface em alguns segundos. Mantenha os terminais abertos.")
    timer = threading.Timer(5, webbrowser.open, args=(URL,))
    timer.daemon = True
    timer.start()
    time.sleep(1)
    print(f"Endereco da interface: {URL}")
    print("Se a primeira inicializacao demorar, aguarde a instalacao das dependencias.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
