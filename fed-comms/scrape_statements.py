import requests
import json
import os
import re
from datetime import datetime, timedelta
from bs4 import BeautifulSoup
import time
from urllib.parse import urljoin, urlparse

class FOMCScraper:
    def __init__(self):
        self.base_url = "https://www.federalreserve.gov"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        
        # Create statements directory if it doesn't exist
        if not os.path.exists('statements'):
            os.makedirs('statements')
    
    def get_fomc_statement_urls_from_calendar(self):
        """
        Extract actual FOMC statement URLs from the official calendar pages
        """
        statement_urls = {}
        
        # Get URLs from modern calendar pages (2020-2025)
        calendar_years = [2020, 2021, 2022, 2023, 2024, 2025]
        
        for year in calendar_years:
            calendar_url = f"{self.base_url}/monetarypolicy/fomccalendars.htm"
            try:
                print(f"Fetching calendar page...")
                response = self.session.get(calendar_url, timeout=10)
                if response.status_code == 200:
                    soup = BeautifulSoup(response.text, 'html.parser')
                    
                    # Look for statement links
                    links = soup.find_all('a', href=True)
                    for link in links:
                        href = link.get('href')
                        if href and 'monetary' in href and ('statement' in link.text.lower() or 'pdf' in href.lower()):
                            full_url = urljoin(self.base_url, href)
                            
                            # Extract date from URL
                            date_match = re.search(r'monetary(\d{8})', href)
                            if date_match:
                                date_str = date_match.group(1)
                                statement_urls[date_str] = full_url
                                
            except Exception as e:
                print(f"Error fetching calendar for {year}: {str(e)}")
        
        return statement_urls
    
    def get_fomc_meeting_dates(self):
        """
        Get FOMC meeting dates from various sources including historical calendars
        and known meeting patterns. FOMC typically meets 8 times per year.
        """
        # First try to get actual URLs from calendar
        calendar_urls = self.get_fomc_statement_urls_from_calendar()
        
        # Known FOMC meeting dates (comprehensive list based on historical patterns)
        known_meetings = [
            # 2000
            "20000202", "20000321", "20000516", "20000628", "20000822", "20001003", "20001115", "20001219",
            # 2001
            "20010103", "20010131", "20010320", "20010501", "20010627", "20010821", "20011002", "20011106", "20011211",
            # 2002
            "20020130", "20020319", "20020507", "20020626", "20020813", "20020924", "20021106", "20021210",
            # 2003
            "20030129", "20030318", "20030506", "20030625", "20030812", "20030916", "20031028", "20031209",
            # 2004
            "20040128", "20040316", "20040504", "20040630", "20040810", "20040921", "20041110", "20041214",
            # 2005
            "20050202", "20050322", "20050503", "20050630", "20050809", "20050920", "20051101", "20051213",
            # 2006
            "20060131", "20060328", "20060510", "20060629", "20060808", "20060920", "20061025", "20061212",
            # 2007
            "20070131", "20070321", "20070509", "20070628", "20070807", "20070918", "20071031", "20071211",
            # 2008
            "20080130", "20080318", "20080430", "20080625", "20080805", "20080916", "20081029", "20081216",
            # 2009
            "20090128", "20090318", "20090429", "20090624", "20090812", "20090923", "20091104", "20091216",
            # 2010
            "20100127", "20100316", "20100428", "20100623", "20100810", "20100921", "20101103", "20101214",
            # Add more precise dates based on actual FOMC schedules
        ]
        
        # Generate potential meeting dates for recent years (2011-2025)
        for year in range(2011, 2026):
            # More precise typical meeting months and dates based on historical patterns
            potential_dates = [
                # January/February meetings
                f"{year}01{27:02d}", f"{year}01{28:02d}", f"{year}01{29:02d}", f"{year}01{30:02d}", f"{year}01{31:02d}",
                f"{year}02{01:02d}", f"{year}02{02:02d}",
                # March meetings
                f"{year}03{15:02d}", f"{year}03{16:02d}", f"{year}03{17:02d}", f"{year}03{18:02d}", 
                f"{year}03{19:02d}", f"{year}03{20:02d}", f"{year}03{21:02d}", f"{year}03{22:02d}",
                # April/May meetings
                f"{year}04{27:02d}", f"{year}04{28:02d}", f"{year}04{29:02d}", f"{year}04{30:02d}",
                f"{year}05{01:02d}", f"{year}05{02:02d}", f"{year}05{03:02d}", f"{year}05{04:02d}", f"{year}05{05:02d}",
                # June meetings
                f"{year}06{09:02d}", f"{year}06{10:02d}", f"{year}06{11:02d}", f"{year}06{12:02d}",
                f"{year}06{13:02d}", f"{year}06{14:02d}", f"{year}06{15:02d}", f"{year}06{16:02d}",
                f"{year}06{17:02d}", f"{year}06{18:02d}",
                # July meetings
                f"{year}07{25:02d}", f"{year}07{26:02d}", f"{year}07{27:02d}", f"{year}07{28:02d}",
                f"{year}07{29:02d}", f"{year}07{30:02d}", f"{year}07{31:02d}",
                f"{year}08{01:02d}", f"{year}08{02:02d}",
                # September meetings
                f"{year}09{15:02d}", f"{year}09{16:02d}", f"{year}09{17:02d}", f"{year}09{18:02d}",
                f"{year}09{19:02d}", f"{year}09{20:02d}", f"{year}09{21:02d}", f"{year}09{22:02d}",
                # October/November meetings
                f"{year}10{28:02d}", f"{year}10{29:02d}", f"{year}10{30:02d}", f"{year}10{31:02d}",
                f"{year}11{01:02d}", f"{year}11{02:02d}", f"{year}11{03:02d}", f"{year}11{04:02d}",
                f"{year}11{05:02d}", f"{year}11{06:02d}", f"{year}11{07:02d}",
                # December meetings
                f"{year}12{12:02d}", f"{year}12{13:02d}", f"{year}12{14:02d}", f"{year}12{15:02d}",
                f"{year}12{16:02d}", f"{year}12{17:02d}", f"{year}12{18:02d}", f"{year}12{19:02d}",
            ]
            known_meetings.extend(potential_dates)
        
        # Combine calendar URLs dates with known dates
        all_dates = list(set(known_meetings + list(calendar_urls.keys())))
        
        return sorted(all_dates), calendar_urls
    
    def construct_statement_urls(self, date_str):
        """
        Construct possible URLs for FOMC statements given a date string (YYYYMMDD)
        """
        year = date_str[:4]
        
        urls = []
        
        # Modern URL format (2008-present)
        urls.append(f"{self.base_url}/newsevents/pressreleases/monetary{date_str}a.htm")
        
        # Older URL formats (2000-2008)
        urls.append(f"{self.base_url}/boarddocs/press/monetary/{year}/{date_str}/")
        urls.append(f"{self.base_url}/boarddocs/press/monetary/{year}/{date_str}/default.htm")
        urls.append(f"{self.base_url}/boarddocs/press/general/{year}/{date_str}/")
        urls.append(f"{self.base_url}/boarddocs/press/general/{year}/{date_str}/default.htm")
        urls.append(f"{self.base_url}/Boarddocs/press/general/{year}/{date_str}/default.htm")
        
        return urls
    
    def extract_text_from_html(self, html_content):
        """
        Extract the main text content from FOMC statement HTML
        """
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Remove script and style elements
        for script in soup(["script", "style"]):
            script.decompose()
        
        # Try to find the main content area
        content_areas = [
            soup.find('div', {'id': 'content'}),
            soup.find('div', {'class': 'col-xs-12'}),
            soup.find('div', {'class': 'content'}),
            soup.find('main'),
            soup.find('article'),
        ]
        
        content_div = None
        for area in content_areas:
            if area:
                content_div = area
                break
        
        if not content_div:
            content_div = soup
        
        # Extract text, preserving paragraph structure
        text_parts = []
        
        # Look for the actual statement content
        paragraphs = content_div.find_all(['p', 'div'])
        
        for para in paragraphs:
            text = para.get_text().strip()
            if text and len(text) > 30:  # Filter out very short snippets
                # Skip navigation and header elements
                if not any(skip_phrase in text.lower() for skip_phrase in [
                    'for immediate release', 'board of governors', 'federal reserve',
                    'main menu', 'search', 'navigation', 'last update', 'back to',
                    'press release', 'media inquiries'
                ]):
                    text_parts.append(text)
        
        # Join paragraphs with newlines
        full_text = '\n\n'.join(text_parts)
        
        # Clean up extra whitespace
        full_text = re.sub(r'\n\s*\n\s*\n', '\n\n', full_text)
        full_text = re.sub(r' +', ' ', full_text)
        
        return full_text.strip()
    
    def scrape_statement(self, date_str):
        """
        Scrape a single FOMC statement for the given date
        """
        urls = self.construct_statement_urls(date_str)
        
        for url in urls:
            try:
                print(f"Trying URL: {url}")
                response = self.session.get(url, timeout=10)
                
                if response.status_code == 200:
                    html_content = response.text
                    
                    # Check if this looks like a valid FOMC statement
                    if 'federal open market committee' in html_content.lower() or 'fomc' in html_content.lower():
                        text_content = self.extract_text_from_html(html_content)
                        
                        if text_content and len(text_content) > 100:  # Must have substantial content
                            # Create the JSON structure
                            statement_data = {
                                'date': date_str,
                                'type': 'statement',
                                'text': text_content,
                                'url': url,
                                'scraped_at': datetime.now().isoformat()
                            }
                            
                            return statement_data
                
            except Exception as e:
                print(f"Error fetching {url}: {str(e)}")
                continue
            
            # Small delay between requests
            time.sleep(0.5)
        
        return None
    
    def save_statement(self, statement_data):
        """
        Save statement data to JSON file
        """
        date_str = statement_data['date']
        filename = f"statements/statement{date_str}.json"
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(statement_data, f, indent=2, ensure_ascii=False)
        
        print(f"Saved: {filename}")
    
    def scrape_all_statements(self):
        """
        Scrape all FOMC statements from 2000 to present
        """
        meeting_dates = self.get_fomc_meeting_dates()
        successful_scrapes = 0
        failed_scrapes = 0
        
        print(f"Attempting to scrape {len(meeting_dates)} potential FOMC meeting dates...")
        
        for date_str in meeting_dates:
            # Check if file already exists
            filename = f"statements/statement{date_str}.json"
            if os.path.exists(filename):
                print(f"Skipping {date_str} - already exists")
                continue
            
            print(f"\nScraping FOMC statement for {date_str}...")
            
            statement_data = self.scrape_statement(date_str)
            
            if statement_data:
                self.save_statement(statement_data)
                successful_scrapes += 1
                print(f"✓ Successfully scraped {date_str}")
            else:
                failed_scrapes += 1
                print(f"✗ Failed to scrape {date_str}")
            
            # Respectful delay between requests
            time.sleep(1)
        
        print(f"\nScraping complete!")
        print(f"Successful: {successful_scrapes}")
        print(f"Failed: {failed_scrapes}")

def main():
    scraper = FOMCScraper()
    scraper.scrape_all_statements()

if __name__ == "__main__":
    main()