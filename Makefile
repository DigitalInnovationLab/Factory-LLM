# ============================================================
# FactoryLLM - An Open Safe AI Sandbox for Evaluating LLM in Smart Factories
# ============================================================
# Linux / macOS / Git Bash / WSL:  make <target>
# Windows PowerShell:              .\make.ps1 <target>

# ── Configuration ────────────────────────────────────────────
VENV         := .fllm

# ── OS detection (must come after VENV is defined) ───────────
ifeq ($(OS),Windows_NT)
    # Running under Git Bash or MSYS2 on Windows
    VENV_BIN     := $(VENV)/Scripts
    PYTHON_BIN   := python
    EXE          := .exe
else
    VENV_BIN     := $(VENV)/bin
    PYTHON_BIN   := python3.10
    EXE          :=
endif

PYTHON       := $(VENV_BIN)/python$(EXE)
PIP          := $(VENV_BIN)/pip$(EXE)
ALEMBIC      := $(VENV_BIN)/alembic$(EXE)
PYTEST       := $(VENV_BIN)/pytest$(EXE)
COMPOSE      := docker compose -f dockercompose.database.yml
APP_PORT     := 8888

# Required .env variables
REQUIRED_VARS := APP_ENV \
                 MYSQL_PASSWORD DB_CONNECTION_SYNC DB_CONNECTION \
                 CHROMA_HOST CHROMA_PORT CHROMA_TOKEN CHROMA_SERVER_AUTHN_CREDENTIALS \
                 NEBULA_USER NEBULA_PASSWORD NEBULA_ADDRESS \
                 OPENAI_API_KEY GOOGLE_API_KEY OPENROUTER_API_KEY

