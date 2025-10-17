import requests
import json
import re
from datetime import datetime
from pathlib import Path
from bs4 import BeautifulSoup
import time
from typing import Optional, List

class FOMCMinutesScraper:
    """Scraper for FOMC meeting minutes from the Federal Reserve website."""
    
    # Constants
    BASE_URL = "https://www.federalreserve.gov"
    MIN_MINUTES_LENGTH = 200
    REQUEST_TIMEOUT = 15
    DELAY_BETWEEN_URLS = 0.5
    DELAY_BETWEEN_MEETINGS = 2.0
    
    # Parent page URLs for extracting release dates
    HISTORICAL_YEARS = range(1993, 2020)  # 1993-2019
    CALENDAR_URL = f"{BASE_URL}/monetarypolicy/fomccalendars.htm"  # 2020-2025
    
    # Common boilerplate phrases to skip
    # NOTE: These should be SPECIFIC to avoid filtering legitimate content
    # Avoid broad phrases that might appear in actual minutes text
    SKIP_PHRASES = [
        'last update:', 'share this page', 'print page', 'email this page',
        'accessibility contact', 'subscribe to', 'back to top',
        'main navigation', 'please enable javascript', 'skip to main content',
        'you are here:', 'breadcrumb', 'main menu', 'privacy program', 'foia',
        'contact us', 'media inquiries', 'other inquiries',
        'board of governors of the federal reserve system, washington, d.c.',
        'return to top', 'release date:',
        # More specific navigation phrases (with context to avoid false positives)
        'about the fed |', 'about the fed:', 'view press release', 
        'latest press releases', 'subscribe to rss'
    ]
    
    def __init__(self):
        self.session = requests.Session()
        
        # Create directories using pathlib
        self.raw_dir = Path('data/fed-comms/minutes/raw')
        self.clean_dir = Path('data/fed-comms/minutes/clean')
        self.raw_dir.mkdir(parents=True, exist_ok=True)
        self.clean_dir.mkdir(parents=True, exist_ok=True)
        
        # Build release date mapping from parent pages
        self.release_date_mapping = {}
        print("Building release date mapping from parent pages...")
        self._build_release_date_mapping()
        print(f"Mapped {len(self.release_date_mapping)} meeting release dates")
    
    def get_known_fomc_dates(self):
        """
        Get comprehensive list of known FOMC meeting dates from 1993-2025
        Using same dates as statements since minutes are released for the same meetings
        """
        known_dates = [
            # 1993
            "19930203", "19930323", "19930518", "19930707", "19930817", "19930921", "19931116", "19931221",
            # 1994
            "19940204", "19940322", "19940517", "19940706", "19940816", "19940927", "19941115", "19941220",
            # 1995
            "19950201", "19950328", "19950523", "19950706", "19950822", "19950926", "19951115", "19951219",
            # 1996
            "19960130", "19960326", "19960521", "19960702", "19960820", "19960924", "19961113", "19961217",
            # 1997
            "19970204", "19970325", "19970520", "19970701", "19970819", "19970930", "19971112", "19971216",
            # 1998
            "19980203", "19980331", "19980519", "19980630", "19980818", "19980929", "19981117", "19981222",
            # 1999
            "19990202", "19990330", "19990518", "19990629", "19990824", "19991005", "19991116", "19991221",
            # 2000
            "20000202", "20000321", "20000516", "20000628", "20000822", "20001003", "20001115", "20001219",
            # 2001  
            "20010131", "20010320", "20010515", "20010627", "20010821", "20011002", "20011106", "20011211",
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
            # 2025
            "20250129", "20250319", "20250507", "20250618", "20250730"
        ]
        
        return sorted(known_dates)
    
    def _build_release_date_mapping(self) -> None:
        """
        Build a mapping of meeting dates (YYYYMMDD) to release dates by scraping parent pages.
        Extracts release dates from:
        - Historical pages: /monetarypolicy/fomchistorical{year}.htm (1993-2019)
        - Calendar page: /monetarypolicy/fomccalendars.htm (2020-2025)
        """
        # Process historical year pages (1993-2019)
        for year in self.HISTORICAL_YEARS:
            url = f"{self.BASE_URL}/monetarypolicy/fomchistorical{year}.htm"
            try:
                print(f"  Fetching {year} historical page...")
                response = self.session.get(url, timeout=self.REQUEST_TIMEOUT)
                if response.status_code == 200:
                    mapping = self._extract_release_dates_from_historical_page(response.text, year)
                    self.release_date_mapping.update(mapping)
                    print(f"    Found {len(mapping)} meetings for {year}")
                else:
                    print(f"    Failed to fetch {year} page: HTTP {response.status_code}")
            except Exception as e:
                print(f"    Error fetching {year} page: {str(e)}")
            time.sleep(self.DELAY_BETWEEN_URLS)
        
        # Process calendar page (2020-2025)
        try:
            print(f"  Fetching calendar page for 2020-2025...")
            response = self.session.get(self.CALENDAR_URL, timeout=self.REQUEST_TIMEOUT)
            if response.status_code == 200:
                mapping = self._extract_release_dates_from_calendar_page(response.text)
                self.release_date_mapping.update(mapping)
                print(f"    Found {len(mapping)} meetings from calendar page")
            else:
                print(f"    Failed to fetch calendar page: HTTP {response.status_code}")
        except Exception as e:
            print(f"    Error fetching calendar page: {str(e)}")
    
    def _extract_release_dates_from_historical_page(self, html_content: str, year: int) -> dict:
        """
        Extract meeting dates and release dates from a historical year page.
        
        Args:
            html_content: Raw HTML content of the historical page
            year: Year of the page
            
        Returns:
            Dictionary mapping meeting date (YYYYMMDD) to release date string
        """
        soup = BeautifulSoup(html_content, 'html.parser')
        mapping = {}
        
        # Look for Minutes links and their associated release dates
        # Pattern: <a href="/fomc/MINUTES/YYYY/YYYYMMDDmin.htm">Minutes</a> (Released Month Day, Year)
        for link in soup.find_all('a', href=True):
            href = link['href']
            
            # Check if this is a minutes link
            # Could be in format: /fomc/MINUTES/1993/19930203min.htm or /fomc/minutes/20030318.htm
            if 'minutes' in href.lower() or 'MINUTES' in href or '/fomc2008' in href:
                # Extract date from URL
                # Try different patterns
                date_match = None
                
                # Pattern 1: /fomc/MINUTES/1993/19930203min.htm
                match = re.search(r'/fomc/MINUTES/\d{4}/(\d{8})min\.htm', href)
                if match:
                    date_match = match.group(1)
                
                # Pattern 2: /fomc/minutes/20030318.htm
                if not date_match:
                    match = re.search(r'/fomc/minutes/(\d{8})\.htm', href)
                    if match:
                        date_match = match.group(1)
                
                # Pattern 3: /monetarypolicy/fomcminutes20080625.htm
                if not date_match:
                    match = re.search(r'/monetarypolicy/fomcminutes(\d{8})\.htm', href)
                    if match:
                        date_match = match.group(1)
                
                # Pattern 4: /monetarypolicy/fomc20080625.htm (special case for 20080625)
                if not date_match:
                    match = re.search(r'/monetarypolicy/fomc(\d{8})\.htm', href)
                    if match:
                        date_match = match.group(1)
                
                if date_match:
                    # Look for release date in the text following the link
                    # The pattern is typically: Minutes</a> (Released Month Day, Year)
                    # Or for 2008+: Minutes (Released Month Day, Year): HTML | PDF
                    release_date = None
                    
                    # Try parent element first
                    parent = link.parent
                    if parent:
                        text = parent.get_text()
                        # Extract "Released Month Day, Year" or "Release Month Day, Year"
                        release_match = re.search(r'Released?\s+([A-Za-z]+\s+\d{1,2},\s+\d{4})', text)
                        if release_match:
                            release_date = release_match.group(1)
                    
                    # If not found, try grandparent element (for 2008+ format)
                    if not release_date and parent and parent.parent:
                        text = parent.parent.get_text()
                        release_match = re.search(r'Released?\s+([A-Za-z]+\s+\d{1,2},\s+\d{4})', text)
                        if release_match:
                            release_date = release_match.group(1)
                    
                    if release_date:
                        mapping[date_match] = release_date
        
        return mapping
    
    def _extract_release_dates_from_calendar_page(self, html_content: str) -> dict:
        """
        Extract meeting dates and release dates from the calendar page (2020-2025).
        
        Args:
            html_content: Raw HTML content of the calendar page
            
        Returns:
            Dictionary mapping meeting date (YYYYMMDD) to release date string
        """
        soup = BeautifulSoup(html_content, 'html.parser')
        mapping = {}
        
        # The calendar page has sections for each year with meeting information
        # Look for Minutes links and their associated release dates
        for link in soup.find_all('a', href=True):
            href = link['href']
            
            # Check if this is a minutes link for 2020+
            if 'fomcminutes' in href.lower():
                # Extract date from URL: /monetarypolicy/fomcminutes20200129.htm
                match = re.search(r'/monetarypolicy/fomcminutes(\d{8})\.htm', href)
                if match:
                    date_match = match.group(1)
                    
                    # Look for release date in parent or grandparent elements
                    release_date = None
                    
                    # Try parent element first
                    parent = link.parent
                    if parent:
                        text = parent.get_text()
                        release_match = re.search(r'Released?\s+([A-Za-z]+\s+\d{1,2},\s+\d{4})', text)
                        if release_match:
                            release_date = release_match.group(1)
                    
                    # If not found, try grandparent element
                    if not release_date and parent and parent.parent:
                        text = parent.parent.get_text()
                        release_match = re.search(r'Released?\s+([A-Za-z]+\s+\d{1,2},\s+\d{4})', text)
                        if release_match:
                            release_date = release_match.group(1)
                    
                    if release_date:
                        mapping[date_match] = release_date
        
        return mapping
    
    def construct_minutes_urls(self, date_str: str) -> List[str]:
        """
        Construct possible URLs for FOMC minutes based on historical patterns.
        
        Args:
            date_str: Date in YYYYMMDD format
            
        Returns:
            List of possible URLs to try
        """
        year = date_str[:4]
        year_int = int(year)
        month = int(date_str[4:6])
        
        urls = []
        
        # Edge case: 20080625 uses /fomc20080625.htm instead of /fomcminutes20080625.htm
        if date_str == "20080625":
            urls.append(f"{self.BASE_URL}/monetarypolicy/fomc{date_str}.htm")
        # Modern format (October 2007-present) - URL pattern changed in October 2007
        elif year_int > 2007 or (year_int == 2007 and month >= 10):
            urls.append(f"{self.BASE_URL}/monetarypolicy/fomcminutes{date_str}.htm")
            # Some may also be available as PDFs
            urls.append(f"{self.BASE_URL}/monetarypolicy/fomcminutes{date_str}.pdf")
        # 1993-1995 format: /fomc/MINUTES/YYYY/YYYYMMDDmin.htm
        elif year_int >= 1993 and year_int <= 1995:
            urls.append(f"{self.BASE_URL}/fomc/MINUTES/{year}/{date_str}min.htm")
        else:
            # Historical format (1996-Oct 2007)
            urls.append(f"{self.BASE_URL}/fomc/minutes/{date_str}.htm")
        
        return urls
    
    def save_raw_html(self, date_str: str, html_content: str, url: str) -> Path:
        """
        Save raw HTML content to file.
        
        Args:
            date_str: Date in YYYYMMDD format
            html_content: Raw HTML content
            url: Source URL
            
        Returns:
            Path to saved file
        """
        filename = self.raw_dir / f"minutes{date_str}.html"
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(f"<!-- Source URL: {url} -->\n")
            f.write(f"<!-- Scraped: {datetime.now().isoformat()} -->\n")
            f.write(html_content)
        return filename
    
    def _clean_whitespace(self, text: str) -> str:
        """
        Clean up whitespace in text while preserving paragraph breaks.
        
        Args:
            text: Text to clean
            
        Returns:
            Cleaned text
        """
        # Split into lines and clean each line
        lines = text.split('\n')
        cleaned_lines = []
        
        for line in lines:
            # Clean multiple spaces within each line
            cleaned_line = re.sub(r'[ \t]+', ' ', line).strip()
            if cleaned_line:  # Only keep non-empty lines
                cleaned_lines.append(cleaned_line)
            elif cleaned_lines and cleaned_lines[-1]:  # Preserve paragraph breaks
                cleaned_lines.append('')
        
        # Join lines back and normalize paragraph breaks
        text = '\n'.join(cleaned_lines)
        # Reduce multiple blank lines to single blank line
        text = re.sub(r'\n\n\n+', '\n\n', text)
        return text.strip()
    
    def extract_minutes_text(self, html_content: str) -> str:
        """
        Extract clean text from FOMC minutes HTML.
        
        Args:
            html_content: Raw HTML content
            
        Returns:
            Cleaned text content
        """
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Remove scripts, styles, and navigation elements
        for element in soup(["script", "style", "nav", "header", "footer"]):
            element.decompose()
        
        # Check if this is a historical page (simpler HTML structure)
        # Includes 1993-1995 format (/fomc/MINUTES/) and 1996-Oct 2007 format (/fomc/minutes/)
        is_historical = ('<HTML>' in html_content.upper() or 
                        '/fomc/minutes/' in html_content or 
                        '/fomc/MINUTES/' in html_content)
        
        if is_historical:
            return self.extract_historical_minutes_text(soup)
        else:
            return self.extract_modern_minutes_text(soup)
    
    def extract_historical_minutes_text(self, soup: BeautifulSoup) -> str:
        """
        Extract text from historical FOMC minutes (1993-Oct 2007).
        
        Args:
            soup: BeautifulSoup parsed HTML
            
        Returns:
            Cleaned text content
        """
        # For historical pages, extract from paragraphs and text blocks
        body = soup.find('body')
        if not body:
            body = soup
        
        # Extract text from paragraphs and table cells, preserving document order
        paragraphs = []
        content_started = False
        seen_texts = set()  # Track text to avoid duplicates
        
        # Process all elements in document order (p, td, th, and li for table headers and lists)
        for element in body.find_all(['p', 'td', 'th', 'li']):
            # Skip td elements that contain p tags (to avoid duplicates)
            if element.name == 'td' and element.find('p'):
                continue
            
            # For p elements that contain other p tags (malformed nested HTML),
            # extract only direct text content (not from nested children)
            if element.name == 'p' and element.find('p'):
                # Get only direct text nodes, not from descendants
                direct_text = ''.join([str(s) for s in element.strings if s.parent == element]).strip()
                if direct_text:
                    # Check for strong tags that are direct children
                    direct_strong = [s for s in element.find_all('strong', recursive=False)]
                    if direct_strong:
                        # Handle as header
                        strong_text = direct_strong[0].get_text(strip=True)
                        if not content_started:
                            # Normalize whitespace for trigger phrase matching
                            strong_normalized = ' '.join(strong_text.lower().split())
                            if ('minutes of the federal open market committee' in strong_normalized or 
                                'meeting held on' in strong_normalized or
                                'a meeting of the federal open market committee' in strong_normalized):
                                content_started = True
                            else:
                                continue
                        if strong_text not in seen_texts:
                            seen_texts.add(strong_text)
                            paragraphs.append(strong_text)
                        # Add remaining direct text if any
                        remaining = direct_text.replace(strong_text, '', 1).strip()
                        if remaining and remaining not in seen_texts:
                            seen_texts.add(remaining)
                            paragraphs.append(remaining)
                    else:
                        # Regular direct text
                        if not content_started:
                            if ('minutes of the federal open market committee' in direct_text.lower() or 
                                'meeting held on' in direct_text.lower() or
                                'a meeting of the federal open market committee' in direct_text.lower()):
                                content_started = True
                            else:
                                continue
                        
                        # Apply skip phrases check
                        text_lower = direct_text.lower()
                        if len(direct_text) < 500:
                            if any(phrase in text_lower for phrase in self.SKIP_PHRASES):
                                continue
                        else:
                            text_edges = text_lower[:200] + text_lower[-200:]
                            if any(phrase in text_edges for phrase in self.SKIP_PHRASES):
                                continue
                        
                        if direct_text not in seen_texts:
                            # Remove "Return to text" from footnotes
                            direct_text = re.sub(r'\s*Return to text\s*$', '', direct_text, flags=re.IGNORECASE)
                            seen_texts.add(direct_text)
                            paragraphs.append(direct_text)
                continue  # Skip the normal processing below
            
            # Handle bullet points
            if element.name == 'li':
                text = element.get_text(separator=' ', strip=True)
                if text and content_started:
                    paragraphs.append(f"- {text}")
                continue
            
            # Check for strong tags in paragraphs (section headers)
            strong_tags = element.find_all('strong')
            if strong_tags and element.name == 'p':
                first_strong = strong_tags[0]
                strong_text = first_strong.get_text(strip=True)
                remaining_text = element.get_text(separator=' ', strip=True)
                
                # If strong tag is followed by <br/> or is the whole paragraph, treat as header
                if first_strong.find_next_sibling('br') or remaining_text == strong_text:
                    # Skip until we find actual minutes content
                    if not content_started:
                        # Normalize whitespace for trigger phrase matching
                        strong_normalized = ' '.join(strong_text.lower().split())
                        if ('minutes of the federal open market committee' in strong_normalized or 
                            'meeting held on' in strong_normalized or
                            'a meeting of the federal open market committee' in strong_normalized):
                            content_started = True
                        else:
                            continue
                    
                    # Add strong text as separate paragraph
                    if strong_text not in seen_texts:
                        seen_texts.add(strong_text)
                        paragraphs.append(strong_text)
                    
                    # Add remaining text if any
                    rest = remaining_text.replace(strong_text, '', 1).strip()
                    if rest and rest not in seen_texts:
                        seen_texts.add(rest)
                        paragraphs.append(rest)
                    continue
            
            # Regular text extraction
            text = element.get_text(separator=' ', strip=True)
            if not text:
                continue
            
            # Skip until we find the actual minutes content
            if not content_started:
                # Normalize whitespace for trigger phrase matching
                text_normalized = ' '.join(text.lower().split())
                if ('minutes of the federal open market committee' in text_normalized or 
                    'meeting held on' in text_normalized or
                    'a meeting of the federal open market committee' in text_normalized):
                    content_started = True
                else:
                    continue
            
            # Skip common boilerplate using class constant
            if any(phrase in text.lower() for phrase in self.SKIP_PHRASES):
                continue
            
            # Skip duplicates
            if text in seen_texts:
                continue
            
            # Remove "Return to text" from footnotes
            text = re.sub(r'\s*Return to text\s*$', '', text, flags=re.IGNORECASE)
            
            seen_texts.add(text)
            paragraphs.append(text)
        
        # Join with double newlines to preserve paragraph structure
        full_text = '\n\n'.join(paragraphs)
        return self._clean_whitespace(full_text)
    
    def extract_modern_minutes_text(self, soup: BeautifulSoup) -> str:
        """
        Extract text from modern FOMC minutes (2008+).
        
        Args:
            soup: BeautifulSoup parsed HTML
            
        Returns:
            Cleaned text content
        """
        # Find the article content area specifically (more targeted than before)
        main_content = soup.select_one('div#article')
        
        if not main_content:
            # Fallback to other selectors
            content_selectors = [
                'div#leftText',  # 2008-2011 format
                'div#content',
                'div.col-xs-12', 
                'main',
                'article',
                'div[class*="content"]'
            ]
            
            for selector in content_selectors:
                main_content = soup.select_one(selector)
                if main_content:
                    break
        
        if not main_content:
            main_content = soup
        
        # Track if we've started seeing actual content (not navigation)
        content_started = False
        seen_texts = set()
        paragraphs = []
        
        # Check if we have an h1 title (2008-2011 format) to know we can start from beginning
        # H1 is often outside main_content (sibling container), so check in full soup
        h1_title = soup.find('h1')
        if h1_title and 'minutes of the federal open market committee' in h1_title.get_text().lower():
            content_started = True
        
        # Process elements in document order (including tables via td/th)
        for element in main_content.find_all(['h1', 'h3', 'p', 'blockquote', 'li', 'td', 'th']):
            # Check if this is the start of actual content (h3 for newer format, h1 for 2008-2011)
            if not content_started and element.name in ['h1', 'h3']:
                heading_text = element.get_text(strip=True)
                if 'minutes of the federal open market committee' in heading_text.lower():
                    content_started = True
                    paragraphs.append(heading_text)
                    continue
            
            # Skip until content starts
            if not content_started:
                continue
            
            # Skip h1 elements after we've started (already processed)
            if element.name == 'h1':
                continue
            
            # Handle different element types
            if element.name == 'li':
                # Bullet point - add with bullet marker
                text = element.get_text(separator=' ', strip=True)
                if text:
                    paragraphs.append(f"- {text}")
            elif element.name in ['td', 'th']:
                # Table cell - skip if it contains p tags (to avoid duplicates)
                if element.find('p'):
                    continue
                
                text = element.get_text(separator=' ', strip=True)
                if text and text not in seen_texts:
                    if not any(phrase in text.lower() for phrase in self.SKIP_PHRASES):
                        seen_texts.add(text)
                        paragraphs.append(text)
            else:
                # Skip blockquote elements that contain lists (will be processed via li elements)
                if element.name == 'blockquote' and (element.find('ul') or element.find('ol')):
                    continue
                
                # Skip blockquote elements that contain p tags (will be processed via p elements)
                # This prevents duplication where content appears first as a block, then with proper breaks
                if element.name == 'blockquote' and element.find('p'):
                    continue
                
                # For p elements that contain other p tags (malformed/unclosed HTML),
                # extract only direct text content (not from nested children)
                if element.name == 'p' and element.find('p'):
                    # Get only direct text nodes, not from descendants
                    direct_text = ''.join([str(s) for s in element.strings if s.parent == element]).strip()
                    if direct_text and direct_text not in seen_texts:
                        # Skip boilerplate
                        if not any(phrase in direct_text.lower() for phrase in self.SKIP_PHRASES):
                            direct_text = re.sub(r'\s*Return to text\s*$', '', direct_text, flags=re.IGNORECASE)
                            seen_texts.add(direct_text)
                            paragraphs.append(direct_text)
                    continue  # Skip normal processing for this element
                
                # For p, h3, blockquote - check for strong tags for headers
                strong_tags = element.find_all('strong', recursive=False)  # Only direct children
                if strong_tags and element.name == 'p':
                    # Check if the strong tag is at the beginning (likely a header)
                    first_strong = strong_tags[0]
                    strong_text = first_strong.get_text(strip=True)
                    
                    # Get remaining text after the strong tag
                    remaining_text = element.get_text(separator=' ', strip=True)
                    
                    # If the strong text is followed by <br/>, it's a header
                    if first_strong.find_next_sibling('br') or remaining_text == strong_text:
                        paragraphs.append(strong_text)
                        # If there's more text, add it separately
                        rest = remaining_text.replace(strong_text, '', 1).strip()
                        if rest:
                            paragraphs.append(rest)
                    else:
                        # Strong tag within paragraph, keep together
                        paragraphs.append(remaining_text)
                else:
                    # Regular paragraph - check for <BR><BR> which indicates paragraph breaks
                    html_str = str(element)
                    has_double_br = '<BR><BR>' in html_str.upper() or '<BR/><BR/>' in html_str.upper()
                    
                    if has_double_br and element.name == 'p':
                        # Split on double BR tags
                        # Convert to string, split on double BR, then parse each piece
                        html_content = str(element)
                        # Split on various double BR patterns (case-insensitive)
                        parts = re.split(r'<[Bb][Rr]\s*/?\s*>\s*<[Bb][Rr]\s*/?\s*>', html_content)
                        
                        for part in parts:
                            if not part.strip():
                                continue
                            # Parse this part as HTML to extract clean text
                            part_soup = BeautifulSoup(part, 'html.parser')
                            part_text = part_soup.get_text(separator=' ', strip=True)
                            
                            if part_text and part_text not in seen_texts:
                                if not any(phrase in part_text.lower() for phrase in self.SKIP_PHRASES):
                                    part_text = re.sub(r'\s*Return to text\s*$', '', part_text, flags=re.IGNORECASE)
                                    seen_texts.add(part_text)
                                    paragraphs.append(part_text)
                    else:
                        # Regular paragraph without double BR
                        text = element.get_text(separator=' ', strip=True)
                        if text:
                            # Skip common boilerplate
                            if any(phrase in text.lower() for phrase in self.SKIP_PHRASES):
                                continue
                            
                            # Skip duplicates
                            if text in seen_texts:
                                continue
                            
                            # Remove "Return to text" from footnotes
                            text = re.sub(r'\s*Return to text\s*$', '', text, flags=re.IGNORECASE)
                            
                            seen_texts.add(text)
                            paragraphs.append(text)
            
            # After processing each element, check if there's loose text immediately after it
            # This handles text nodes that are siblings of elements (between closing and opening tags)
            next_sibling = element.next_sibling
            if isinstance(next_sibling, str):
                text = next_sibling.strip()
                if text and text not in seen_texts:
                    # Skip if it's just whitespace or navigation
                    if not any(phrase in text.lower() for phrase in self.SKIP_PHRASES):
                        seen_texts.add(text)
                        paragraphs.append(text)
        
        # Join with paragraph breaks (double newlines)
        full_text = '\n\n'.join(paragraphs)
        
        # Remove specific unwanted patterns
        unwanted_patterns = [
            r'Please enable JavaScript if it is disabled in your browser.*?below\.',
            r'Last Update:.*'
        ]
        
        for pattern in unwanted_patterns:
            full_text = re.sub(pattern, '', full_text, flags=re.IGNORECASE | re.DOTALL)
        
        return self._clean_whitespace(full_text)
    
    def format_date(self, date_str: str) -> str:
        """
        Convert YYYYMMDD to ISO 8601 format (YYYY-MM-DD).
        
        Args:
            date_str: Date in YYYYMMDD format
            
        Returns:
            Date in YYYY-MM-DD format
        """
        year = date_str[:4]
        month = date_str[4:6]
        day = date_str[6:8]
        return f"{year}-{month}-{day}"
    
    def format_release_date(self, release_date_str: str) -> Optional[str]:
        """
        Convert release date from various formats to ISO 8601 format (YYYY-MM-DD).
        
        Args:
            release_date_str: Date string in formats like "July 06, 2022" or "May 21, 1998"
            
        Returns:
            Date in YYYY-MM-DD format, or None if parsing fails
        """
        if not release_date_str:
            return None
        
        # Common formats found in Fed minutes
        formats = [
            "%B %d, %Y",      # "July 06, 2022"
            "%B %d,%Y",       # "July 06,2022" (no space after comma)
            "%b %d, %Y",      # "Jul 06, 2022"
            "%b %d,%Y",       # "Jul 06,2022"
            "%B%d, %Y",       # "July06, 2022" (no space)
            "%B%d,%Y",        # "July06,2022"
        ]
        
        for fmt in formats:
            try:
                parsed_date = datetime.strptime(release_date_str.strip(), fmt)
                return parsed_date.strftime("%Y-%m-%d")
            except ValueError:
                continue
        
        # If no format worked, return None
        return None
    
    def save_clean_json(self, date_str: str, text_content: str, release_date: Optional[str] = None) -> Path:
        """
        Save clean JSON file with required format for minutes.
        
        Args:
            date_str: Date in YYYYMMDD format
            text_content: Cleaned text content
            release_date: Optional release date string (will be converted to YYYY-MM-DD format)
            
        Returns:
            Path to saved file
        """
        # Format release date to ISO 8601 format
        formatted_release_date = self.format_release_date(release_date) if release_date else None
        
        data = {
            "meeting_date": self.format_date(date_str),
            "release_date": formatted_release_date,
            "type": "minutes", 
            "text": text_content
        }
        
        filename = self.clean_dir / f"minutes{date_str}.json"
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        return filename
    
    def scrape_minutes(self, date_str: str) -> bool:
        """
        Scrape FOMC minutes for a single meeting date.
        
        Args:
            date_str: Date in YYYYMMDD format
            
        Returns:
            True if successful, False otherwise
        """
        urls = self.construct_minutes_urls(date_str)
        
        for url in urls:
            try:
                print(f"  Trying: {url}")
                response = self.session.get(url, timeout=self.REQUEST_TIMEOUT)
                
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
                        
                        if len(text_content) > self.MIN_MINUTES_LENGTH:
                            # Get release date from mapping (built from parent pages)
                            release_date = self.release_date_mapping.get(date_str)
                            
                            # Save raw HTML
                            raw_file = self.save_raw_html(date_str, html_content, url)
                            
                            # Save clean JSON
                            json_file = self.save_clean_json(date_str, text_content, release_date)
                            
                            # Calculate stats
                            char_count = len(text_content)
                            paragraph_count = len([p for p in text_content.split('\n\n') if p.strip()])
                            
                            print(f"  SUCCESS! Saved to {raw_file} and {json_file}")
                            print(f"  Stats: {char_count:,} chars, {paragraph_count} paragraphs")
                            if release_date:
                                print(f"  Release date: {release_date}")
                            return True
                        else:
                            print(f"  Content too short ({len(text_content)} chars)")
                    else:
                        print(f"  No FOMC minutes indicators found")
                else:
                    print(f"  HTTP {response.status_code}")
                    
            except requests.exceptions.RequestException as e:
                print(f"  Request error: {str(e)}")
            except Exception as e:
                print(f"  Unexpected error: {str(e)}")
            
            # Small delay between URL attempts
            time.sleep(self.DELAY_BETWEEN_URLS)
        
        return False
    
    def scrape_all_minutes(self) -> None:
        """Scrape all FOMC minutes from 1993 to 2025."""
        meeting_dates = self.get_known_fomc_dates()
        successful = 0
        failed = 0
        
        print(f"Starting FOMC minutes scraper for {len(meeting_dates)} dates...")
        print("=" * 60)
        
        for i, date_str in enumerate(meeting_dates, 1):
            print(f"[{i}/{len(meeting_dates)}] {date_str}: Scraping...")
            
            if self.scrape_minutes(date_str):
                successful += 1
            else:
                failed += 1
                print(f"  Failed to find minutes for {date_str}")
            
            # Respectful delay between meetings
            time.sleep(self.DELAY_BETWEEN_MEETINGS)
        
        print("=" * 60)
        print(f"Scraping complete!")
        print(f"Successful: {successful}")
        print(f"Failed: {failed}")
        print(f"Total processed: {successful + failed}")

def main() -> None:
    """Main entry point for the scraper."""
    scraper = FOMCMinutesScraper()
    scraper.scrape_all_minutes()

if __name__ == "__main__":
    main()