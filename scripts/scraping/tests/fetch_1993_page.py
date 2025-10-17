"""Simple script to fetch and save the 1993 FOMC historical page."""

import requests

url = "https://www.federalreserve.gov/monetarypolicy/fomchistorical1993.htm"

print(f"Fetching: {url}")
response = requests.get(url)

if response.status_code == 200:
    with open("scripts/scraping/tests/fomchistorical1993.html", "w", encoding="utf-8") as f:
        f.write(response.text)
    print("✅ Saved to scripts/scraping/tests/fomchistorical1993.html")
else:
    print(f"❌ Failed with status code: {response.status_code}")

