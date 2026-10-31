param([int]$Port = 8765, [switch]$NoBrowser)
$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $PSScriptRoot
Push-Location $projectRoot
try {
    if (-not (Test-Path '.venv/Scripts/python.exe') -or -not (Test-Path 'apps/frontend/dist/index.html')) {
        Write-Host 'First run: installing dependencies and building SCST...'
        & "$PSScriptRoot/setup.ps1"
    }
    $listener = [System.Net.Sockets.TcpListener]::new([System.Net.IPAddress]::Loopback, $Port)
    try { $listener.Start() } catch { throw "Port $Port is already in use. Open the existing SCST window or choose -Port 8766." } finally { $listener.Stop() }
    $address = "http://127.0.0.1:$Port"
    Write-Host "SCST demo: $address (Ctrl+C to stop). Changes are session-only." -ForegroundColor Green
    $launchArgs = @('tooling/run_local.py', '--port', "$Port")
    if ($NoBrowser) { $launchArgs += '--no-browser' }
    & .venv/Scripts/python.exe @launchArgs
    if ($LASTEXITCODE -ne 0) { throw "SCST exited with code $LASTEXITCODE" }
} finally { Pop-Location }
