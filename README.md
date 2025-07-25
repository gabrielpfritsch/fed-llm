# Fed-LLM project

## Overview

This repository contains:

### FOMC Communications (`fed-comms/`)
- **Statements**: Policy statements from FOMC meetings
- **Minutes**: Detailed meeting minutes 
- **Press Conferences**: Transcripts from Chair press conferences (2011+)
- **Speeches**: Individual speeches by FOMC members (2000-2025)

### Economic Data (`data/`)
- Macro & financial data (PCE, CPI, Payroll, S&P500, etc.)
- *Coming soon*

### News articles (`news/`)
- Reuters articles related to monetary policy
- *Coming soon*

## Dataset

The current dataset includes:
- FOMC member speeches
- Meeting minutes
- Press conference transcripts
- Complete collection of FOMC statements

All FOMC data is saved in both raw and clean formats with consistent JSON structure.

## Usage

Run individual scrapers:

```bash
python fed-comms/scrape_statements.py
python fed-comms/scrape_minutes.py
python fed-comms/scrape_press_conferences.py
python fed-comms/scrape_speeches.py
```

## Data Structure

Each scraper creates `raw/` and `clean/` directories containing:
- Raw HTML/PDF files for backup
- Clean JSON files with structured data (date, title, text, etc.)