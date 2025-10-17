"""Test script to verify a single meeting gets the correct release date."""

import sys
from pathlib import Path
import json

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from scrape_minutes import FOMCMinutesScraper

def main():
    """Test scraping a single meeting."""
    print("Testing single meeting scrape with release date mapping...")
    print("=" * 60)
    
    # Create scraper
    scraper = FOMCMinutesScraper()
    
    # Test date from 1993 that should have release date "March 26, 1993"
    test_date = "19930203"
    expected_release_date = "March 26, 1993"
    
    print(f"\nTesting meeting date: {test_date}")
    print(f"Expected release date: {expected_release_date}")
    
    # Check mapping
    mapped_date = scraper.release_date_mapping.get(test_date)
    print(f"Mapped release date: {mapped_date}")
    
    if mapped_date == expected_release_date:
        print("✓ Mapping is correct!")
    else:
        print("✗ Mapping is incorrect!")
        return
    
    # Scrape the meeting
    print(f"\nAttempting to scrape meeting {test_date}...")
    success = scraper.scrape_minutes(test_date)
    
    if success:
        print("✓ Scraping successful!")
        
        # Read the JSON to verify the release date
        json_file = scraper.clean_dir / f"minutes{test_date}.json"
        if json_file.exists():
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            print(f"\nJSON contents:")
            print(f"  meeting_date: {data.get('meeting_date')}")
            print(f"  release_date: {data.get('release_date')}")
            print(f"  type: {data.get('type')}")
            print(f"  text length: {len(data.get('text', ''))} chars")
            
            # Verify the release date was converted correctly
            # Expected: March 26, 1993 -> 1993-03-26
            expected_json_date = "1993-03-26"
            if data.get('release_date') == expected_json_date:
                print(f"\n✓ Release date correctly formatted as {expected_json_date}")
            else:
                print(f"\n✗ Release date is {data.get('release_date')}, expected {expected_json_date}")
        else:
            print("✗ JSON file not found!")
    else:
        print("✗ Scraping failed!")

if __name__ == "__main__":
    main()

