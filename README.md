# FactoryLLM - An Open Safe AI Sandbox for Evaluating LLM in Smart Factories

> **An Open Safe AI Sandbox for Evaluating Large Language Models in Smart Factories**

[![Python 3.10](https://img.shields.io/badge/python-3.10-blue.svg)](https://www.python.org/downloads/release/python-3100/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Docker](https://img.shields.io/badge/docker-required-blue.svg)](https://www.docker.com/)
[![NiceGUI](https://img.shields.io/badge/UI-NiceGUI-cyan.svg)](https://nicegui.io/)

---

## Overview

**F-LLM** is a research platform designed to benchmark and compare Large Language Models (LLMs) across multiple docs in smart factory contexts. It provides:

- A **conversational playground** to interact with 20+ LLMs using different prompting strategies
- A **Retrieval-Augmented Generation (RAG)** pipeline supporting vector search (ChromaDB)
- A **fully automated evaluation pipeline** measuring context precision, recall, faithfulness, and response groundedness using RAGAS and NVIDIA NeMo metrics
- A **reproducible environment** via Docker, Makefile, and locked dependency files

---

## Prerequisites

| Requirement       | Version                | Notes                                    |
| ----------------- | ---------------------- | ---------------------------------------- |
| Python            | **3.10 exactly** | Other versions are not supported         |
| Docker Desktop    | 4.x+                   | Must be running before `make db-up`    |
| Git               | Any                    | For cloning the repository               |
| MySQL client libs | System-level           | Only needed if connecting without Docker |

> **Windows users:** All `make` commands have PowerShell equivalents — use `.\make.ps1 <target>` instead.

---

## Installation

### 1 — Clone the Repository

```bash
git clone https://github.com/DigitalInnovationLab/Factory-LLM
cd Factory-LLM
```

### 2 — Create the Virtual Environment & Install Dependencies

**Linux / macOS / Git Bash / WSL:**

```bash
make install
```

**Windows PowerShell:**

```powershell
.\make.ps1 install
```

This will:

- Create a `.fllm/` virtual environment using Python 3.10
- Upgrade `pip`
- Install all packages from `requirements.txt`

### 3 — Manual Installation (if `make` is unavailable)

```bash
python3.10 -m venv .fllm
source .fllm/bin/activate          # Windows: .fllm\Scripts\activate
pip install --upgrade pip
pip install -r requirements.txt
```

---

## Configuration

### 1 — Copy the environment template

```bash
cp .env.example .env
```

### 2 — Fill in your `.env` file

```dotenv
# ── Application ──────────────────────────────────────────────
APP_ENV=development

# ── MySQL ─────────────────────────────────────────────────────
MYSQL_PASSWORD=your_mysql_password
DB_CONNECTION_SYNC=mysql+pymysql://root:your_mysql_password@localhost:3306/f-llm
DB_CONNECTION=mysql+asyncmy://root:your_mysql_password@localhost:3306/f-llm

# ── ChromaDB (Vector Store) ───────────────────────────────────
CHROMA_HOST=localhost
CHROMA_PORT=8000
CHROMA_TOKEN=your_chroma_auth_token
CHROMA_SERVER_AUTHN_CREDENTIALS=your_chroma_auth_token

# ── NebulaGraph (Knowledge Graph) ────────────────────────────
NEBULA_USER=root
NEBULA_PASSWORD=nebula
NEBULA_ADDRESS=localhost:9669

# ── LLM API Keys ─────────────────────────────────────────────
OPENAI_API_KEY=sk-...
GOOGLE_API_KEY=AIza...
OPENROUTER_API_KEY=sk-or-...
GROQ_API_KEY=gsk_...         # Optional
```

> **Important:** `DB_CONNECTION_SYNC` must use `mysql+pymysql://` (not `mysql://`) for Alembic migration compatibility.

### 3 — Validate your setup

```bash
make validate          # Linux / macOS / Git Bash
.\make.ps1 validate    # Windows PowerShell
```

Expected output:

```
[ Python ]
  ✓ Python 3.10.x

[ Virtual Environment ]
  ✓ Venv found at .fllm/
  ✓ Python: Python 3.10.x
  Checking key packages:
    ✓ nicegui           2.x.x
    ✓ fastapi           0.x.x
    ...

[ Docker ]
  ✓ Docker daemon is running

[ Environment Variables ]
  ✓ .env file found
  ✓ APP_ENV              deve****
  ✓ OPENAI_API_KEY       sk-p****
  ...

[ Docker Services ]
  ✓ mysql     is running
  ✓ chromadb  is running

[ Database Connectivity ]
  ✓ MySQL connection successful

[ Alembic Migration State ]
  ✓ Database is at head: 0001_initial_schema (head)
```

---

## Database Setup

### Start all services (MySQL, ChromaDB, NebulaGraph)

```bash
make db-up             # Linux / macOS / Git Bash
.\make.ps1 db-up       # Windows PowerShell
```

Services started:

| Service     | URL                       | Purpose                       |
| ----------- | ------------------------- | ----------------------------- |
| MySQL       | `localhost:3306`        | Primary relational database   |
| phpMyAdmin  | `http://localhost:8080` | MySQL web UI                  |
| ChromaDB    | `http://localhost:8000` | Vector store for RAG          |
| NebulaGraph | `localhost:9669`        | Knowledge graph for Graph-RAG |

### Apply Database Migrations

```bash
make migrate             # Linux / macOS / Git Bash
.\make.ps1 migrate       # Windows PowerShell
```

This runs `alembic upgrade head` — applying the initial schema (`users`, `tasks`, `chats`, `messages`, `files`, `feedback`, `reasoning_steps` tables).

### Stop all services

```bash
make db-down
```

### Reset database (destructive — all data lost)

```bash
make db-reset
```

---

## Running the Application

```bash
make run               # Linux / macOS / Git Bash
.\make.ps1 run         # Windows PowerShell
```

Open your browser at: **[http://localhost:8888](http://localhost:8888)**

### First-time walkthrough

1. **Login** — Enter any valid email address (account is created automatically)
2. **Select a Topic** — Create a topic.
3. **Configure** — Configure the LLM model, prompting technique and RAG technique.
4. **Upload Documents** — Upload PDF files.
5. **Chat** — Ask questions.
6. **Review Reasoning** — Expand the reasoning trace to see intermediate thoughts

---

## Evaluation Pipeline

The evaluation pipeline measures RAG quality across 6 metrics using **RAGAS** and **NVIDIA NeMo** frameworks.

### Run Evaluation

```bash
make evaluate              # Linux / macOS / Git Bash
.\make.ps1 evaluate        # Windows PowerShell
```

You will be prompted:

```
┌─────────────────────────────────────────┐
│        F-LLM Evaluation Runner          │
└─────────────────────────────────────────┘
Enter chat ID(s) to evaluate (comma-separated, e.g. 1,2,3): 1,2,3
  ✓ Evaluating chat IDs: [1, 2, 3]
```

### Metrics Computed

| Metric                          | Framework   | Description                                                 |
| ------------------------------- | ----------- | ----------------------------------------------------------- |
| **Context Precision**     | RAGAS       | Are retrieved documents ranked by relevance to the query?   |
| **Context Recall**        | RAGAS       | Are all required documents retrieved for the answer?        |
| **Response Relevancy**    | RAGAS       | Is the generated answer relevant to the user's question?    |
| **Faithfulness**          | RAGAS       | Is every claim in the answer grounded in retrieved context? |
| **Context Relevance**     | NVIDIA NeMo | Overall relevance of context to the question                |
| **Response Groundedness** | NVIDIA NeMo | Is the response fully supported by provided contexts?       |


### Output Files

All outputs are saved to `evaluation/results/`:

| File                          | Description                                                |
| ----------------------------- | ---------------------------------------------------------- |
| `fig2_radar_comparison.png` | Radar chart comparing all models across all 6 metrics      |
| `fig3_boxplots.png`         | Box plots showing score distributions per metric per model |
| `fig4_summary_heatmap.png`  | Mean score heatmap (models × metrics, colour-coded)       |
| `evaluation.sqlite`         | Raw scores database for further analysis                   |
| `evaluation.log`            | Detailed evaluation log                                    |

### Clean evaluation results

```bash
make evaluate-clean        # Deletes evaluation/results/ entirely
.\make.ps1 evaluate-clean  # Windows
```

---

## Project Structure

```
F-LLM/
│
├── app.py                          # Application entry point (NiceGUI + FastAPI)
├── Makefile                        # Build automation (Linux / macOS / Git Bash)
├── make.ps1                        # Build automation (Windows PowerShell)
├── requirements.txt                # Python dependencies
├── requirements.lock.txt           # Locked dependency versions
├── alembic.ini                     # Alembic configuration
├── dockercompose.database.yml      # Docker services (MySQL, ChromaDB, NebulaGraph)
├── .env.example                    # Environment variable template
│
├── backend/
│   ├── alembic/
│   │   ├── env.py                  # Migration runner (pymysql URL fix included)
│   │   └── versions/
│   │       └── 0001_initial_schema.py   # Single squashed migration
│   │
│   └── src/
│       ├── models/                 # SQLAlchemy ORM models
│       │   ├── user.py             # User entity
│       │   ├── chat.py             # Chat sessions
│       │   ├── message.py          # Chat messages (USER / ASSISTANT)
│       │   ├── task.py             # LLM tasks / topics
│       │   ├── file.py             # Uploaded files
│       │   ├── feedback.py         # User feedback
│       │   └── reasoning_step.py   # LLM reasoning traces
│       │
│       ├── services/               # Business logic
│       │   ├── ask.py              # LLM orchestration (main chat handler)
│       │   ├── chat.py             # Chat CRUD
│       │   ├── rag.py              # Vector + Graph retrieval
│       │   ├── etl.py              # Document ingestion (PDF → vectors)
│       │   ├── file.py             # File management
│       │   ├── task.py             # Task management
│       │   ├── user.py             # User authentication
│       │   ├── feedback.py         # Feedback submission
│       │   └── cache.py            # Response caching
│       │
│       ├── llm/                    # LLM integration
│       │   ├── models.py           # LlmFactory — builds LLM client per model
│       │   └── llm_utils.py        # Shared LLM helpers
│       │
│       ├── prompts/                # Prompt engineering
│       │   ├── prompter/           # Prompt template generation
│       │   ├── parser/             # Response parsing
│       │   ├── operations/         # Graph of Operations (GoO) framework
│       │   ├── controller/         # GoO execution controller
│       │   └── techniques/         # I/O, CoT, ToT, GoT implementations
│       │
│       ├── constants/              # Enums
│       │   ├── llm.py              # LlmModel enum
│       │   ├── rag.py              # RagTechnique enum
│       │   └── prompt.py           # Technique enum
│       │
│       └── llamaindex_extensions/
│           └── pdftextimagereader.py   # Multi-modal PDF reader (text + images)
│
├── frontend/
│   ├── pages/
│   │   ├── login_interface.py      # Login page (/)
│   │   ├── conv_interface.py       # Conversation history (/)
│   │   ├── task_interface.py       # Topic selector (/topic)
│   │   └── chat_interface.py       # Chat UI (/chat/<id>)
│   │
│   └── components/
│       ├── auth_middleware.py      # Session + auth guard
│       ├── navbar.py               # Navigation bar
│       ├── message.py              # Message bubble components
│       ├── task.py                 # Task card rendering
│       ├── feedback.py             # Feedback modal
│       ├── reasoning.py            # Reasoning trace display
│       └── css/                    # Custom stylesheets
│
├── evaluation/
│   ├── evaluate.py                 # Full evaluation pipeline
│   ├── evaluation.sqlite           # Scores database (generated)
│   ├── evaluation.log              # Evaluation log (generated)
│   └── results/                    # Visualisations (generated)
│       ├── fig2_radar_comparison.png
│       ├── fig3_boxplots.png
│       └── fig4_summary_heatmap.png
│
└── test_ui/                        # Playwright end-to-end tests
```

---

## Supported LLM Models

| Provider             | Model            | Identifier           |
| -------------------- | ---------------- | -------------------- |
| **OpenAI**     | GPT-3.5 Turbo    | `gpt-3.5-turbo`    |
|                      | GPT-4            | `gpt-4`            |
|                      | GPT-4o           | `gpt-4o`           |
|                      | GPT-4o Mini      | `gpt-4o-mini`      |
| **Google**     | Gemini 1.5 Pro   | `gemini-1.5-pro`   |
|                      | Gemini 1.5 Flash | `gemini-1.5-flash` |
|                      | Gemini 2.0 Flash | `gemini-2.0-flash` |
|                      | Gemini 2.5 Pro   | `gemini-2.5-pro`   |
| **DeepSeek**   | DeepSeek-v3      | `deepseek-v3`      |
|                      | DeepSeek-r1      | `deepseek-r1`      |
|                      | DeepSeek-r1-zero | `deepseek-r1-zero` |
| **Meta**       | Llama-4 Maverick | `llama-4-maverick` |
|                      | Llama-4 Scout    | `llama-4-scout`    |
| **Alibaba**    | QWen-3 235B      | `qwen-3-235b`      |
| **Google**     | Gemma-3 27B      | `gemma-3-27b`      |
| **OpenRouter** | Quasar Alpha     | `quasar-alpha`     |

---

## What to Look For (Key Results)

When reading evaluation outputs, focus on the following:

### 1. Radar Chart (`fig2_radar_comparison.png`)

- **Larger polygon area** = better overall performance
- Look for which model consistently covers all 6 axes

### 2. Box Plots (`fig3_boxplots.png`)

- **Narrow box + high median** = consistent and accurate model
- **Wide box or low median** = unstable or poor performance on that metric
- Compare spread across models for the same metric to assess reliability

### 3. Heatmap (`fig4_summary_heatmap.png`)

- **Green cells** = high mean score (> 0.7)
- **Red cells** = poor performance (< 0.3)
- Identify which model × metric combinations are problematic
- Faithfulness and Context Recall tend to be the most discriminating metrics

### 4. Expected Observations

- **GoT > ToT > CoT > I/O** in reasoning-heavy Q&A
- **Vector RAG** outperforms no-RAG on context-dependent questions
- **Graph RAG** shows advantage on multi-hop relational queries
- Larger models (GPT-4o, Gemini 2.5 Pro) score higher on Faithfulness
- Smaller/faster models (Gemini Flash, GPT-4o-mini) trade faithfulness for speed

---

## Testing

```bash
# Run all tests (unit + integration)
make test

# Unit tests only
make test-unit

# Integration tests (requires running DB)
make test-integration

# Playwright UI tests (requires running app)
make test-ui

# Unit tests + HTML coverage report
make test-cov
# Open: htmlcov/index.html
```

---

## Troubleshooting


### `RuntimeError: Expected ASGI message 'websocket.accept'...`

Version mismatch between `python-engineio` and `uvicorn`. Reinstall from the locked requirements:

```bash
.fllm/bin/pip install -r requirements.lock.txt
```

### Alembic: `Nothing to be done` / already at head

The squashed migration may already be applied. Check state:

```bash
.fllm/bin/alembic current
# If output shows no revision, stamp it:
.fllm/bin/alembic stamp 0001_initial_schema
```

### MySQL connection fails in `make validate`

- Ensure Docker containers are running: `make db-up`
- Verify `MYSQL_PASSWORD` in `.env` matches `MYSQL_ROOT_PASSWORD` in `dockercompose.database.yml`
- Wait 10–15 seconds after `make db-up` for MySQL to fully initialise

## Citation

If you use this work in your research, please cite:

```bibtex
@inproceedings{fllm2026indin,
  title     = {<title>},
  author    = {<Author Names>},
  booktitle = {<booktitle>},
  year      = {<year>},
  pages     = {<pages>},
  doi       = {<doi>}
}
```

---

