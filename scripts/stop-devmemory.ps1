param()

$ErrorActionPreference = "Stop"

$Root = Resolve-Path (Join-Path $PSScriptRoot "..")
Set-Location $Root

if (-not (Test-Path ".env.production")) {
  Write-Host "Missing .env.production. Nothing was stopped." -ForegroundColor Yellow
  exit 1
}

if (-not (Get-Command docker -ErrorAction SilentlyContinue)) {
  Write-Host "Docker was not found. Install Docker Desktop if you need to manage DevMemory services." -ForegroundColor Red
  exit 1
}

Write-Host "Stopping DevMemory private deployment..."
docker compose --env-file .env.production -f docker-compose.prod.yml down
if ($LASTEXITCODE -ne 0) {
  Write-Host "Docker Compose failed to stop DevMemory." -ForegroundColor Red
  exit $LASTEXITCODE
}

Write-Host "DevMemory stopped." -ForegroundColor Green
