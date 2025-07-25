# Fed-LLM project

## Overview

This repository contains scrapers for collecting comprehensive FOMC (Federal Open Market Committee) data from the Federal Reserve website, including:

- **Statements**: Policy statements from FOMC meetings
- **Minutes**: Detailed meeting minutes 
- **Press Conferences**: Transcripts from Chair press conferences (2011+)
- **Speeches**: Individual speeches by FOMC members (2000-2025)

## Dataset

The scraped dataset includes:
- FOMC member speeches
- Meeting minutes
- Press conference transcripts
- Complete collection of FOMC statements

All data is saved in both raw and clean formats with consistent JSON structure.

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