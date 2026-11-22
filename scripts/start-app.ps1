param([switch]$NoBrowser)
$ErrorActionPreference='Stop'
$projectRoot=(Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$python=Join-Path $projectRoot 'backend\.venv\Scripts\python.exe'
$vite=Join-Path $projectRoot 'frontend\node_modules\vite\bin\vite.js'
if (!(Test-Path -LiteralPath $python) -or !(Test-Path -LiteralPath $vite)) { throw 'Dependensi belum terpasang. Ikuti README.md sebelum membuka aplikasi.' }
$node=(Get-Command node -ErrorAction Stop).Source
$logs=Join-Path $projectRoot 'var\launcher'
New-Item -ItemType Directory -Path $logs -Force | Out-Null
function BackendReady {
    try { $r=Invoke-RestMethod -Uri 'http://127.0.0.1:8000/api/v1/health' -TimeoutSec 2; return $r.status -eq 'ok' -and $r.efa_engine -eq 'statsmodels' } catch { return $false }
}
function FrontendReady {
    try { $r=Invoke-WebRequest -UseBasicParsing -Uri 'http://127.0.0.1:5173' -TimeoutSec 5; return $r.StatusCode -eq 200 -and $r.Content.Contains('Multivariat Lab') } catch { return $false }
}
function BackendRunning {
    return [bool](Get-CimInstance Win32_Process -Filter "Name='python.exe'" | Where-Object { $_.CommandLine -like '*uvicorn backend.app:app*' -and $_.CommandLine -like ('*'+$python+'*') } | Select-Object -First 1)
}
function FrontendRunning {
    return [bool](Get-CimInstance Win32_Process -Filter "Name='node.exe'" | Where-Object { $_.CommandLine -like ('*'+$vite+'*') } | Select-Object -First 1)
}
if (!(BackendReady) -and !(BackendRunning)) {
    Start-Process -FilePath $python -ArgumentList @('-m','uvicorn','backend.app:app','--host','127.0.0.1','--port','8000') -WorkingDirectory $projectRoot -WindowStyle Hidden -RedirectStandardOutput (Join-Path $logs 'backend.log') -RedirectStandardError (Join-Path $logs 'backend-error.log') | Out-Null
}
if (!(FrontendReady) -and !(FrontendRunning)) {
    Start-Process -FilePath $node -ArgumentList @(('"'+$vite+'"'),'--host','127.0.0.1','--port','5173','--strictPort') -WorkingDirectory (Join-Path $projectRoot 'frontend') -WindowStyle Hidden -RedirectStandardOutput (Join-Path $logs 'frontend.log') -RedirectStandardError (Join-Path $logs 'frontend-error.log') | Out-Null
}
for($attempt=0;$attempt -lt 40;$attempt++) {
    if ((BackendReady) -and (FrontendReady)) {
        Write-Output 'Multivariat Lab siap: http://127.0.0.1:5173'
        if (!$NoBrowser) { Start-Process 'http://127.0.0.1:5173' }
        exit 0
    }
    Start-Sleep -Milliseconds 500
}
throw "Aplikasi belum siap. Periksa catatan di $logs."
