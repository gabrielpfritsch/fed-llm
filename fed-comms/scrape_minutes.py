import requests
import json
import os
import re
from datetime import datetime
from bs4 import BeautifulSoup
import time
from urllib.parse import urljoin

class FOMCMinutesScraper:
    def __init__(self):
        self.base_url = "https://www.federalreserve.gov"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        
        # Create directories
        os.makedirs('minutes/raw', exist_ok=True)
        os.makedirs('minutes/clean', exist_ok=True)
    
    def get_known_fomc_dates(self):
        """
        Get comprehensive list of known FOMC meeting dates from 2000-2025
        Using same dates as statements since minutes are released for the same meetings
        """
        known_dates = [
            # 2000
            "20000202", "20000321", "20000516", "20000628", "20000822", "20001003", "20001115", "20001219",
            # 2001  
            "20010103", "20010131", "20010320", "20010515", "20010627", "20010821", "20011002", "20011106", "20011211",
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
            # 2011
            "20110126", "20110315", "20110427", "20110622", "20110809", "20110921", "20111102", "20111213",
            # 2012
            "20120125", "20120313", "20120425", "20120620", "20120801", "20120913", "20121024", "20121212",
            # 2013
            "20130130", "20130320", "20130501", "20130619", "20130731", "20130918", "20131030", "20131218",
            # 2014
            "20140129", "20140319", "20140430", "20140618", "20140730", "20140917", "20141029", "20141217",
            # 2015
            "20150128", "20150318", "20150429", "20150617", "20150729", "20150917", "20151028", "20151216",
            # 2016
            "20160127", "20160316", "20160427", "20160615", "20160727", "20160921", "20161102", "20161214",
            # 2017
            "20170201", "20170315", "20170503", "20170614", "20170726", "20170920", "20171101", "20171213",
            # 2018
            "20180131", "20180321", "20180502", "20180613", "20180801", "20180926", "20181108", "20181219",
            # 2019
            "20190130", "20190320", "20190501", "20190619", "20190731", "20190918", "20191030", "20191211",
            # 2020
            "20200129", "20200315", "20200429", "20200610", "20200729", "20200916", "20201105", "20201216",
            # 2021
            "20210127", "20210317", "20210428", "20210616", "20210728", "20210922", "20211103", "20211215",
            # 2022
            "20220126", "20220316", "20220504", "20220615", "20220727", "20220921", "20221102", "20221214",
            # 2023
            "20230201", "20230322", "20230503", "20230614", "20230726", "20230920", "20231101", "20231213",
            # 2024
            "20240131", "20240320", "20240501", "20240612", "20240731", "20240918", "20241107", "20241218",
            # 2025 (actual dates through July 23, 2025)
            "20250129", "20250319", "20250507", "20250618", "20250730"
        ]
        
        return sorted(known_dates)
    
    def construct_minutes_urls(self, date_str):
        """
        Construct possible URLs for FOMC minutes based on historical patterns
        """
        year = date_str[:4]
        year_int = int(year)
        
        urls = []
        
        if year_int >= 2008:
            # Modern format (2008-present)
            urls.append(f"{self.base_url}/monetarypolicy/fomcminutes{date_str}.htm")
            # Some may also be available as PDFs
            urls.append(f"{self.base_url}/monetarypolicy/fomcminutes{date_str}.pdf")
        else:
            # Historical format (2000-2007)
            urls.append(f"{self.base_url}/fomc/minutes/{date_str}.htm")
        
        return urls
    
    def save_raw_html(self, date_str, html_content, url):
        """
        Save raw HTML content to file
        """
        filename = f"minutes/raw/minutes{date_str}.html"
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(f"<!-- Source URL: {url} -->\n")
            f.write(f"<!-- Scraped: {datetime.now().isoformat()} -->\n")
            f.write(html_content)
        return filename
    
    def extract_release_date(self, html_content):
        """
        Extract the release date from the minutes HTML
        """
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Look for common patterns for release date
        release_patterns = [
            r'Last Update:\s*([A-Za-z]+ \d{1,2}, \d{4})',
            r'Released:\s*([A-Za-z]+ \d{1,2}, \d{4})',
            r'Release Date:\s*([A-Za-z]+ \d{1,2}, \d{4})',
            r'(?:Released|Last Update):\s*([A-Za-z]+ \d{1,2}, \d{4})'
        ]
        
        # Search in the full text
        full_text = soup.get_text()
        for pattern in release_patterns:
            match = re.search(pattern, full_text, re.IGNORECASE)
            if match:
                return match.group(1)
        
        # Look for specific HTML elements that might contain the date
        date_selectors = [
            '.lastUpdate',
            '#lastUpdate', 
            '.releaseDate',
            '[class*="date"]',
            '[id*="date"]'
        ]
        
        for selector in date_selectors:
            element = soup.select_one(selector)
            if element:
                text = element.get_text().strip()
                for pattern in release_patterns:
                    match = re.search(pattern, text, re.IGNORECASE)
                    if match:
                        return match.group(1)
        
        return None
    
    def extract_minutes_text(self, html_content):
        """
        Extract clean text from FOMC minutes HTML
        """
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Remove scripts, styles, and navigation elements
        for element in soup(["script", "style", "nav", "header", "footer"]):
            element.decompose()
        
        # Check if this is a historical page (simpler HTML structure)
        is_historical = '<HTML>' in html_content.upper() or '/fomc/minutes/' in html_content
        
        if is_historical:
            return self.extract_historical_minutes_text(soup)
        else:
            return self.extract_modern_minutes_text(soup)
    
    def extract_historical_minutes_text(self, soup):
        """
        Extract text from historical FOMC minutes (2000-2007 era)
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
            # Skip until we find the actual minutes content
            if not content_started:
                if ('minutes of the federal open market committee' in line.lower() or 
                    'meeting held on' in line.lower() or
                    'a meeting of the federal open market committee' in line.lower()):
                    content_started = True
                    filtered_lines.append(line)
                continue
            
            # Skip common boilerplate
            skip_phrases = [
                'release date:', 'last update:', 'home', 'accessibility', 
                'board of governors', 'washington', 'privacy program', 'foia', 'contact us'
            ]
            
            if not any(phrase in line.lower() for phrase in skip_phrases):
                filtered_lines.append(line)
        
        # Join and clean
        full_text = ' '.join(filtered_lines)
        full_text = re.sub(r'\s+', ' ', full_text)  # Multiple spaces to single
        
        return full_text.strip()
    
    def extract_modern_minutes_text(self, soup):
        """
        Extract text from modern FOMC minutes (2008+)
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
        
        # Extract paragraphs and other text elements
        text_elements = []
        for element in main_content.find_all(['p', 'div', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6']):
            text = element.get_text().strip()
            if len(text) > 10:  # Skip very short text
                # Skip common navigation/header text and boilerplate
                skip_phrases = [
                    'last update', 'share', 'print', 'email', 'accessibility', 'contact',
                    'subscribe', 'press release', 'back to top', 'main navigation',
                    'search', 'home', 'about the fed', 'please enable javascript',
                    'skip to main content', 'you are here:', 'breadcrumb', 'main menu',
                    'board of governors of the federal reserve system', 'washington, d.c.',
                    'media inquiries', 'other inquiries'
                ]
                
                if not any(phrase in text.lower() for phrase in skip_phrases):
                    text_elements.append(text)
        
        # Join with paragraph breaks
        full_text = '\n\n'.join(text_elements)
        
        # Remove specific unwanted patterns
        unwanted_patterns = [
            r'Please enable JavaScript if it is disabled in your browser.*?below\.',
            r'Skip to main content',
            r'You are here:.*',
            r'Last Update:.*',
            r'For media inquiries.*',
            r'Subscribe.*'
        ]
        
        for pattern in unwanted_patterns:
            full_text = re.sub(pattern, '', full_text, flags=re.IGNORECASE | re.DOTALL)
        
        # Clean up whitespace
        full_text = re.sub(r'\s+', ' ', full_text)  # Multiple spaces to single
        full_text = re.sub(r'\n\s*\n\s*\n+', '\n\n', full_text)  # Multiple newlines to double
        
        return full_text.strip()
    
    def format_date(self, date_str):
        """
        Convert YYYYMMDD to DD-MM-YYYY format
        """
        year = date_str[:4]
        month = date_str[4:6]
        day = date_str[6:8]
        return f"{day}-{month}-{year}"
    
    def save_clean_json(self, date_str, text_content, release_date=None):
        """
        Save clean JSON file with required format for minutes
        """
        data = {
            "meeting_date": self.format_date(date_str),
            "release_date": release_date,
            "type": "minutes", 
            "text": text_content
        }
        
        filename = f"minutes/clean/minutes{date_str}.json"
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        return filename
    
    def scrape_minutes(self, date_str):
        """
        Scrape FOMC minutes for a single meeting date
        """
        urls = self.construct_minutes_urls(date_str)
        
        for url in urls:
            try:
                print(f"  Trying: {url}")
                response = self.session.get(url, timeout=15)
                
                if response.status_code == 200:
                    html_content = response.text
                    
                    # Validate this looks like FOMC minutes
                    content_lower = html_content.lower()
                    minutes_indicators = [
                        'minutes of the federal open market committee',
                        'fomc minutes',
                        'meeting held on',
                        'federal open market committee meeting'
                    ]
                    
                    if any(indicator in content_lower for indicator in minutes_indicators):
                        # Extract text content
                        text_content = self.extract_minutes_text(html_content)
                        
                        if len(text_content) > 500:  # Minutes should be substantial
                            # Extract release date
                            release_date = self.extract_release_date(html_content)
                            
                            # Save raw HTML
                            raw_file = self.save_raw_html(date_str, html_content, url)
                            
                            # Save clean JSON
                            json_file = self.save_clean_json(date_str, text_content, release_date)
                            
                            print(f"  SUCCESS! Saved to {raw_file} and {json_file}")
                            if release_date:
                                print(f"  Release date: {release_date}")
                            return True
                        else:
                            print(f"  Content too short ({len(text_content)} chars)")
                    else:
                        print(f"  No FOMC minutes indicators found")
                else:
                    print(f"  HTTP {response.status_code}")
                    
            except Exception as e:
                print(f"  Error: {str(e)}")
            
            # Small delay between URL attempts
            time.sleep(0.5)
        
        return False
    
    def scrape_all_minutes(self):
        """
        Scrape all FOMC minutes from 2000 to 2025
        """
        meeting_dates = self.get_known_fomc_dates()
        successful = 0
        failed = 0
        skipped = 0
        
        print(f"Starting FOMC minutes scraper for {len(meeting_dates)} dates...")
        print("=" * 60)
        
        for i, date_str in enumerate(meeting_dates, 1):
            # Check if already exists
            raw_exists = os.path.exists(f"minutes/raw/minutes{date_str}.html")
            json_exists = os.path.exists(f"minutes/clean/minutes{date_str}.json")
            
            if raw_exists and json_exists:
                print(f"[{i}/{len(meeting_dates)}] {date_str}: Already exists - skipping")
                skipped += 1
                continue
            
            print(f"[{i}/{len(meeting_dates)}] {date_str}: Scraping...")
            
            if self.scrape_minutes(date_str):
                successful += 1
            else:
                failed += 1
                print(f"  Failed to find minutes for {date_str}")
            
            # Respectful delay between meetings
            time.sleep(2)
        
        print("=" * 60)
        print(f"Scraping complete!")
        print(f"Successful: {successful}")
        print(f"Failed: {failed}")
        print(f"Skipped: {skipped}")
        print(f"Total processed: {successful + failed + skipped}")

def main():
    scraper = FOMCMinutesScraper()
    scraper.scrape_all_minutes()

if __name__ == "__main__":
    main()