from scrape_statements import FOMCStatementScraper
import os

# Test with just a few recent dates
test_dates = ["20240131", "20240320", "20240501"]

scraper = FOMCStatementScraper() 

print("Testing scraper with recent dates...")
for date in test_dates:
    print(f"\nTesting {date}:")
    success = scraper.scrape_statement(date)
    if success:
        print(f"SUCCESS for {date}")
        # Check files exist
        raw_file = f"statements/raw/statement{date}.html"
        json_file = f"statements/clean/statement{date}.json"
        print(f"Raw file exists: {os.path.exists(raw_file)}")
        print(f"JSON file exists: {os.path.exists(json_file)}")
    else:
        print(f"FAILED for {date}")