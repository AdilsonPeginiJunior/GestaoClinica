# Inicia interface React (porta 5173)
Set-Location $PSScriptRoot\..\frontend
if (-not (Test-Path node_modules)) {
    Write-Host "Instalando dependencias npm..."
    npm install
}
Write-Host "Interface em http://localhost:5173"
npm run dev
