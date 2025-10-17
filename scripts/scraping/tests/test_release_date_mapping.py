"""Test script to verify release date mapping extraction."""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from scrape_minutes import FOMCMinutesScraper

def main():
    """Test the release date mapping."""
    print("Testing release date mapping extraction...")
    print("=" * 60)
    
    # Create scraper (this will build the mapping)
    scraper = FOMCMinutesScraper()
    
    print("\n" + "=" * 60)
    print(f"Total meetings mapped: {len(scraper.release_date_mapping)}")
    print("=" * 60)
    
    # Test a few known dates from 1993
    test_dates = [
        "19930203",  # Should be "March 26, 1993"
        "19930323",  # Should be "May 21, 1993"
        "19930518",  # Should be "July 9, 1993"
        "19931116",  # Should be "December 23, 1993"
        "20200129",  # 2020 meeting
        "20240131",  # Recent meeting
    ]
    
    print("\nSample release dates:")
    print("-" * 60)
    for date in test_dates:
        release_date = scraper.release_date_mapping.get(date)
        if release_date:
            print(f"{date}: {release_date}")
        else:
            print(f"{date}: NOT FOUND")
    
    # Show all 1993 meetings
    print("\nAll 1993 meetings:")
    print("-" * 60)
    for date, release in sorted(scraper.release_date_mapping.items()):
        if date.startswith("1993"):
            print(f"{date}: {release}")
    
    # Show statistics by year
    print("\nMeetings mapped by year:")
    print("-" * 60)
    year_counts = {}
    for date in scraper.release_date_mapping.keys():
        year = date[:4]
        year_counts[year] = year_counts.get(year, 0) + 1
    
    for year in sorted(year_counts.keys()):
        print(f"{year}: {year_counts[year]} meetings")

if __name__ == "__main__":
    main()

