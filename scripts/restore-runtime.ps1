$ErrorActionPreference = 'Stop'
$workspace = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$sourceRoot = (Resolve-Path 'D:\MultivariatLab-runtime').Path
if ($sourceRoot -ne 'D:\MultivariatLab-runtime') { throw 'Unexpected source directory' }
$archive = Join-Path $workspace 'tmp\restored-runtime'
$plan = @(
    @{ Source='frontend\node_modules'; Target=(Join-Path $workspace 'frontend\node_modules-restored') },
    @{ Source='browsers'; Target=(Join-Path $env:LOCALAPPDATA 'ms-playwright') },
    @{ Source='frontend-install-incomplete'; Target=(Join-Path $archive 'frontend-install-incomplete') },
    @{ Source='frontend-node_modules'; Target=(Join-Path $archive 'frontend-node_modules') },
    @{ Source='npm-cache'; Target=(Join-Path $archive 'npm-cache') },
    @{ Source='temp'; Target=(Join-Path $archive 'temp') }
)
foreach ($entry in $plan) {
    $source = Join-Path $sourceRoot $entry.Source
    if (Test-Path -LiteralPath $entry.Target) { throw "Destination already exists: $($entry.Target)" }
    & robocopy $source $entry.Target /E /COPY:DAT /DCOPY:DAT /R:1 /W:1 /NFL /NDL /NJH /NJS /NP | Out-Null
    if ($LASTEXITCODE -ge 8) { throw "Copy failed: $source" }
    $files = @(Get-ChildItem -LiteralPath $source -File -Recurse -Force)
    foreach ($file in $files) {
        $relative = $file.FullName.Substring($source.Length).TrimStart('\')
        $destination = Join-Path $entry.Target $relative
        if ((Get-FileHash -LiteralPath $file.FullName -Algorithm SHA256).Hash -ne (Get-FileHash -LiteralPath $destination -Algorithm SHA256).Hash) { throw "Verification failed: $relative" }
    }
    Write-Output "Verified $($files.Count) files: $($entry.Source)"
}
$link = Get-Item -LiteralPath (Join-Path $workspace 'frontend\node_modules') -Force
if ($link.LinkType -ne 'Junction' -or $link.Target -ne (Join-Path $sourceRoot 'frontend\node_modules')) { throw 'Unexpected frontend link' }
$vite = Get-CimInstance Win32_Process -Filter "Name='node.exe'" | Where-Object { $_.CommandLine -like '*vite\bin\vite.js*' -and $_.CommandLine.Contains($workspace) }
foreach ($process in $vite) { Stop-Process -Id $process.ProcessId }
# Delete only the verified junction itself, never its directory contents.
[System.IO.Directory]::Delete($link.FullName)
Rename-Item -LiteralPath (Join-Path $workspace 'frontend\node_modules-restored') -NewName 'node_modules'
# All source files have matching SHA256 copies on C before removing the old directory.
$checkedSource = (Resolve-Path -LiteralPath $sourceRoot).Path
if ($checkedSource -ne 'D:\MultivariatLab-runtime') { throw 'Unsafe source path' }
Remove-Item -LiteralPath $checkedSource -Recurse -Force
Write-Output 'Runtime restored to C; D source removed after verification.'
