# Fed-LLM project

## Overview

This repository contains:

### FOMC Communications (`data/fed-comms/`)
- **Statements**: Policy statements from FOMC meetings
- **Minutes**: Detailed meeting minutes 
- **Press Conferences**: Transcripts from Chair press conferences (2011+)
- **Speeches**: Individual speeches by FOMC members (2000-2025)

All FOMC data is saved in both `raw/` and `clean/` formats with consistent JSON structure.

### Macroeconomic Data (`data/macro-releases/`)
- Economic indicators and releases (PCE, CPI, Payroll, GDP, etc.)
- *Coming soon*

### News Articles (`data/news/`)
- Financial news related to monetary policy
- *Coming soon*

### Scripts (`scripts/scraping/`)
- Web scrapers for collecting data from various sources

## Project Structure

```
fed-llm/
├── scripts/
│   └── scraping/          # Web scrapers
│       ├── scrape_statements.py
│       ├── scrape_minutes.py
│       ├── scrape_press_conferences.py
│       └── scrape_speeches.py
├── data/
│   ├── fed-comms/         # FOMC communications
│   │   ├── statements/
│   │   ├── minutes/
│   │   ├── press-confs/
│   │   └── speeches/
│   ├── macro-releases/    # Macroeconomic data
│   └── news/              # News articles
├── pyproject.toml         # Project dependencies
└── README.md
```

## Setup

This project uses [uv](https://github.com/astral-sh/uv) for dependency management.

1. **Install uv** (one-time setup):
   ```bash
   # Windows
   powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
   
   # macOS/Linux
   curl -LsSf https://astral.sh/uv/install.sh | sh
   ```

2. **Create environment and install dependencies**:
   ```bash
   uv sync
   ```

3. **Adding new packages** (as needed):
   ```bash
   uv add scipy  # Adds to pyproject.toml and installs
   ```

The virtual environment will auto-activate when you open a terminal in VS Code/Cursor.