# ── Colors ───────────────────────────────────────────────────
RED    := \033[0;31m
GREEN  := \033[0;32m
YELLOW := \033[0;33m
CYAN   := \033[0;36m
BOLD   := \033[1m
RESET  := \033[0m

OK     := $(GREEN)✓$(RESET)
FAIL   := $(RED)✗$(RESET)
WARN   := $(YELLOW)⚠$(RESET)

.PHONY: help validate install \
        db-up db-down db-reset migrate \
        run \
        evaluate evaluate-clean \
        test test-unit test-integration test-ui test-cov \
        lint format \
        logs clean

.DEFAULT_GOAL := help

# ─────────────────────────────────────────────────────────────
# HELP
# ─────────────────────────────────────────────────────────────
help:
	@printf "\n$(BOLD)$(CYAN)FactoryLLM - An Open Safe AI Sandbox for Evaluating LLM in Smart Factories$(RESET)\n"
	@printf "$(CYAN)══════════════════════════════════════════════$(RESET)\n"
	@printf "$(YELLOW)Windows PowerShell users: use $(BOLD).\\make.ps1 <target>$(RESET)\n\n"
	@printf "$(BOLD)Setup$(RESET)\n"
	@printf "  $(GREEN)make install$(RESET)           Create .fllm venv + install dependencies\n"
	@printf "  $(GREEN)make validate$(RESET)          Check Python, Docker, .env, services, DB\n"
	@printf "\n$(BOLD)Database$(RESET)\n"
	@printf "  $(GREEN)make db-up$(RESET)             Start MySQL, ChromaDB, NebulaGraph via Docker\n"
	@printf "  $(GREEN)make db-down$(RESET)           Stop all Docker services\n"
	@printf "  $(GREEN)make migrate$(RESET)           Run Alembic migrations (upgrade head)\n"
	@printf "  $(GREEN)make db-reset$(RESET)          $(RED)⚠ Drop + recreate schema (destructive)$(RESET)\n"
	@printf "\n$(BOLD)Run$(RESET)\n"
	@printf "  $(GREEN)make run$(RESET)               Start the application on port $(APP_PORT)\n"
	@printf "\n$(BOLD)Evaluation$(RESET)\n"
	@printf "  $(GREEN)make evaluate$(RESET)          Run LLM evaluation (prompts for chat IDs)\n"
	@printf "  $(GREEN)make evaluate-clean$(RESET)    Delete all generated visualisations & results\n"
	@printf "\n$(BOLD)Test$(RESET)\n"
	@printf "  $(GREEN)make test$(RESET)              Run unit + integration tests\n"
	@printf "  $(GREEN)make test-unit$(RESET)         Run backend unit tests\n"
	@printf "  $(GREEN)make test-integration$(RESET)  Run backend integration tests\n"
	@printf "  $(GREEN)make test-ui$(RESET)           Run Playwright UI tests\n"
	@printf "  $(GREEN)make test-cov$(RESET)          Run unit tests with HTML coverage report\n"
	@printf "\n$(BOLD)Code Quality$(RESET)\n"
	@printf "  $(GREEN)make lint$(RESET)              Lint with ruff (check only)\n"
	@printf "  $(GREEN)make format$(RESET)            Auto-format + fix with ruff\n"
	@printf "\n$(BOLD)Misc$(RESET)\n"
	@printf "  $(GREEN)make logs$(RESET)              Tail Docker service logs\n"
	@printf "  $(GREEN)make clean$(RESET)             Remove venv, caches, compiled files\n\n"

# ─────────────────────────────────────────────────────────────
# VALIDATE — full environment check
# ─────────────────────────────────────────────────────────────
validate:
	@printf "\n$(BOLD)$(CYAN)Validating F-LLM environment...$(RESET)\n"
	@printf "$(CYAN)══════════════════════════════════════════════$(RESET)\n\n"
	@$(MAKE) -s _check-python
	@$(MAKE) -s _check-venv
	@$(MAKE) -s _check-docker
	@$(MAKE) -s _check-env
	@$(MAKE) -s _check-services
	@printf "\n$(BOLD)$(GREEN)✓ All checks passed — environment is ready!$(RESET)\n\n"

# ── Python version ────────────────────────────────────────────
_check-python:
	@printf "$(BOLD)[ Python ]$(RESET)\n"
	@if ! command -v $(PYTHON_BIN) > /dev/null 2>&1; then \
		printf "  $(FAIL) $(PYTHON_BIN) not found. Install Python 3.10 from python.org\n"; \
		exit 1; \
	fi
	@PY_VER=$$($(PYTHON_BIN) -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')"); \
	if [ "$$PY_VER" != "3.10" ]; then \
		printf "  $(FAIL) Requires Python 3.10, found $$PY_VER\n"; \
		exit 1; \
	fi
	@printf "  $(OK) $$($(PYTHON_BIN) --version)\n"

# ── Virtual environment ───────────────────────────────────────
_check-venv:
	@printf "\n$(BOLD)[ Virtual Environment ]$(RESET)\n"
	@if [ ! -d "$(VENV)" ]; then \
		printf "  $(FAIL) Venv '$(VENV)/' not found  →  run: make install\n"; \
		exit 1; \
	fi
	@if [ ! -x "$(PYTHON)" ]; then \
		printf "  $(FAIL) Python binary missing in venv  →  run: make install\n"; \
		exit 1; \
	fi
	@printf "  $(OK) Venv found at $(VENV)/\n"
	@printf "  $(OK) Python: $$($(PYTHON) --version)\n"
	@printf "  Checking key packages:\n"
	@MISSING=0; \
	check_pkg() { \
		pkg=$$1; import=$$2; label=$$3; \
		ver=$$($(PYTHON) -c "import $$import; v=getattr($$import,'__version__',getattr($$import,'version','?')); print(v)" 2>/dev/null); \
		if [ -n "$$ver" ]; then \
			printf "    $(OK) %-22s %s\n" "$$label" "$$ver"; \
		else \
			printf "    $(FAIL) %-22s not installed\n" "$$label"; \
			MISSING=1; \
		fi; \
	}; \
	$(PYTHON) -c "import nicegui;     print('$(OK) nicegui            ', nicegui.__version__)" 2>/dev/null || { printf "    $(FAIL) nicegui              not installed\n"; MISSING=1; }; \
	$(PYTHON) -c "import fastapi;     print('$(OK) fastapi            ', fastapi.__version__)" 2>/dev/null || { printf "    $(FAIL) fastapi              not installed\n"; MISSING=1; }; \
	$(PYTHON) -c "import sqlalchemy;  print('$(OK) sqlalchemy         ', sqlalchemy.__version__)" 2>/dev/null || { printf "    $(FAIL) sqlalchemy           not installed\n"; MISSING=1; }; \
	$(PYTHON) -c "import alembic;     print('$(OK) alembic            ', alembic.__version__)" 2>/dev/null || { printf "    $(FAIL) alembic              not installed\n"; MISSING=1; }; \
	$(PYTHON) -c "import langchain;   print('$(OK) langchain          ', langchain.__version__)" 2>/dev/null || { printf "    $(FAIL) langchain            not installed\n"; MISSING=1; }; \
	$(PYTHON) -c "import fitz;        print('$(OK) PyMuPDF (fitz)     ', fitz.__version__)" 2>/dev/null || { printf "    $(FAIL) PyMuPDF (fitz)       not installed\n"; MISSING=1; }; \
	$(PYTHON) -c "import chromadb;    print('$(OK) chromadb           ', chromadb.__version__)" 2>/dev/null || { printf "    $(FAIL) chromadb             not installed\n"; MISSING=1; }; \
	$(PYTHON) -c "import pymysql;     print('$(OK) PyMySQL            ', pymysql.__version__)" 2>/dev/null || { printf "    $(FAIL) PyMySQL              not installed\n"; MISSING=1; }; \
	if [ "$$MISSING" = "1" ]; then printf "  $(WARN) Some packages missing  →  run: make install\n"; fi

# ── Docker ────────────────────────────────────────────────────
_check-docker:
	@printf "\n$(BOLD)[ Docker ]$(RESET)\n"
	@if ! command -v docker > /dev/null 2>&1; then \
		printf "  $(FAIL) docker CLI not found — install Docker Desktop\n"; \
		exit 1; \
	fi
	@if ! docker info > /dev/null 2>&1; then \
		printf "  $(FAIL) Docker daemon not running — start Docker Desktop\n"; \
		exit 1; \
	fi
	@printf "  $(OK) Docker daemon is running\n"
	@printf "  $(OK) $$(docker --version)\n"
	@printf "  $(OK) $$(docker compose version)\n"

# ── Environment variables ─────────────────────────────────────
_check-env:
	@printf "\n$(BOLD)[ Environment Variables ]$(RESET)\n"
	@if [ ! -f ".env" ]; then \
		printf "  $(FAIL) .env file not found\n"; \
		printf "       Fix: cp .env.example .env  then fill in your values\n"; \
		exit 1; \
	fi
	@printf "  $(OK) .env file found\n"
	@FAIL_COUNT=0; \
	for var in $(REQUIRED_VARS); do \
		val=$$(grep -E "^$$var[[:space:]]*=" .env | head -1 \
		       | sed 's/^[^=]*=//; s/^[[:space:]]*//; s/[[:space:]]*$$//; s/^"//; s/"$$//; s/^'"'"'//; s/'"'"'$$//'); \
		if [ -z "$$val" ] \
		   || [ "$$val" = "your_mysql_password" ] \
		   || [ "$$val" = "your_chroma_auth_token" ] \
		   || [ "$$val" = "change-me-to-a-random-secret-string" ] \
		   || echo "$$val" | grep -qE "^(sk-\.\.\.|AIza\.\.\.|sk-or-\.\.\.|gsk_\.\.\.)$$"; then \
			printf "  $(FAIL) %-42s not set or still placeholder\n" "$$var"; \
			FAIL_COUNT=$$((FAIL_COUNT + 1)); \
		else \
			MASKED=$$(echo "$$val" | sed 's/\(.\{4\}\).*/\1****/'); \
			printf "  $(OK) %-42s %s\n" "$$var" "$$MASKED"; \
		fi; \
	done; \
	if [ "$$FAIL_COUNT" -gt 0 ]; then \
		printf "  $(WARN) $$FAIL_COUNT variable(s) need attention in .env\n"; \
	fi

# ── Docker services + DB connectivity ────────────────────────
_check-services:
	@printf "\n$(BOLD)[ Docker Services ]$(RESET)\n"
	@for svc in mysql chromadb graphd; do \
		if $(COMPOSE) ps --status running --services 2>/dev/null | grep -q "^$$svc$$"; then \
			printf "  $(OK) $$svc is running\n"; \
		else \
			printf "  $(WARN) $$svc is not running  →  run: make db-up\n"; \
		fi; \
	done
	@printf "\n$(BOLD)[ Database Connectivity ]$(RESET)\n"
	@if [ ! -f ".env" ]; then \
		printf "  $(WARN) Skipping (no .env)\n"; \
	elif ! $(COMPOSE) ps --status running --services 2>/dev/null | grep -q "^mysql$$"; then \
		printf "  $(WARN) Skipping MySQL check (container not running)\n"; \
	else \
		DB_URL=$$(grep -E "^DB_CONNECTION_SYNC[[:space:]]*=" .env | head -1 \
		          | sed 's/^[^=]*=//;s/^[[:space:]]*//;s/[[:space:]]*$$//;s/^"//;s/"$$//;s/^'"'"'//;s/'"'"'$$//'); \
		if [ -z "$$DB_URL" ]; then \
			printf "  $(WARN) DB_CONNECTION_SYNC not set in .env\n"; \
		else \
			if DB_CONNECTION_SYNC="$$DB_URL" $(PYTHON) -c \
				"import os,sys; from sqlalchemy import create_engine,text; u=os.environ['DB_CONNECTION_SYNC']; u=u.replace('mysql://','mysql+pymysql://',1) if u.startswith('mysql://') and not u.startswith('mysql+pymysql://') else u; e=create_engine(u,connect_args={'connect_timeout':5}); c=e.connect(); c.execute(text('SELECT 1'))" \
				2>/dev/null; then \
				printf "  $(OK) MySQL connection successful\n"; \
			else \
				printf "  $(FAIL) MySQL connection failed — check DB_CONNECTION_SYNC in .env\n"; \
			fi; \
		fi; \
	fi
	@printf "\n$(BOLD)[ Alembic Migration State ]$(RESET)\n"
	@if [ -f ".env" ] && $(COMPOSE) ps --status running --services 2>/dev/null | grep -q "^mysql$$"; then \
		CURRENT=$$($(ALEMBIC) current 2>/dev/null | grep -v "^INFO" | head -1); \
		if echo "$$CURRENT" | grep -q "(head)"; then \
			printf "  $(OK) Database is at head: $$CURRENT\n"; \
		elif [ -n "$$CURRENT" ]; then \
			printf "  $(WARN) Pending migrations  →  run: make migrate\n"; \
			printf "       Current: $$CURRENT\n"; \
		else \
			printf "  $(WARN) Could not determine migration state  →  run: make migrate\n"; \
		fi; \
	else \
		printf "  $(WARN) Skipping (MySQL not running or .env missing)\n"; \
	fi

# ─────────────────────────────────────────────────────────────
# INSTALL
# ─────────────────────────────────────────────────────────────
install:
	@printf "\n$(BOLD)$(CYAN)Setting up F-LLM environment...$(RESET)\n\n"
	@if ! command -v $(PYTHON_BIN) > /dev/null 2>&1; then \
		printf "$(FAIL) $(PYTHON_BIN) not found. Install Python 3.10 first.\n"; \
		exit 1; \
	fi
	@if [ ! -d "$(VENV)" ]; then \
		printf "$(CYAN)Creating venv at $(VENV)/...$(RESET)\n"; \
		$(PYTHON_BIN) -m venv $(VENV); \
		printf "$(OK) Venv created\n"; \
	else \
		printf "$(WARN) Venv already exists at $(VENV)/ — skipping creation\n"; \
	fi
	@printf "$(CYAN)Upgrading pip...$(RESET)\n"
	@$(PIP) install --upgrade pip -q
	@printf "$(CYAN)Installing from requirements.txt...$(RESET)\n"
	@$(PIP) install -r requirements.txt
	@printf "\n$(OK) $(BOLD)Installation complete$(RESET)\n"
	@printf "\n$(BOLD)Recommended next steps:$(RESET)\n"
	@printf "  1. $(CYAN)cp .env.example .env$(RESET)  — fill in your API keys and passwords\n"
	@printf "  2. $(CYAN)make db-up$(RESET)             — start Docker services\n"
	@printf "  3. $(CYAN)make migrate$(RESET)           — apply database migrations\n"
	@printf "  4. $(CYAN)make validate$(RESET)          — confirm everything is ready\n"
	@printf "  5. $(CYAN)make run$(RESET)               — start the app\n\n"

# ─────────────────────────────────────────────────────────────
# DATABASE
# ─────────────────────────────────────────────────────────────
db-up:
	@printf "$(CYAN)Starting Docker services (MySQL, ChromaDB, NebulaGraph)...$(RESET)\n"
	@$(COMPOSE) up -d
	@printf "$(CYAN)Waiting for MySQL to be ready$(RESET)"
	@for i in $$(seq 1 30); do \
		if $(COMPOSE) exec -T mysql mysqladmin ping -h 127.0.0.1 --silent 2>/dev/null; then \
			printf "\n$(OK) MySQL is ready\n"; \
			break; \
		fi; \
		printf "."; \
		sleep 2; \
	done
	@printf "$(OK) All services started\n"
	@printf "  MySQL      → localhost:3306\n"
	@printf "  phpMyAdmin → http://localhost:8080\n"
	@printf "  ChromaDB   → http://localhost:8000\n"
	@printf "  NebulaGraph → localhost:9669\n\n"

db-down:
	@printf "$(CYAN)Stopping Docker services...$(RESET)\n"
	@$(COMPOSE) down
	@printf "$(OK) All services stopped\n"

migrate:
	@printf "$(CYAN)Running Alembic migrations...$(RESET)\n"
	@$(ALEMBIC) upgrade head
	@printf "$(OK) Migrations applied\n"

db-reset:
	@printf "\n$(RED)$(BOLD)⚠  WARNING: This will drop and recreate the ENTIRE database schema.$(RESET)\n"
	@printf "$(RED)   All data will be permanently lost.$(RESET)\n\n"
	@printf "Type $(BOLD)yes$(RESET) to confirm: "; read confirm; \
	[ "$$confirm" = "yes" ] || { printf "Aborted.\n"; exit 1; }
	@printf "$(CYAN)Downgrading to base...$(RESET)\n"
	@$(ALEMBIC) downgrade base
	@printf "$(CYAN)Upgrading to head...$(RESET)\n"
	@$(ALEMBIC) upgrade head
	@printf "$(OK) Database reset complete\n"

# ─────────────────────────────────────────────────────────────
# RUN
# ─────────────────────────────────────────────────────────────
run:
	@printf "$(CYAN)Starting F-LLM on http://localhost:$(APP_PORT)$(RESET)\n"
	@printf "$(CYAN)Press Ctrl+C to stop$(RESET)\n\n"
	@$(PYTHON) app.py

# ─────────────────────────────────────────────────────────────
# EVALUATE
# ─────────────────────────────────────────────────────────────
EVAL_RESULTS := evaluation/results

evaluate:
	@printf "$(CYAN)Starting F-LLM evaluation pipeline...$(RESET)\n"
	@printf "$(CYAN)Results will be saved to $(BOLD)$(EVAL_RESULTS)/$(RESET)\n\n"
	@$(PYTHON) evaluation/evaluate.py

evaluate-clean:
	@printf "$(YELLOW)Removing evaluation results and visualisations...$(RESET)\n"
	@if [ -d "$(EVAL_RESULTS)" ]; then \
		rm -rf $(EVAL_RESULTS); \
		printf "  $(OK) Deleted $(EVAL_RESULTS)/\n"; \
	else \
		printf "  $(WARN) $(EVAL_RESULTS)/ does not exist — nothing to clean\n"; \
	fi

# ─────────────────────────────────────────────────────────────
# TEST
# ─────────────────────────────────────────────────────────────
test: test-unit test-integration
	@printf "\n$(OK) $(BOLD)All tests complete$(RESET)\n"

test-unit:
	@printf "\n$(CYAN)Running unit tests...$(RESET)\n"
	@$(PYTEST) backend/src -v --tb=short -q

test-integration:
	@printf "\n$(CYAN)Running integration tests...$(RESET)\n"
	@$(PYTEST) backend/tests_integration -v --tb=short -q

test-ui:
	@printf "\n$(CYAN)Running Playwright UI tests...$(RESET)\n"
	@$(PYTEST) test_ui -v --tb=short -q

test-cov:
	@printf "\n$(CYAN)Running unit tests with coverage...$(RESET)\n"
	@$(PYTEST) backend/src \
		--cov=backend \
		--cov-report=term-missing \
		--cov-report=html:htmlcov \
		-q
	@printf "\n$(OK) Coverage report → $(BOLD)htmlcov/index.html$(RESET)\n"

# ─────────────────────────────────────────────────────────────
# CODE QUALITY
# ─────────────────────────────────────────────────────────────
lint:
	@printf "$(CYAN)Linting with ruff...$(RESET)\n"
	@$(VENV)/bin/ruff check backend/ frontend/ app.py || true

format:
	@printf "$(CYAN)Formatting with ruff...$(RESET)\n"
	@$(VENV)/bin/ruff format backend/ frontend/ app.py
	@$(VENV)/bin/ruff check --fix backend/ frontend/ app.py || true
	@printf "$(OK) Formatting complete\n"

# ─────────────────────────────────────────────────────────────
# MISC
# ─────────────────────────────────────────────────────────────
logs:
	@$(COMPOSE) logs -f

clean:
	@printf "$(YELLOW)Removing venv and caches...$(RESET)\n"
	@rm -rf $(VENV)
	@find . -type d -name __pycache__  ! -path "./.git/*" -exec rm -rf {} + 2>/dev/null; true
	@find . -type d -name .pytest_cache ! -path "./.git/*" -exec rm -rf {} + 2>/dev/null; true
	@find . -type d -name htmlcov       ! -path "./.git/*" -exec rm -rf {} + 2>/dev/null; true
	@find . -name "*.pyc"               ! -path "./.git/*" -delete 2>/dev/null; true
	@find . -name ".coverage"           ! -path "./.git/*" -delete 2>/dev/null; true
	@printf "$(OK) Clean\n"
