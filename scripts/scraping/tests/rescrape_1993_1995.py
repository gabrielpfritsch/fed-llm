"""Script to re-scrape 1993-1995 meetings to update release dates."""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from scrape_minutes import FOMCMinutesScraper

def main():
    """Re-scrape 1993-1995 meetings to update release dates."""
    print("Re-scraping 1993-1995 meetings to update release dates...")
    print("=" * 60)
    
    # Create scraper
    scraper = FOMCMinutesScraper()
    
    # Get all known dates
    all_dates = scraper.get_known_fomc_dates()
    
    # Filter for 1993-1995
    dates_to_scrape = [d for d in all_dates if d.startswith('1993') or d.startswith('1994') or d.startswith('1995')]
    
    print(f"\nFound {len(dates_to_scrape)} meetings from 1993-1995 to re-scrape")
    print("=" * 60)
    
    successful = 0
    failed = 0
    
    for i, date_str in enumerate(dates_to_scrape, 1):
        print(f"\n[{i}/{len(dates_to_scrape)}] {date_str}: Re-scraping...")
        
        # Check if we have a release date mapped
        release_date = scraper.release_date_mapping.get(date_str)
        if release_date:
            print(f"  Expected release date: {release_date}")
        else:
            print(f"  WARNING: No release date mapped for this meeting")
        
        if scraper.scrape_minutes(date_str):
            successful += 1
        else:
            failed += 1
            print(f"  FAILED to scrape {date_str}")
    
    print("\n" + "=" * 60)
    print(f"Re-scraping complete!")
    print(f"Successful: {successful}")
    print(f"Failed: {failed}")
    print(f"Total processed: {successful + failed}")

if __name__ == "__main__":
    main()

