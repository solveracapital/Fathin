$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $PSScriptRoot
Set-Location -LiteralPath $projectRoot
& "$projectRoot/backend/.venv/Scripts/python.exe" -m uvicorn backend.app:app --host 127.0.0.1 --port 8000
