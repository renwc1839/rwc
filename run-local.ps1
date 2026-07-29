$ErrorActionPreference = "Stop"

$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
$Backend = Join-Path $Root "backend"
$Frontend = Join-Path $Root "frontend"
$Python = Join-Path $Backend ".venv\Scripts\python.exe"
$NodeBin = "C:\Users\ASUS\.cache\codex-runtimes\codex-primary-runtime\dependencies\node\bin"
$PnpmDir = "C:\Users\ASUS\.cache\codex-runtimes\codex-primary-runtime\dependencies\bin\fallback"
$Pnpm = Join-Path $PnpmDir "pnpm.cmd"
$FrontendUrl = "http://localhost:5173/login"
$BackendUrl = "http://127.0.0.1:8000"

Write-Host "========================================"
Write-Host "RWC local temporary launcher"
Write-Host "Frontend: $FrontendUrl"
Write-Host "Backend : $BackendUrl"
Write-Host "========================================"
Write-Host ""

if (!(Test-Path $Python)) {
  throw "Missing backend Python venv: $Python"
}

if (!(Test-Path $Pnpm)) {
  throw "Missing bundled pnpm: $Pnpm"
}

$backendPort = Get-NetTCPConnection -LocalPort 8000 -ErrorAction SilentlyContinue
if ($backendPort) {
  Write-Host "Backend already running on port 8000."
} else {
  Write-Host "Starting backend on 127.0.0.1:8000 ..."
  Start-Process -FilePath $Python `
    -ArgumentList @("-m", "uvicorn", "app.main:app", "--host", "127.0.0.1", "--port", "8000") `
    -WorkingDirectory $Backend `
    -RedirectStandardOutput (Join-Path $Root "backend-dev.out.log") `
    -RedirectStandardError (Join-Path $Root "backend-dev.err.log") `
    -WindowStyle Hidden
}

$frontendPort = Get-NetTCPConnection -LocalPort 5173 -ErrorAction SilentlyContinue
if ($frontendPort) {
  Write-Host "Frontend already running on port 5173."
} else {
  Write-Host "Starting frontend on localhost:5173 ..."
  $frontendCommand = "`$env:Path='$NodeBin;$PnpmDir;' + `$env:Path; Set-Location '$Frontend'; & '$Pnpm' run dev -- --host localhost --port 5173"
  Start-Process -FilePath "powershell" `
    -ArgumentList @("-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", $frontendCommand) `
    -RedirectStandardOutput (Join-Path $Root "frontend-dev.out.log") `
    -RedirectStandardError (Join-Path $Root "frontend-dev.err.log") `
    -WindowStyle Hidden
}

Start-Sleep -Seconds 3

Write-Host ""
Write-Host "Open:"
Write-Host "  $FrontendUrl"
Write-Host ""
Write-Host "Test accounts:"
Write-Host "  Tenant  : tenant_demo / Tenant@123456"
Write-Host "  Admin   : superadmin / Admin@123456"
Write-Host "  Staff   : appointment_staff / Staff@123456"
Write-Host "  Property: property_manager / Property@123456"
Write-Host "  Landlord: demo_landlord / Landlord@123456"
Write-Host "  Repair  : repair_worker / Repair@123456"
Write-Host ""

Start-Process $FrontendUrl
