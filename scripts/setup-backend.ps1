$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $PSScriptRoot
Set-Location -LiteralPath $projectRoot
if (-not (Test-Path -LiteralPath 'backend/.venv/Scripts/python.exe')) { python -m venv backend/.venv }
& backend/.venv/Scripts/python.exe -m pip install -r backend/requirements.lock.txt
