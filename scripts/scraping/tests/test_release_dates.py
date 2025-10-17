"""Test the release dates mapping functionality."""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from scripts.scraping.scrape_minutes import FOMCMinutesScraper

print("Testing release dates mapping...\n")
print("=" * 80)

scraper = FOMCMinutesScraper()

# Fetch the mapping
release_dates_map = scraper.fetch_release_dates_mapping()

print("=" * 80)
print("\nSample of mapped dates:")
print("=" * 80)

# Show a sample of dates from different years
sample_dates = [
    '19930203',  # 1993
    '19960130',  # 1996
    '20000202',  # 2000
    '20070131',  # 2007
    '20100127',  # 2010
    '20150128',  # 2015
    '20200129',  # 2020
    '20240731',  # 2024
    '20250730',  # 2025
]

for date in sample_dates:
    if date in release_dates_map:
        print(f"{date}: {release_dates_map[date]}")
    else:
        print(f"{date}: NOT FOUND")

print("\n" + "=" * 80)
print(f"Total dates mapped: {len(release_dates_map)}")
print(f"Expected dates: 261")
print(f"Coverage: {len(release_dates_map)/261*100:.1f}%")

