# Inicia API FastAPI (porta 8000)
Set-Location $PSScriptRoot\..\backend
if (-not (Test-Path .venv)) {
    Write-Host "Criando ambiente virtual..."
    python -m venv .venv
}
.\.venv\Scripts\pip install -r requirements.txt -q
Write-Host "API em http://localhost:8000  |  Docs: http://localhost:8000/docs"
.\.venv\Scripts\uvicorn app.main:app --reload --port 8000
