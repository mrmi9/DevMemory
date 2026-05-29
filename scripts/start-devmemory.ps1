param(
  [string]$Url = "http://127.0.0.1:5173",
  [int]$TimeoutSeconds = 120,
  [switch]$NoBrowser
)

$ErrorActionPreference = "Stop"

$Root = Resolve-Path (Join-Path $PSScriptRoot "..")
Set-Location $Root

if (-not (Test-Path ".env.production")) {
  Write-Host "Missing .env.production." -ForegroundColor Red
  Write-Host "Create it from .env.production.example first:"
  Write-Host "  copy .env.production.example .env.production"
  Write-Host "  notepad .env.production"
  exit 1
}

if (-not (Get-Command docker -ErrorAction SilentlyContinue)) {
  Write-Host "Docker was not found. Install and start Docker Desktop, then try again." -ForegroundColor Red
  exit 1
}

Write-Host "Starting DevMemory private deployment..."
docker compose --env-file .env.production -f docker-compose.prod.yml up --build -d
if ($LASTEXITCODE -ne 0) {
  Write-Host "Docker Compose failed to start DevMemory." -ForegroundColor Red
  exit $LASTEXITCODE
}

Write-Host "Waiting for web entry: $Url"
$Deadline = (Get-Date).AddSeconds($TimeoutSeconds)
$Ready = $false

while ((Get-Date) -lt $Deadline) {
  try {
    $Response = Invoke-WebRequest -Uri $Url -UseBasicParsing -TimeoutSec 5
    if ($Response.StatusCode -ge 200 -and $Response.StatusCode -lt 500) {
      $Ready = $true
      break
    }
  } catch {
    Start-Sleep -Seconds 2
  }
}

if (-not $Ready) {
  Write-Host "DevMemory services started, but the web entry did not become ready within $TimeoutSeconds seconds." -ForegroundColor Yellow
  Write-Host "Check service status with:"
  Write-Host "  docker compose --env-file .env.production -f docker-compose.prod.yml ps"
  exit 1
}

Write-Host "DevMemory is ready: $Url" -ForegroundColor Green

if (-not $NoBrowser) {
  Start-Process $Url
}
