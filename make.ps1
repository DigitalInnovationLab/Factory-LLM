# ============================================================
# FactoryLLM - An Open Safe AI Sandbox for Evaluating LLM in Smart Factories
# Windows PowerShell equivalent of the Makefile
# ============================================================
# Usage:  .\make.ps1 <target>
# Example: .\make.ps1 validate
#          .\make.ps1 install
#          .\make.ps1 run
#
# Requires: Python 3.10, Docker Desktop, Git for Windows

param(
    [Parameter(Position = 0)]
    [string]$Target = "help"
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

# ── Configuration ─────────────────────────────────────────────
$VENV         = ".fllm"
$VENV_BIN     = "$VENV\Scripts"
$PYTHON       = "$VENV_BIN\python.exe"
$PIP          = "$VENV_BIN\pip.exe"
$ALEMBIC      = "$VENV_BIN\alembic.exe"
$PYTEST       = "$VENV_BIN\pytest.exe"
$RUFF         = "$VENV_BIN\ruff.exe"
$APP_PORT     = 8888
$COMPOSE_FILE = "dockercompose.database.yml"

$REQUIRED_VARS = @(
    "APP_ENV",
    "MYSQL_PASSWORD", "DB_CONNECTION_SYNC", "DB_CONNECTION",
    "CHROMA_HOST", "CHROMA_PORT", "CHROMA_TOKEN", "CHROMA_SERVER_AUTHN_CREDENTIALS",
    "NEBULA_USER", "NEBULA_PASSWORD", "NEBULA_ADDRESS",
    "OPENAI_API_KEY", "GOOGLE_API_KEY", "OPENROUTER_API_KEY"
)

$PLACEHOLDER_VALUES = @(
    "your_mysql_password", "your_chroma_auth_token",
    "sk-...", "AIza...", "sk-or-...", "gsk_..."
)

# ── Helpers ───────────────────────────────────────────────────
function Write-Ok   { param($msg) Write-Host "  [OK] $msg" -ForegroundColor Green }
function Write-Fail { param($msg) Write-Host "  [X]  $msg" -ForegroundColor Red }
function Write-Warn { param($msg) Write-Host "  [!]  $msg" -ForegroundColor Yellow }
function Write-Section { param($msg) Write-Host "`n$msg" -ForegroundColor White }
function Write-Header {
    param($msg)
    Write-Host ""
    Write-Host $msg -ForegroundColor Cyan
    Write-Host ("=" * 48) -ForegroundColor Cyan
}

function Read-EnvFile {
    $env_vars = @{}
    if (Test-Path ".env") {
        Get-Content ".env" | ForEach-Object {
            if ($_ -match "^\s*([^#][^=]+?)\s*=\s*(.*)\s*$") {
                $key = $Matches[1].Trim()
                $val = $Matches[2].Trim().Trim('"').Trim("'")
                $env_vars[$key] = $val
            }
        }
    }
    return $env_vars
}

function Assert-ExitCode {
    param($msg)
    if ($LASTEXITCODE -ne 0) {
        Write-Fail $msg
        exit 1
    }
}

# ── Targets ───────────────────────────────────────────────────

function Show-Help {
    Write-Header "FactoryLLM - An Open Safe AI Sandbox for Evaluating LLM in Smart Factories"
    Write-Host ""
    Write-Host "USAGE:  .\make.ps1 <target>" -ForegroundColor White
    Write-Host ""
    Write-Host "Setup" -ForegroundColor White
    Write-Host "  install           Create .fllm venv + install dependencies" -ForegroundColor Green
    Write-Host "  validate          Check Python, Docker, .env, services, DB" -ForegroundColor Green
    Write-Host ""
    Write-Host "Database" -ForegroundColor White
    Write-Host "  db-up             Start MySQL, ChromaDB, NebulaGraph via Docker" -ForegroundColor Green
    Write-Host "  db-down           Stop all Docker services" -ForegroundColor Green
    Write-Host "  migrate           Run Alembic migrations (upgrade head)" -ForegroundColor Green
    Write-Host "  db-reset          [!] Drop + recreate schema (destructive)" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Run" -ForegroundColor White
    Write-Host "  run               Start the application on port $APP_PORT" -ForegroundColor Green
    Write-Host ""
    Write-Host "Test" -ForegroundColor White
    Write-Host "  test              Run unit + integration tests" -ForegroundColor Green
    Write-Host "  test-unit         Run backend unit tests" -ForegroundColor Green
    Write-Host "  test-integration  Run backend integration tests" -ForegroundColor Green
    Write-Host "  test-ui           Run Playwright UI tests" -ForegroundColor Green
    Write-Host "  test-cov          Run unit tests with HTML coverage report" -ForegroundColor Green
    Write-Host ""
    Write-Host "Code Quality" -ForegroundColor White
    Write-Host "  lint              Lint with ruff (check only)" -ForegroundColor Green
    Write-Host "  format            Auto-format + fix with ruff" -ForegroundColor Green
    Write-Host ""
    Write-Host "Misc" -ForegroundColor White
    Write-Host "  logs              Tail Docker service logs" -ForegroundColor Green
    Write-Host "  clean             Remove venv, caches, compiled files" -ForegroundColor Green
    Write-Host ""
}

function Invoke-Validate {
    Write-Header "Validating F-LLM environment..."
    Check-Python
    Check-Venv
    Check-Docker
    Check-Env
    Check-Services
    Write-Host ""
    Write-Host "  All checks passed — environment is ready!" -ForegroundColor Green
    Write-Host ""
}

function Check-Python {
    Write-Section "[ Python ]"
    $py = $null
    # Try python3.10 first, then python3, then python
    foreach ($cmd in @("python3.10", "python3", "python")) {
        try {
            $ver = & $cmd --version 2>&1
            if ($ver -match "Python 3\.10") {
                $py = $cmd; break
            }
        } catch {}
    }
    if (-not $py) {
        Write-Fail "Python 3.10 not found. Download from https://www.python.org/downloads/"
        exit 1
    }
    $version = & $py --version 2>&1
    Write-Ok "$version (via '$py')"
}

function Check-Venv {
    Write-Section "[ Virtual Environment ]"
    if (-not (Test-Path $VENV)) {
        Write-Fail "Venv '$VENV\' not found  ->  run: .\make.ps1 install"
        exit 1
    }
    if (-not (Test-Path $PYTHON)) {
        Write-Fail "Python binary missing in venv  ->  run: .\make.ps1 install"
        exit 1
    }
    Write-Ok "Venv found at $VENV\"
    Write-Ok "Python: $(& $PYTHON --version 2>&1)"

    Write-Host "  Checking key packages:" -ForegroundColor White
    $packages = @(
        @{ import = "nicegui";     label = "nicegui" },
        @{ import = "fastapi";     label = "fastapi" },
        @{ import = "sqlalchemy";  label = "sqlalchemy" },
        @{ import = "alembic";     label = "alembic" },
        @{ import = "langchain";   label = "langchain" },
        @{ import = "fitz";        label = "PyMuPDF (fitz)" },
        @{ import = "chromadb";    label = "chromadb" },
        @{ import = "pymysql";     label = "PyMySQL" }
    )
    foreach ($pkg in $packages) {
        $ver = & $PYTHON -c "import $($pkg.import); print(getattr($($pkg.import), '__version__', '?'))" 2>$null
        if ($LASTEXITCODE -eq 0 -and $ver) {
            Write-Host ("    [OK] {0,-24} {1}" -f $pkg.label, $ver) -ForegroundColor Green
        } else {
            Write-Host ("    [X]  {0,-24} not installed" -f $pkg.label) -ForegroundColor Red
        }
    }
}

function Check-Docker {
    Write-Section "[ Docker ]"
    if (-not (Get-Command "docker" -ErrorAction SilentlyContinue)) {
        Write-Fail "docker not found — install Docker Desktop from https://www.docker.com"
        exit 1
    }
    $info = docker info 2>&1
    if ($LASTEXITCODE -ne 0) {
        Write-Fail "Docker daemon not running — start Docker Desktop"
        exit 1
    }
    Write-Ok "Docker daemon is running"
    Write-Ok "$(docker --version)"
    Write-Ok "$(docker compose version)"
}

function Check-Env {
    Write-Section "[ Environment Variables ]"
    if (-not (Test-Path ".env")) {
        Write-Fail ".env file not found"
        Write-Host "       Fix: copy .env.example .env  (then fill in your values)" -ForegroundColor Yellow
        exit 1
    }
    Write-Ok ".env file found"

    $env_vars = Read-EnvFile
    $fail_count = 0

    foreach ($var in $REQUIRED_VARS) {
        $val = $env_vars[$var]
        $is_placeholder = (-not $val) -or ($PLACEHOLDER_VALUES -contains $val)
        if ($is_placeholder) {
            Write-Host ("  [X]  {0,-42} not set or still placeholder" -f $var) -ForegroundColor Red
            $fail_count++
        } else {
            $masked = if ($val.Length -gt 4) { $val.Substring(0, 4) + "****" } else { "****" }
            Write-Host ("  [OK] {0,-42} {1}" -f $var, $masked) -ForegroundColor Green
        }
    }
    if ($fail_count -gt 0) {
        Write-Warn "$fail_count variable(s) need attention in .env"
    }
}

function Check-Services {
    Write-Section "[ Docker Services ]"
    foreach ($svc in @("mysql", "chromadb", "graphd")) {
        $running = docker compose -f $COMPOSE_FILE ps --status running --services 2>$null | Select-String "^$svc$"
        if ($running) {
            Write-Ok "$svc is running"
        } else {
            Write-Warn "$svc is not running  ->  run: .\make.ps1 db-up"
        }
    }

    Write-Section "[ Database Connectivity ]"
    $env_vars = Read-EnvFile
    $db_url   = $env_vars["DB_CONNECTION_SYNC"]

    if (-not $db_url) {
        Write-Warn "Skipping (DB_CONNECTION_SYNC not set in .env)"
    } elseif (-not (docker compose -f $COMPOSE_FILE ps --status running --services 2>$null | Select-String "^mysql$")) {
        Write-Warn "Skipping MySQL check (container not running)"
    } else {
        if ($db_url.StartsWith("mysql://") -and -not $db_url.StartsWith("mysql+pymysql://")) {
            $db_url = $db_url.Replace("mysql://", "mysql+pymysql://")
        }
        $result = & $PYTHON -c @"
try:
    from sqlalchemy import create_engine, text
    e = create_engine('$db_url', connect_args={'connect_timeout': 5})
    with e.connect() as c: c.execute(text('SELECT 1'))
    print('ok')
except Exception as ex:
    print(f'error: {ex}')
"@ 2>$null
        if ($result -eq "ok") {
            Write-Ok "MySQL connection successful"
        } else {
            Write-Warn "MySQL connection failed — check DB_CONNECTION_SYNC in .env"
        }
    }

    Write-Section "[ Alembic Migration State ]"
    $alembic_out = & $ALEMBIC current 2>$null | Where-Object { $_ -notmatch "^INFO" } | Select-Object -First 1
    if ($alembic_out -match "\(head\)") {
        Write-Ok "Database is at head: $alembic_out"
    } elseif ($alembic_out) {
        Write-Warn "Pending migrations  ->  run: .\make.ps1 migrate"
        Write-Host "       Current: $alembic_out" -ForegroundColor Yellow
    } else {
        Write-Warn "Could not determine migration state  ->  run: .\make.ps1 migrate"
    }
}

function Invoke-Install {
    Write-Header "Setting up F-LLM environment..."

    # Find python 3.10
    $py = $null
    foreach ($cmd in @("python3.10", "python3", "python")) {
        try {
            $ver = & $cmd --version 2>&1
            if ($ver -match "Python 3\.10") { $py = $cmd; break }
        } catch {}
    }
    if (-not $py) {
        Write-Fail "Python 3.10 not found. Download from https://www.python.org/downloads/"
        exit 1
    }

    if (-not (Test-Path $VENV)) {
        Write-Host "Creating venv at $VENV\..." -ForegroundColor Cyan
        & $py -m venv $VENV
        Assert-ExitCode "Failed to create venv"
        Write-Ok "Venv created"
    } else {
        Write-Warn "Venv already exists at $VENV\ — skipping creation"
    }

    Write-Host "Upgrading pip..." -ForegroundColor Cyan
    & $PIP install --upgrade pip -q

    Write-Host "Installing from requirements.txt..." -ForegroundColor Cyan
    & $PIP install -r requirements.txt
    Assert-ExitCode "pip install failed"

    Write-Host ""
    Write-Ok "Installation complete"
    Write-Host ""
    Write-Host "Recommended next steps:" -ForegroundColor White
    Write-Host "  1. copy .env.example .env   (fill in API keys and passwords)" -ForegroundColor Cyan
    Write-Host "  2. .\make.ps1 db-up         (start Docker services)" -ForegroundColor Cyan
    Write-Host "  3. .\make.ps1 migrate        (apply database migrations)" -ForegroundColor Cyan
    Write-Host "  4. .\make.ps1 validate       (confirm everything is ready)" -ForegroundColor Cyan
    Write-Host "  5. .\make.ps1 run            (start the app)" -ForegroundColor Cyan
    Write-Host ""
}

function Invoke-DbUp {
    Write-Host "Starting Docker services (MySQL, ChromaDB, NebulaGraph)..." -ForegroundColor Cyan
    docker compose -f $COMPOSE_FILE up -d
    Assert-ExitCode "docker compose up failed"

    Write-Host "Waiting for MySQL to be ready" -ForegroundColor Cyan -NoNewline
    $ready = $false
    for ($i = 1; $i -le 30; $i++) {
        $ping = docker compose -f $COMPOSE_FILE exec -T mysql mysqladmin ping -h 127.0.0.1 --silent 2>$null
        if ($LASTEXITCODE -eq 0) { $ready = $true; break }
        Write-Host "." -NoNewline
        Start-Sleep -Seconds 2
    }
    Write-Host ""
    if ($ready) { Write-Ok "MySQL is ready" } else { Write-Warn "MySQL may not be ready yet — wait a few seconds" }
    Write-Host ""
    Write-Host "  MySQL       -> localhost:3306" -ForegroundColor White
    Write-Host "  phpMyAdmin  -> http://localhost:8080" -ForegroundColor White
    Write-Host "  ChromaDB    -> http://localhost:8000" -ForegroundColor White
    Write-Host "  NebulaGraph -> localhost:9669" -ForegroundColor White
    Write-Host ""
}

function Invoke-DbDown {
    Write-Host "Stopping Docker services..." -ForegroundColor Cyan
    docker compose -f $COMPOSE_FILE down
    Write-Ok "All services stopped"
}

function Invoke-Migrate {
    Write-Host "Running Alembic migrations..." -ForegroundColor Cyan
    & $ALEMBIC upgrade head
    Assert-ExitCode "Migration failed"
    Write-Ok "Migrations applied"
}

function Invoke-DbReset {
    Write-Host ""
    Write-Host "WARNING: This will drop and recreate the ENTIRE database schema." -ForegroundColor Red
    Write-Host "         All data will be permanently lost." -ForegroundColor Red
    Write-Host ""
    $confirm = Read-Host "Type 'yes' to confirm"
    if ($confirm -ne "yes") { Write-Host "Aborted."; return }

    Write-Host "Downgrading to base..." -ForegroundColor Cyan
    & $ALEMBIC downgrade base
    Write-Host "Upgrading to head..." -ForegroundColor Cyan
    & $ALEMBIC upgrade head
    Write-Ok "Database reset complete"
}

function Invoke-Run {
    Write-Host "Starting F-LLM on http://localhost:$APP_PORT" -ForegroundColor Cyan
    Write-Host "Press Ctrl+C to stop" -ForegroundColor Cyan
    Write-Host ""
    & $PYTHON app.py
}

function Invoke-Test {
    Invoke-TestUnit
    Invoke-TestIntegration
    Write-Host ""
    Write-Ok "All tests complete"
}

function Invoke-TestUnit {
    Write-Host "Running unit tests..." -ForegroundColor Cyan
    & $PYTEST backend\src -v --tb=short -q
}

function Invoke-TestIntegration {
    Write-Host "Running integration tests..." -ForegroundColor Cyan
    & $PYTEST backend\tests_integration -v --tb=short -q
}

function Invoke-TestUi {
    Write-Host "Running Playwright UI tests..." -ForegroundColor Cyan
    & $PYTEST test_ui -v --tb=short -q
}

function Invoke-TestCov {
    Write-Host "Running unit tests with coverage..." -ForegroundColor Cyan
    & $PYTEST backend\src --cov=backend --cov-report=term-missing --cov-report=html:htmlcov -q
    Write-Ok "Coverage report -> htmlcov\index.html"
}

function Invoke-Lint {
    Write-Host "Linting with ruff..." -ForegroundColor Cyan
    & $RUFF check backend\ frontend\ app.py
}

function Invoke-Format {
    Write-Host "Formatting with ruff..." -ForegroundColor Cyan
    & $RUFF format backend\ frontend\ app.py
    & $RUFF check --fix backend\ frontend\ app.py
    Write-Ok "Formatting complete"
}

function Invoke-Logs {
    docker compose -f $COMPOSE_FILE logs -f
}

function Invoke-Clean {
    Write-Host "Removing venv and caches..." -ForegroundColor Yellow
    if (Test-Path $VENV)     { Remove-Item -Recurse -Force $VENV }
    Get-ChildItem -Recurse -Directory -Filter "__pycache__"  | Remove-Item -Recurse -Force -ErrorAction SilentlyContinue
    Get-ChildItem -Recurse -Directory -Filter ".pytest_cache"| Remove-Item -Recurse -Force -ErrorAction SilentlyContinue
    Get-ChildItem -Recurse -Directory -Filter "htmlcov"      | Remove-Item -Recurse -Force -ErrorAction SilentlyContinue
    Get-ChildItem -Recurse -Filter "*.pyc"                   | Remove-Item -Force -ErrorAction SilentlyContinue
    Get-ChildItem -Recurse -Filter ".coverage"               | Remove-Item -Force -ErrorAction SilentlyContinue
    Write-Ok "Clean"
}

# ── Dispatch ──────────────────────────────────────────────────
switch ($Target.ToLower()) {
    "help"             { Show-Help }
    "validate"         { Invoke-Validate }
    "install"          { Invoke-Install }
    "db-up"            { Invoke-DbUp }
    "db-down"          { Invoke-DbDown }
    "migrate"          { Invoke-Migrate }
    "db-reset"         { Invoke-DbReset }
    "run"              { Invoke-Run }
    "test"             { Invoke-Test }
    "test-unit"        { Invoke-TestUnit }
    "test-integration" { Invoke-TestIntegration }
    "test-ui"          { Invoke-TestUi }
    "test-cov"         { Invoke-TestCov }
    "lint"             { Invoke-Lint }
    "format"           { Invoke-Format }
    "logs"             { Invoke-Logs }
    "clean"            { Invoke-Clean }
    default {
        Write-Host "Unknown target: '$Target'" -ForegroundColor Red
        Write-Host "Run '.\make.ps1 help' for available targets." -ForegroundColor Yellow
        exit 1
    }
}
