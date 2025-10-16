"""Quick script to read and display test JSON files."""

import json
from pathlib import Path

# Get the project root (two levels up from this script)
project_root = Path(__file__).parent.parent.parent

# Test dates
dates = ["20070131", "20240612"]

json_file = project_root / "data" / "fed-comms" / "minutes" / "clean" / f"minutes{dates[0]}.json"

with open(json_file, 'r', encoding='utf-8') as f:
    data = json.load(f)

print(data)

