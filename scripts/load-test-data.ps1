# Load test data (resumes and vacancies) into the application - Windows version

$ErrorActionPreference = "Continue"

# Configuration
$backendUrl = if ($env:BACKEND_URL) { $env:BACKEND_URL } else { "http://localhost:8000" }
$frontendUrl = if ($env:FRONTEND_URL) { $env:FRONTEND_URL } else { "http://localhost:5173" }
$testDataDir = if ($env:TEST_DATA_DIR) { $env:TEST_DATA_DIR } else { ".\testdata\vacancy-resume-matching-dataset-main" }

Write-Host "========================================" -ForegroundColor Blue
Write-Host "  Loading Test Data" -ForegroundColor Blue
Write-Host "========================================" -ForegroundColor Blue
Write-Host ""

# Check if backend is running
Write-Host "Checking if backend is running..." -ForegroundColor Yellow
try {
    $response = Invoke-WebRequest -Uri "$backendUrl/health" -UseBasicParsing -TimeoutSec 5
    Write-Host "Backend is running" -ForegroundColor Green
} catch {
    Write-Host "Backend is not running at $backendUrl" -ForegroundColor Red
    Write-Host "Please start the application first: docker compose up -d"
    exit 1
}
Write-Host ""

# Check test data directory
if (!(Test-Path $testDataDir)) {
    Write-Host "Test data directory not found: $testDataDir" -ForegroundColor Red
    exit 1
}

$resumeDir = Join-Path $testDataDir "CV"
$vacancyCsv = Join-Path $testDataDir "5_vacancies.csv"

if (!(Test-Path $resumeDir)) {
    Write-Host "Resume directory not found: $resumeDir" -ForegroundColor Red
    exit 1
}

if (!(Test-Path $vacancyCsv)) {
    Write-Host "Vacancy file not found: $vacancyCsv" -ForegroundColor Red
    exit 1
}

# Count resume files
$resumeFiles = Get-ChildItem -Path $resumeDir -Include *.docx,*.pdf,*.DOCX,*.PDF -File
Write-Host "Found $($resumeFiles.Count) resume files" -ForegroundColor Green
Write-Host ""

# 1. Upload Resumes
Write-Host "[1/2] Uploading resumes..." -ForegroundColor Yellow

$resumeUploaded = 0
$resumeFailed = 0

foreach ($resume in $resumeFiles) {
    $filename = [System.IO.Path]::GetFileName($resume)
    Write-Host -NoNewline "   Uploading: $filename... "

    try {
        $result = Invoke-RestMethod -Uri "$backendUrl/api/resumes/upload" `
            -Method Post `
            -Form @{ file = Get-Item -Path $resume.FullName } `
            -TimeoutSec 30

        Write-Host "OK" -ForegroundColor Green
        $resumeUploaded++
    } catch {
        Write-Host "FAILED ($($_.Exception.Response.StatusCode.value__))" -ForegroundColor Red
        $resumeFailed++
    }

    Start-Sleep -Milliseconds 200
}

Write-Host ""
Write-Host "Resumes uploaded: $resumeUploaded" -ForegroundColor Green
if ($resumeFailed -gt 0) {
    Write-Host "Resumes failed: $resumeFailed" -ForegroundColor Yellow
}
Write-Host ""

# 2. Create Vacancies from CSV
Write-Host "[2/2] Creating vacancies from CSV..." -ForegroundColor Yellow

# Read CSV and skip header
$csvLines = Get-Content $vacancyCsv | Select-Object -Skip 1

foreach ($line in $csvLines) {
    if ([string]::IsNullOrWhiteSpace($line)) { continue }

    # Parse CSV (simple split - assumes no commas in quoted fields for the first few fields)
    $parts = $line -split '","', 3
    if ($parts.Length -lt 3) { continue }

    $id = $parts[0] -replace '"', ''
    $jobDescription = ($parts[1]) -replace '"', ''
    $jobTitle = ($parts[2] -split '","')[0] -replace '"', ''

    # Escape JSON special characters
    $jobDescription = $jobDescription -replace '\n', ' ' -replace '\r', ' '
    $jobTitle = $jobTitle -replace '\n', ' ' -replace '\r', ' '

    $jsonPayload = @{
        title = $jobTitle
        description = $jobDescription.Substring(0, [Math]::Min(2000, $jobDescription.Length)) + "..."
        location = "Remote"
        salary_min = 80000
        salary_max = 150000
        currency = "USD"
    } | ConvertTo-Json

    Write-Host -NoNewline "   Creating: $jobTitle... "

    try {
        $result = Invoke-RestMethod -Uri "$backendUrl/api/vacancies/" `
            -Method Post `
            -ContentType "application/json" `
            -Body $jsonPayload `
            -TimeoutSec 10

        Write-Host "OK" -ForegroundColor Green
    } catch {
        Write-Host "FAILED ($($_.Exception.Message))" -ForegroundColor Red
    }

    Start-Sleep -Milliseconds 200
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "  Test Data Loading Complete!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""
Write-Host "Summary:"
Write-Host "  - Resumes uploaded: $resumeUploaded"
Write-Host "  - Vacancies created: ~5 (from CSV)"
Write-Host ""
Write-Host "Next steps:"
Write-Host "  - Open frontend: http://localhost:5173"
Write-Host "  - Browse resumes: http://localhost:5173/resume-database"
Write-Host "  - Browse vacancies: http://localhost:5173/vacancies"
Write-Host "  - Try matching: http://localhost:5173/compare-vacancy"
Write-Host ""
