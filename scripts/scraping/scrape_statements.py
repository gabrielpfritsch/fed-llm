import requests
import json
import os
import re
from datetime import datetime
from bs4 import BeautifulSoup
import time
from urllib.parse import urljoin

class FOMCStatementScraper:
    def __init__(self):
        self.base_url = "https://www.federalreserve.gov"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        
        # Create directories
        os.makedirs('data/fed-comms/statements/raw', exist_ok=True)
        os.makedirs('data/fed-comms/statements/clean', exist_ok=True)
    
    def get_known_fomc_dates(self):
        """
        Get comprehensive list of known FOMC meeting dates from 1993-2025
        Based on historical FOMC schedules and patterns
        """
        known_dates = [
            # 1994 (/fomc/{date}default.htm)
            "19940204", "19940322", "19940517", "19940816", "19940927", "19941115",
            # 1995 (/fomc/{date}default.htm)
            "19950201", "19950706", "19951219",
            # 1996 (/fomc/{date}DEFAULT.htm)
            "19960131",
            # 1997 (/boarddocs/press/general/{year}/{date}/)
            "19970325",  
            # 1998 (/boarddocs/press/general/{year}/{date}/)
            "19980929", "19981117",
            # 1999 (/boarddocs/press/general/{year}/{date}/)
            "19990518", "19990629", "19990824", "19991005", "19991116", "19991221",
            # 2000 (/boarddocs/press/general/{year}/{date}/)
            "20000202", "20000321", "20000516", "20000628", "20000822", "20001003", "20001115", "20001219",
            # 2001 (/boarddocs/press/general/{year}/{date}/)
            "20010131", "20010320", "20010515", "20010627", "20010821", "20011002", "20011106", "20011211",
            # 2002 (/boarddocs/press/general/{year}/{date}/ until 20020319 then /boarddocs/press/monetary/{year}/{date}/)
            "20020130", "20020319", "20020507", "20020626", "20020813", "20020924", "20021106", "20021210",
            # 2003 (/boarddocs/press/monetary/{year}/{date}/default.htm)
            "20030129", "20030318", "20030506", "20030625", "20030812", "20030916", "20031028", "20031209",
            # 2004 (/boarddocs/press/monetary/{year}/{date}/default.htm)
            "20040128", "20040316", "20040504", "20040630", "20040810", "20040921", "20041110", "20041214",
            # 2005 (/boarddocs/press/monetary/{year}/{date}/default.htm)
            "20050202", "20050322", "20050503", "20050630", "20050809", "20050920", "20051101", "20051213",
            # 2006 (/newsevents/pressreleases/monetary{date}a.htm)
            "20060131", "20060328", "20060510", "20060629", "20060808", "20060920", "20061025", "20061212",
            # 2007 (/newsevents/pressreleases/monetary{date}a.htm)
            "20070131", "20070321", "20070509", "20070628", "20070807", "20070918", "20071031", "20071211",
            # 2008 (/newsevents/pressreleases/monetary{date}a.htm)
            "20080130", "20080318", "20080430", "20080625", "20080805", "20080916", "20081029", "20081216",
            # 2009 (/newsevents/pressreleases/monetary{date}a.htm)
            "20090128", "20090318", "20090429", "20090624", "20090812", "20090923", "20091104", "20091216",
            # 2010 (/newsevents/pressreleases/monetary{date}a.htm)
            "20100127", "20100316", "20100428", "20100623", "20100810", "20100921", "20101103", "20101214",
            # 2011 (/newsevents/pressreleases/monetary{date}a.htm)
            "20110126", "20110315", "20110427", "20110622", "20110809", "20110921", "20111102", "20111213",
            # 2012 (/newsevents/pressreleases/monetary{date}a.htm)
            "20120125", "20120313", "20120425", "20120620", "20120801", "20120913", "20121024", "20121212",
            # 2013 (/newsevents/pressreleases/monetary{date}a.htm)
            "20130130", "20130320", "20130501", "20130619", "20130731", "20130918", "20131030", "20131218",
            # 2014 (/newsevents/pressreleases/monetary{date}a.htm)
            "20140129", "20140319", "20140430", "20140618", "20140730", "20140917", "20141029", "20141217",
            # 2015 (/newsevents/pressreleases/monetary{date}a.htm)
            "20150128", "20150318", "20150429", "20150617", "20150729", "20150917", "20151028", "20151216",
            # 2016 (/newsevents/pressreleases/monetary{date}a.htm)
            "20160127", "20160316", "20160427", "20160615", "20160727", "20160921", "20161102", "20161214",
            # 2017 (/newsevents/pressreleases/monetary{date}a.htm)
            "20170201", "20170315", "20170503", "20170614", "20170726", "20170920", "20171101", "20171213",
            # 2018 (/newsevents/pressreleases/monetary{date}a.htm)
            "20180131", "20180321", "20180502", "20180613", "20180801", "20180926", "20181108", "20181219",
            # 2019 (/newsevents/pressreleases/monetary{date}a.htm)
            "20190130", "20190320", "20190501", "20190619", "20190731", "20190918", "20191030", "20191211",
            # 2020 (/newsevents/pressreleases/monetary{date}a.htm)
            "20200129", "20200315", "20200429", "20200610", "20200729", "20200916", "20201105", "20201216",
            # 2021 (/newsevents/pressreleases/monetary{date}a.htm)
            "20210127", "20210317", "20210428", "20210616", "20210728", "20210922", "20211103", "20211215",
            # 2022 (/newsevents/pressreleases/monetary{date}a.htm)
            "20220126", "20220316", "20220504", "20220615", "20220727", "20220921", "20221102", "20221214",
            # 2023 (/newsevents/pressreleases/monetary{date}a.htm)
            "20230201", "20230322", "20230503", "20230614", "20230726", "20230920", "20231101", "20231213",
            # 2024 (/newsevents/pressreleases/monetary{date}a.htm)
            "20240131", "20240320", "20240501", "20240612", "20240731", "20240918", "20241107", "20241218",
            # 2025 (/newsevents/pressreleases/monetary{date}a.htm)
            "20250129", "20250319", "20250507", "20250618", "20250730"
        ]
        
        return sorted(known_dates)
    
    def construct_statement_urls(self, date_str):
        """
        Construct possible URLs for FOMC statements based on historical patterns
        """
        year = date_str[:4]
        year_int = int(year)
        
        urls = []
        
        # Modern format (2008-present) - most common
        urls.append(f"{self.base_url}/newsevents/pressreleases/monetary{date_str}a.htm")
        urls.append(f"{self.base_url}/newsevents/pressreleases/monetary{date_str}.htm")
        
        # Historical formats based on year
        if year_int <= 2001:
            # 2000-2001: Use general path
            urls.append(f"{self.base_url}/boarddocs/press/general/{year}/{date_str}/")
            urls.append(f"{self.base_url}/boarddocs/press/general/{year}/{date_str}/default.htm")
        elif year_int == 2002:
            # 2002: Mixed year - try both general and monetary
            urls.append(f"{self.base_url}/boarddocs/press/general/{year}/{date_str}/")
            urls.append(f"{self.base_url}/boarddocs/press/general/{year}/{date_str}/default.htm")
            urls.append(f"{self.base_url}/boarddocs/press/monetary/{year}/{date_str}/")
            urls.append(f"{self.base_url}/boarddocs/press/monetary/{year}/{date_str}/default.htm")
        elif year_int >= 2003 and year_int <= 2007:
            # 2003-2007: Use monetary path with default.htm
            urls.append(f"{self.base_url}/boarddocs/press/monetary/{year}/{date_str}/default.htm")
            urls.append(f"{self.base_url}/boarddocs/press/monetary/{year}/{date_str}/")
        else:
            # 2008+: Already covered by modern format above, but add fallback
            urls.append(f"{self.base_url}/boarddocs/press/monetary/{year}/{date_str}/default.htm")
            urls.append(f"{self.base_url}/boarddocs/press/monetary/{year}/{date_str}/")
        
        # Add case variations for older URLs
        if year_int <= 2007:
            urls.append(f"{self.base_url}/BoardDocs/Press/monetary/{year}/{date_str}/default.htm")
            urls.append(f"{self.base_url}/BoardDocs/Press/general/{year}/{date_str}/default.htm")
        
        return urls
    
    def save_raw_html(self, date_str, html_content, url):
        """
        Save raw HTML content to file
        """
        filename = f"data/fed-comms/statements/raw/statement{date_str}.html"
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(f"<!-- Source URL: {url} -->\n")
            f.write(f"<!-- Scraped: {datetime.now().isoformat()} -->\n")
            f.write(html_content)
        return filename
    
    def extract_statement_text(self, html_content):
        """
        Extract clean text from FOMC statement HTML
        """
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Remove scripts, styles, and navigation elements
        for element in soup(["script", "style", "nav", "header", "footer"]):
            element.decompose()
        
        # Check if this is a historical page (simpler HTML structure)
        is_historical = '<HTML>' in html_content.upper() or 'boarddocs/press/' in html_content
        
        if is_historical:
            return self.extract_historical_statement_text(soup)
        else:
            return self.extract_modern_statement_text(soup)
    
    def extract_historical_statement_text(self, soup):
        """
        Extract text from historical FOMC statements (2000-2004 era)
        """
        # For historical pages, extract directly from body
        body = soup.find('body')
        if not body:
            body = soup
        
        # Get all text and clean it up
        full_text = body.get_text()
        
        # Split into lines and filter
        lines = [line.strip() for line in full_text.split('\n') if line.strip()]
        
        # Filter out header/footer elements
        filtered_lines = []
        content_started = False
        
        for line in lines:
            # Skip until we find the actual statement
            if not content_started:
                if ('federal open market committee' in line.lower() or 
                    'committee' in line.lower() and 'voted' in line.lower()):
                    content_started = True
                    filtered_lines.append(line)
                continue
            
            # Skip common boilerplate
            skip_phrases = [
                'release date:', 'for immediate release', 'last update:', 
                'home', 'accessibility', 'board of governors', 'washington',
                'privacy program', 'foia', 'contact us'
            ]
            
            if not any(phrase in line.lower() for phrase in skip_phrases):
                filtered_lines.append(line)
        
        # Join and clean
        full_text = ' '.join(filtered_lines)
        full_text = re.sub(r'\s+', ' ', full_text)  # Multiple spaces to single
        
        return full_text.strip()
    
    def extract_modern_statement_text(self, soup):
        """
        Extract text from modern FOMC statements (2005+)
        """
        # Try to find main content area
        content_selectors = [
            'div#content',
            'div.col-xs-12', 
            'main',
            'article',
            'div[class*="content"]',
            'div[id*="content"]'
        ]
        
        main_content = None
        for selector in content_selectors:
            main_content = soup.select_one(selector)
            if main_content:
                break
        
        if not main_content:
            main_content = soup
        
        # Extract paragraphs
        paragraphs = []
        for p in main_content.find_all(['p', 'div']):
            text = p.get_text().strip()
            if len(text) > 20:  # Skip very short text
                # Skip common navigation/header text and boilerplate
                skip_phrases = [
                    'for immediate release', 'board of governors', 'federal reserve system',
                    'last update', 'share', 'print', 'email', 'accessibility', 'contact',
                    'subscribe', 'press release', 'back to top', 'main navigation',
                    'search', 'home', 'about the fed', 'please enable javascript',
                    'if it is disabled in your browser', 'access the information through the links',
                    'skip to main content', 'you are here:', 'breadcrumb', 'main menu',
                    'federal reserve bank', 'federal reserve board', 'washington, d.c.',
                    'media inquiries', 'other inquiries'
                ]
                
                if not any(phrase in text.lower() for phrase in skip_phrases):
                    paragraphs.append(text)
        
        # Join paragraphs and clean up
        full_text = '\n\n'.join(paragraphs)
        
        # Remove specific unwanted sentences/phrases
        unwanted_patterns = [
            r'Please enable JavaScript if it is disabled in your browser or access the information through the links provided below\.',
            r'Skip to main content',
            r'You are here:.*',
            r'Last Update:.*',
            r'For media inquiries.*',
            r'Other inquiries.*',
            r'Board of Governors of the Federal Reserve System.*',
            r'Washington, D\.C\. \d+.*',
            r'Accessibility.*Contact.*',
            r'Subscribe.*'
        ]
        
        for pattern in unwanted_patterns:
            full_text = re.sub(pattern, '', full_text, flags=re.IGNORECASE | re.DOTALL)
        
        # Clean up whitespace
        full_text = re.sub(r'\s+', ' ', full_text)  # Multiple spaces to single
        full_text = re.sub(r'\n\s*\n\s*\n+', '\n\n', full_text)  # Multiple newlines to double
        
        # Remove any remaining empty lines at start/end
        full_text = full_text.strip()
        
        # Remove the JavaScript message if it still appears at the beginning
        if full_text.lower().startswith('please enable javascript'):
            # Find the end of this sentence and remove it
            end_idx = full_text.find('.', 0)
            if end_idx != -1:
                full_text = full_text[end_idx+1:].strip()
        
        return full_text
    
    def format_date(self, date_str):
        """
        Convert YYYYMMDD to DD-MM-YYYY format
        """
        year = date_str[:4]
        month = date_str[4:6]
        day = date_str[6:8]
        return f"{day}-{month}-{year}"
    
    def save_clean_json(self, date_str, text_content):
        """
        Save clean JSON file with required format
        """
        data = {
            "date": self.format_date(date_str),
            "type": "statement", 
            "text": text_content
        }
        
        filename = f"data/fed-comms/statements/clean/statement{date_str}.json"
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        return filename
    
    def scrape_statement(self, date_str):
        """
        Scrape a single FOMC statement
        """
        urls = self.construct_statement_urls(date_str)
        
        for url in urls:
            try:
                print(f"  Trying: {url}")
                response = self.session.get(url, timeout=15)
                
                if response.status_code == 200:
                    html_content = response.text
                    
                    # Validate this is likely a FOMC statement
                    content_lower = html_content.lower()
                    fomc_indicators = [
                        'federal open market committee',
                        'fomc',
                        'monetary policy',
                        'interest rate',
                        'fed funds rate'
                    ]
                    
                    if any(indicator in content_lower for indicator in fomc_indicators):
                        # Extract text content
                        text_content = self.extract_statement_text(html_content)
                        
                        if len(text_content) > 200:  # Must have substantial content
                            # Save raw HTML
                            raw_file = self.save_raw_html(date_str, html_content, url)
                            
                            # Save clean JSON
                            json_file = self.save_clean_json(date_str, text_content)
                            
                            print(f"  SUCCESS! Saved to {raw_file} and {json_file}")
                            return True
                        else:
                            print(f"  Content too short ({len(text_content)} chars)")
                    else:
                        print(f"  No FOMC indicators found")
                else:
                    print(f"  HTTP {response.status_code}")
                    
            except Exception as e:
                print(f"  Error: {str(e)}")
            
            # Small delay between URL attempts
            time.sleep(0.5)
        
        return False
    
    def scrape_all_statements(self):
        """
        Scrape all FOMC statements from 2000 to 2025
        """
        meeting_dates = self.get_known_fomc_dates()
        successful = 0
        failed = 0
        skipped = 0
        
        print(f"Starting FOMC statement scraper for {len(meeting_dates)} dates...")
        print("=" * 60)
        
        for i, date_str in enumerate(meeting_dates, 1):
            # Check if already exists
            raw_exists = os.path.exists(f"data/fed-comms/statements/raw/statement{date_str}.html")
            json_exists = os.path.exists(f"data/fed-comms/statements/clean/statement{date_str}.json")
            
            if raw_exists and json_exists:
                print(f"[{i}/{len(meeting_dates)}] {date_str}: Already exists - skipping")
                skipped += 1
                continue
            
            print(f"[{i}/{len(meeting_dates)}] {date_str}: Scraping...")
            
            if self.scrape_statement(date_str):
                successful += 1
            else:
                failed += 1
                print(f"  Failed to find statement for {date_str}")
            
            # Respectful delay between meetings
            time.sleep(2)
        
        print("=" * 60)
        print(f"Scraping complete!")
        print(f"Successful: {successful}")
        print(f"Failed: {failed}")
        print(f"Skipped: {skipped}")
        print(f"Total processed: {successful + failed + skipped}")

def main():
    scraper = FOMCStatementScraper()
    scraper.scrape_all_statements()

if __name__ == "__main__":
    main()