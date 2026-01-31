# TEAM7 Resume Analysis Platform - Local Setup Script for Windows
# One-command setup for local development

$ErrorActionPreference = "Stop"

Write-Host "========================================" -ForegroundColor Blue
Write-Host "  TEAM7 Resume Analysis Platform" -ForegroundColor Blue
Write-Host "  Local Development Setup (Windows)" -ForegroundColor Blue
Write-Host "========================================" -ForegroundColor Blue
Write-Host ""

# 1. Check prerequisites
Write-Host "[1/6] Checking prerequisites..." -ForegroundColor Yellow
try {
    $dockerVersion = docker --version 2>$null
    if ($LASTEXITCODE -ne 0) {
        throw "Docker not found"
    }
    Write-Host "   Docker is installed" -ForegroundColor Green
} catch {
    Write-Host "   Docker Desktop is not installed." -ForegroundColor Red
    Write-Host "   Please install Docker Desktop first:"
    Write-Host "   https://www.docker.com/products/docker-desktop"
    exit 1
}

try {
    $composeResult = docker compose version 2>$null
    if ($LASTEXITCODE -ne 0) {
        throw "Docker Compose not found"
    }
} catch {
    Write-Host "   Docker Compose is not available." -ForegroundColor Red
    Write-Host "   Please install Docker Desktop with Compose."
    exit 1
}
Write-Host ""

# 2. Create .env file
Write-Host "[2/6] Setting up environment..." -ForegroundColor Yellow
if (!(Test-Path .env)) {
    if (Test-Path .env.example) {
        Copy-Item .env.example .env
        Write-Host "   Created .env from .env.example" -ForegroundColor Green
    } else {
        @"
# Database
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
POSTGRES_DB=resume_analysis

# Ports
BACKEND_PORT=8000
FRONTEND_PORT=5173

# Optional: Add your API keys for enhanced features
# OPENAI_API_KEY=your_key_here
# ANTHROPIC_API_KEY=your_key_here
"@ | Out-File -Encoding UTF8 .env
        Write-Host "   Created .env with defaults" -ForegroundColor Green
    }
} else {
    Write-Host "   .env already exists" -ForegroundColor Green
}
Write-Host ""

# 3. Create necessary directories
Write-Host "[3/6] Creating directories..." -ForegroundColor Yellow
New-Item -ItemType Directory -Force -Path backend\models_cache | Out-Null
New-Item -ItemType Directory -Force -Path backend\data\uploads | Out-Null
Write-Host "   Directories created" -ForegroundColor Green
Write-Host ""

# 4. Stop any existing containers
Write-Host "[4/6] Stopping existing containers..." -ForegroundColor Yellow
docker compose down --remove-orphans 2>$null
Write-Host "   Cleaned up old containers" -ForegroundColor Green
Write-Host ""

# 5. Build and start services
Write-Host "[5/6] Building and starting services..." -ForegroundColor Yellow
Write-Host "   This may take 5-10 minutes on first run..."
Write-Host ""

# Start database and Redis first
docker compose up -d postgres redis

# Wait for database
Write-Host "   Waiting for database..."
$ready = $false
for ($i = 0; $i -lt 30; $i++) {
    $result = docker compose exec -T postgres pg_isready -U postgres 2>$null
    if ($LASTEXITCODE -eq 0) {
        $ready = $true
        break
    }
    Start-Sleep -Seconds 1
}
if ($ready) {
    Write-Host "   Database is ready" -ForegroundColor Green
}

# Build and start all services
docker compose build
docker compose up -d
Write-Host ""

# 6. Wait for services and health check
Write-Host "[6/6] Verifying services..." -ForegroundColor Yellow
Start-Sleep -Seconds 10

# Check backend
$backendReady = $false
for ($i = 0; $i -lt 20; $i++) {
    try {
        $response = Invoke-WebRequest -Uri "http://localhost:8000/health" -UseBasicParsing -TimeoutSec 2 -ErrorAction Stop
        if ($response.StatusCode -eq 200) {
            Write-Host "   Backend is healthy" -ForegroundColor Green
            $backendReady = $true
            break
        }
    } catch {
        # Ignore errors, retry
    }
    Start-Sleep -Seconds 2
}
if (-not $backendReady) {
    Write-Host "   Backend may still be starting... Check logs with: docker compose logs backend" -ForegroundColor Yellow
}

# Check frontend
try {
    $response = Invoke-WebRequest -Uri "http://localhost:5173/" -UseBasicParsing -TimeoutSec 2 -ErrorAction Stop
    if ($response.StatusCode -eq 200) {
        Write-Host "   Frontend is healthy" -ForegroundColor Green
    }
} catch {
    Write-Host "   Frontend may still be starting..." -ForegroundColor Yellow
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "  Setup Complete!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""
Write-Host "Services running at:"
Write-Host "  - Frontend:        http://localhost:5173"
Write-Host "  - Backend API:     http://localhost:8000"
Write-Host "  - API Docs:        http://localhost:8000/docs"
Write-Host "  - Flower Monitor:  http://localhost:5555"
Write-Host ""
Write-Host "Useful commands:"
Write-Host "  - View logs:       docker compose logs -f"
Write-Host "  - Stop services:   docker compose down"
Write-Host "  - Restart:         docker compose restart"
Write-Host ""
Write-Host "Load test data (65 resumes + 5 vacancies):"
Write-Host "  - .\scripts\load-test-data.ps1"
Write-Host ""
