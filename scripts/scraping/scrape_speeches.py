import requests
import json
import os
import re
from datetime import datetime
from bs4 import BeautifulSoup
import time
from urllib.parse import urljoin
import random

class FOMCSpeechScraper:
    def __init__(self):
        self.base_url = "https://www.federalreserve.gov"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        
        # Create directories
        os.makedirs('data/fed-comms/speeches/raw', exist_ok=True)
        os.makedirs('data/fed-comms/speeches/clean', exist_ok=True)
    
    def get_speeches_for_year(self, year):
        """
        Get list of speeches for a specific year by scraping the year's speech page
        """
        speeches = []
        
        # Different URL patterns for different year ranges
        if year >= 2011:
            # Modern format: 2024-speeches.htm (starts from 2011)
            url = f"{self.base_url}/newsevents/speech/{year}-speeches.htm"
        else:
            # Historical format: 2005speech.htm (2000-2010)
            url = f"{self.base_url}/newsevents/speech/{year}speech.htm"
        
        try:
            print(f"  Fetching speeches list for {year}: {url}")
            
            def fetch_page():
                return self.session.get(url, timeout=15)
            
            response = self.retry_with_backoff(fetch_page)
            
            if response and response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                
                if year >= 2011:
                    speeches = self.parse_modern_speeches_page(soup, year)
                else:
                    speeches = self.parse_historical_speeches_page(soup, year)
                    
                print(f"  Found {len(speeches)} speeches for {year}")
                return speeches
            else:
                print(f"  Failed to fetch {year} speeches: HTTP {response.status_code}")
                return []
                
        except Exception as e:
            print(f"  Error fetching {year} speeches: {str(e)}")
            return []
    
    def parse_modern_speeches_page(self, soup, year):
        """
        Parse speeches from modern format pages (2006+)
        """
        speeches = []
        
        # Look for speech entries in the main content
        # Modern pages typically have date, title, speaker, event structure
        content_div = soup.find('div', {'id': 'content'}) or soup.find('div', class_='col-xs-12') or soup
        
        # Find all potential speech blocks
        speech_blocks = []
        
        # Look for date patterns followed by links
        date_pattern = r'(\d{1,2}/\d{1,2}/\d{4})'
        text_content = content_div.get_text()
        
        # Find all links that look like speech links
        speech_links = content_div.find_all('a', href=re.compile(r'/newsevents/speech/\w+\d{8}[a-z]?\.htm'))
        
        for link in speech_links:
            try:
                # Get the link URL and extract date from it
                href = link.get('href')
                title = link.get_text().strip()
                
                # Extract date from URL (format: speakernameYYYYMMDD.htm)
                date_match = re.search(r'(\d{8})', href)
                if not date_match:
                    continue
                    
                date_str = date_match.group(1)
                speech_year = int(date_str[:4])
                
                # Only include speeches from the current year
                if speech_year != year:
                    continue
                
                # Find the surrounding context to get speaker and event info
                parent = link.find_parent()
                if not parent:
                    continue
                
                # Navigate up to find the speech block
                speech_block = parent
                for _ in range(5):  # Look up to 5 levels up
                    if speech_block and speech_block.name:
                        text = speech_block.get_text()
                        if date_str[:4] in text or any(month in text for month in ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December']):
                            break
                    speech_block = speech_block.find_parent() if speech_block else None
                
                if not speech_block:
                    speech_block = parent
                
                # Extract speaker and event from the block text
                block_text = speech_block.get_text()
                lines = [line.strip() for line in block_text.split('\n') if line.strip()]
                
                speaker = ""
                event = ""
                
                # Look for speaker patterns
                for line in lines:
                    if any(title_word in line for title_word in ['Governor', 'Chair', 'President', 'Vice Chair']):
                        speaker = line
                        break
                
                # Look for event/location patterns
                for line in lines:
                    if 'At ' in line or 'at ' in line:
                        event = line
                        break
                
                # If we couldn't find event, use the last meaningful line
                if not event and len(lines) > 2:
                    event = lines[-1]
                
                speeches.append({
                    'date': date_str,
                    'title': title,
                    'speaker': speaker,
                    'event': event,
                    'url': urljoin(self.base_url, href)
                })
                
            except Exception as e:
                print(f"    Error parsing speech link: {str(e)}")
                continue
        
        return speeches
    
    def parse_historical_speeches_page(self, soup, year):
        """
        Parse speeches from historical format pages (2000-2005)
        """
        speeches = []
        
        # Historical pages have a different structure
        # Look for bullet points or list items with speech information
        content = soup.find('body') or soup
        
        # Find all links that look like speech links 
        # Pattern 1: boarddocs/speeches (2000-2005)
        speech_links_pattern1 = content.find_all('a', href=re.compile(r'/boarddocs/speeches/\d{4}/\d{8}'))
        # Pattern 2: newsevents/speech (2006-2010)  
        speech_links_pattern2 = content.find_all('a', href=re.compile(r'/newsevents/speech/\w+\d{8}[a-z]?\.htm'))
        
        speech_links = speech_links_pattern1 + speech_links_pattern2
        
        for link in speech_links:
            try:
                href = link.get('href')
                title = link.get_text().strip()
                
                # Extract date from URL - handle multiple patterns
                date_str = None
                
                # Pattern 1: /boarddocs/speeches/2004/20041202/ (standard 8-digit with slashes)
                date_match = re.search(r'/(\d{8})/', href)
                if date_match:
                    date_str = date_match.group(1)
                
                # Pattern 2: /speeches/2000/200012062.htm (9-digit - extract properly)
                if not date_str:
                    date_match = re.search(r'/(\d{9})\.htm', href)
                    if date_match:
                        nine_digit = date_match.group(1)
                        # For URLs like /2000/200012062.htm, the date is YYYYMMDX where X is extra
                        # Extract YYYYMMDD: take first 4 digits (year) + digits 5-8 (MMDD from the 9-digit)
                        if nine_digit.startswith('2000'):
                            # 200012062 -> 20001206 (year + month + day)
                            year = nine_digit[:4]  # 2000
                            month_day = nine_digit[4:8]  # 1206
                            date_str = year + month_day  # 20001206
                        else:
                            date_str = nine_digit[:8]  # fallback to first 8
                
                # Pattern 3: /speech/duke20101202a.htm (8-digit before .htm)
                if not date_str:
                    date_match = re.search(r'(\d{8})[a-z]?\.htm', href)
                    if date_match:
                        date_str = date_match.group(1)
                
                if not date_str:
                    continue
                
                # For historical speeches, we need to scrape the individual page
                # to get accurate speaker and event information
                speaker, event = self.get_historical_speech_metadata(urljoin(self.base_url, href))
                
                speeches.append({
                    'date': date_str,
                    'title': title,
                    'speaker': speaker,
                    'event': event,
                    'url': urljoin(self.base_url, href)
                })
                
            except Exception as e:
                print(f"    Error parsing historical speech: {str(e)}")
                continue
        
        return speeches
    
    def get_historical_speech_metadata(self, url):
        """
        Extract speaker and event information from individual historical speech pages
        """
        try:
            def fetch_metadata():
                return self.session.get(url, timeout=10)
            
            response = self.retry_with_backoff(fetch_metadata)
            if response and response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # Historical speech pages have the format:
                # "Remarks by Governor Ben S. Bernanke"
                # "Before the National Economists Club, Washington, D.C."
                # "December 2, 2004"
                
                # Get the main content
                body = soup.find('body') or soup
                text_content = body.get_text()
                
                # Look for the "Remarks by" pattern
                speaker = ""
                event = ""
                
                # Split into lines and look for the header information
                lines = [line.strip() for line in text_content.split('\n') if line.strip()]
                
                for i, line in enumerate(lines):
                    # Look for "Remarks by" or similar patterns
                    if 'remarks by' in line.lower() or 'statement by' in line.lower() or 'speech by' in line.lower():
                        # Extract speaker from this line
                        if 'by' in line.lower():
                            speaker_part = line.split('by', 1)[1].strip()
                            speaker = speaker_part
                        
                        # Look for event in the next few lines
                        for j in range(i+1, min(i+4, len(lines))):
                            next_line = lines[j]
                            # Event lines often start with "Before", "At", "To"
                            if any(prefix in next_line.lower() for prefix in ['before', 'at the', 'to the', 'delivered']):
                                event = next_line
                                break
                        break
                    
                    # Alternative pattern: look for Governor/Chairman titles at start of lines
                    elif any(title in line for title in ['Governor ', 'Chairman ', 'Vice Chairman ', 'President ']):
                        # Check if this looks like a speaker line (not just mention in text)
                        if len(line) < 100 and not '.' in line:  # Short line, no periods (likely header)
                            speaker = line
                            # Look for event in next line
                            if i+1 < len(lines):
                                next_line = lines[i+1]
                                if any(prefix in next_line.lower() for prefix in ['before', 'at the', 'to the', 'delivered']):
                                    event = next_line
                            break
                
                return speaker, event
            
        except Exception as e:
            print(f"      Error fetching metadata from {url}: {str(e)}")
            
        return "", ""
    
    def rate_limit_delay(self, min_delay=1.0, max_delay=3.0):
        """
        Implement respectful rate limiting with random delays
        """
        delay = random.uniform(min_delay, max_delay)
        time.sleep(delay)
    
    def retry_with_backoff(self, func, max_retries=3, base_delay=1.0):
        """
        Retry function with exponential backoff
        """
        for attempt in range(max_retries):
            try:
                return func()
            except Exception as e:
                if attempt == max_retries - 1:
                    raise e
                delay = base_delay * (2 ** attempt) + random.uniform(0, 1)
                print(f"    Retry {attempt + 1}/{max_retries} after {delay:.1f}s delay: {str(e)}")
                time.sleep(delay)
        return None
    
    def scrape_individual_speech(self, speech_info):
        """
        Scrape the content of an individual speech
        """
        try:
            # Handle potential encoding issues in titles
            safe_title = speech_info['title'].encode('ascii', 'ignore').decode('ascii')
            print(f"    Scraping: {safe_title}")
            
            def fetch_speech():
                return self.session.get(speech_info['url'], timeout=15)
            
            response = self.retry_with_backoff(fetch_speech)
            
            if response and response.status_code == 200:
                html_content = response.text
                soup = BeautifulSoup(html_content, 'html.parser')
                
                # Extract speech text
                speech_text = self.extract_speech_text(soup, speech_info['url'])
                
                if len(speech_text) > 200:  # Must have substantial content
                    # Save raw HTML
                    raw_file = self.save_raw_html(speech_info['date'], html_content, speech_info['url'])
                    
                    # Save clean JSON
                    json_file = self.save_clean_json(speech_info, speech_text)
                    
                    print(f"    SUCCESS! Saved {len(speech_text)} chars to {json_file}")
                    return True
                else:
                    print(f"    Content too short ({len(speech_text)} chars)")
                    return False
            else:
                print(f"    HTTP {response.status_code}")
                return False
                
        except Exception as e:
            print(f"    Error: {str(e)}")
            return False
    
    def extract_speech_text(self, soup, url_hint=None):
        """
        Extract clean speech text from the HTML
        """
        # Remove scripts, styles, navigation
        for element in soup(["script", "style", "nav", "header", "footer"]):
            element.decompose()
        
        # Check if this is a historical page using URL hint or soup content
        is_historical = False
        if url_hint:
            is_historical = '/boarddocs/speeches/' in url_hint or (
                '/newsevents/speech/' in url_hint and 
                not any(year in url_hint for year in ['2011', '2012', '2013', '2014', '2015', '2016', '2017', '2018', '2019', '2020', '2021', '2022', '2023', '2024', '2025'])
            )
        
        if not is_historical:
            # Fallback: check soup content for historical indicators
            soup_text = str(soup)
            is_historical = '/boarddocs/speeches/' in soup_text or (
                'Federal Reserve Board' in soup_text and 
                len(soup.find_all('table')) >= 2
            )
        
        if is_historical:
            return self.extract_historical_speech_text(soup)
        
        # Find main content area for modern speeches
        content_selectors = [
            'div#content',
            'div.col-xs-12',
            'main',
            'article',
            'div[class*="content"]'
        ]
        
        main_content = None
        for selector in content_selectors:
            main_content = soup.select_one(selector)
            if main_content:
                break
        
        if not main_content:
            main_content = soup.find('body') or soup
        
        # Extract paragraphs
        paragraphs = []
        for element in main_content.find_all(['p', 'div']):
            text = element.get_text().strip()
            if len(text) > 20:  # Skip very short text
                # Skip common navigation/header text
                skip_phrases = [
                    'for immediate release', 'board of governors', 'federal reserve system',
                    'last update', 'share', 'print', 'email', 'accessibility', 'contact',
                    'subscribe', 'back to top', 'main navigation', 'search', 'home',
                    'skip to main content', 'you are here:', 'breadcrumb',
                    'watch live', 'pdf', 'accessible version'
                ]
                
                if not any(phrase in text.lower() for phrase in skip_phrases):
                    paragraphs.append(text)
        
        # Join paragraphs
        full_text = '\n\n'.join(paragraphs)
        
        # Remove JavaScript warning and redundant metadata from the beginning
        full_text = self.clean_speech_text_start(full_text)
        
        # Clean up whitespace
        full_text = re.sub(r'\s+', ' ', full_text)  # Multiple spaces to single
        full_text = re.sub(r'\n\s*\n\s*\n+', '\n\n', full_text)  # Multiple newlines to double
        
        return full_text.strip()
    
    def clean_speech_text_start(self, text):
        """
        Remove JavaScript warning and redundant metadata from the beginning of speech text
        """
        # Remove the JavaScript warning
        javascript_pattern = r'^Please enable JavaScript if it is disabled in your browser or access the information through the links provided below\.\s*'
        text = re.sub(javascript_pattern, '', text, flags=re.IGNORECASE)
        
        # Remove redundant speaker and event information at the start
        # Pattern: "Governor/Chairman Name At/Before event location"
        lines = text.split('\n')
        cleaned_lines = []
        content_started = False
        
        for i, line in enumerate(lines):
            line = line.strip()
            if not line:
                if content_started:
                    cleaned_lines.append('')
                continue
            
            # Skip redundant metadata lines at the beginning
            if not content_started:
                # Skip lines that are just the speaker name
                if any(title in line for title in ['Governor ', 'Chairman ', 'Chair ', 'President ', 'Vice Chairman ']):
                    # Check if this is just metadata (short line, no periods)
                    if len(line) < 100 and line.count('.') <= 1:
                        continue
                
                # Skip lines that are just event locations
                if any(prefix in line for prefix in ['At the ', 'Before the ', 'To the ', 'Delivered at ']):
                    if len(line) < 150 and line.count('.') <= 1:
                        continue
                
                # Look for actual speech content starting
                # Speech content usually starts with substantive text, greetings, or "Thank you"
                if any(starter in line.lower() for starter in [
                    'thank you', 'good morning', 'good afternoon', 'good evening',
                    'it is my pleasure', 'i am pleased', 'let me start', 'i want to',
                    'today i', 'this morning', 'this afternoon', 'welcome', 'i am here'
                ]) or len(line) > 100:
                    content_started = True
                    cleaned_lines.append(line)
                    continue
            else:
                cleaned_lines.append(line)
        
        return '\n'.join(cleaned_lines).strip()
    
    def extract_historical_speech_text(self, soup):
        """
        Extract text from historical FOMC speeches (2000-2010 era)
        Uses structural HTML patterns rather than text-based detection
        """
        # Remove scripts, styles, navigation
        for element in soup(["script", "style", "nav", "header", "footer"]):
            element.decompose()
        
        body = soup.find('body')
        if not body:
            body = soup
        
        # Historical speeches follow a consistent table structure:
        # Table 1: Metadata (speaker, venue, date)
        # Table 2+: Speech content (title + actual speech text)
        # Last table: Navigation/footer
        
        tables = body.find_all('table')
        
        if len(tables) >= 2:
            speech_text = ""
            
            # Find the main content table by looking for the one with actual speech content
            for table in tables:
                table_text = table.get_text().strip()
                
                # Skip navigation tables (short with navigation words)
                if any(nav_word in table_text.lower() for nav_word in [
                    'return to top', 'home', 'search', 'skip to', 'last update',
                    'contact us', 'privacy', 'accessibility'
                ]) and len(table_text) < 500:
                    continue
                
                # Skip pure metadata tables (short, just speaker/venue/date info)
                if (len(table_text) < 500 and 
                    any(meta_word in table_text.lower() for meta_word in [
                        'remarks by', 'speech by', 'statement by'
                    ])):
                    continue
                
                # This should be the main content table
                if len(table_text) > 500:  # Must have substantial content
                    # Get the table text and clean it 
                    table_text_clean = table_text.strip()
                    
                    # Look for the first sentence that clearly starts the speech
                    # First, handle cases where title and first sentence are on the same line
                    # Look for common speech starter patterns (only obvious greetings)
                    speech_starters = [
                        r'\bThank you\b',
                        r'\bGood morning\b',
                        r'\bGood afternoon\b', 
                        r'\bGood evening\b',
                        r'\bIt is my pleasure\b'
                    ]
                    
                    # Find the earliest occurrence of any speech starter
                    earliest_match = None
                    earliest_pos = len(table_text_clean)
                    
                    for pattern in speech_starters:
                        match = re.search(pattern, table_text_clean, re.IGNORECASE)
                        if match and match.start() < earliest_pos:
                            earliest_match = match
                            earliest_pos = match.start()
                    
                    if earliest_match and earliest_pos < len(table_text_clean) * 0.5:
                        # Start from the earliest pattern onwards (only if in first half)
                        speech_text = table_text_clean[earliest_match.start():].strip()
                        break
                    
                    # Split by sentences and find where speech content begins
                    sentences = re.split(r'(?<=[.!?])\s+', table_text_clean)
                    
                    speech_content = ""
                    found_start = False
                    
                    for sentence in sentences:
                        sentence = sentence.strip()
                        if not sentence or len(sentence) < 20:
                            continue
                        
                        # Skip metadata/title sentences
                        if not found_start:
                            # Skip obvious titles (short, no periods, all caps, title-like)
                            if (len(sentence) < 200 and 
                                sentence.count('.') == 0 and
                                (sentence.isupper() or  # All caps titles
                                 ':' in sentence or  # Titles often have colons
                                 sentence.count(' ') < 3)):  # Very short phrases
                                continue
                            
                            # Skip date lines and metadata
                            if any(meta in sentence.lower() for meta in [
                                'january', 'february', 'march', 'april', 'may', 'june',
                                'july', 'august', 'september', 'october', 'november', 'december',
                                'remarks by', 'speech by', 'statement by'
                            ]) and len(sentence) < 300:
                                continue
                            
                            # Start including from first substantial sentence
                            found_start = True
                        
                        if found_start:
                            speech_content += sentence + " "
                    
                    if speech_content:
                        speech_text = speech_content.strip()
                        break  # Found content, stop looking
            
            if speech_text:
                # Clean up whitespace
                speech_text = re.sub(r'\s+', ' ', speech_text)
                speech_text = re.sub(r'\n\s*\n\s*\n+', '\n\n', speech_text)
                return speech_text.strip()
        
        # Fallback: use the original method if table structure doesn't work
        full_text = body.get_text()
        lines = [line.strip() for line in full_text.split('\n') if line.strip()]
        
        # Filter out navigation/header/footer content
        filtered_lines = []
        for line in lines:
            skip_patterns = [
                'board of governors of the federal reserve system', 'home', 'search',
                'accessibility', 'contact us', 'privacy program', 'foia', 'skip to',
                'return to top', 'last update'
            ]
            
            if not any(pattern in line.lower() for pattern in skip_patterns):
                filtered_lines.append(line)
        
        # Join and apply fallback speech detection
        raw_text = ' '.join(filtered_lines)
        clean_text = self.find_speech_beginning(raw_text)
        
        # Clean up whitespace
        clean_text = re.sub(r'\s+', ' ', clean_text)
        
        return clean_text.strip()
    
    def find_speech_beginning(self, text):
        """
        Fallback method for finding speech beginning when structural approach fails
        Only uses obvious starter words as last resort
        """
        # Split into sentences for analysis
        sentences = re.split(r'(?<=[.!?])\s+', text)
        
        # Skip obvious metadata/navigation sentences
        for i, sentence in enumerate(sentences):
            sentence = sentence.strip()
            if len(sentence) < 20:
                continue
                
            # Skip navigation and metadata
            if any(skip_phrase in sentence.lower() for skip_phrase in [
                'return to top', 'back to', 'skip to', 'home', 'search',
                'contact us', 'privacy', 'accessibility', 'remarks by',
                'speech by', 'statement by'
            ]):
                continue
            
            # Only use obvious greeting patterns as fallback
            obvious_starters = [
                r'^(Thank you|Good morning|Good afternoon|Good evening)\b',
                r'^(It is (my |a )?pleasure)\b'
            ]
            
            for pattern in obvious_starters:
                if re.match(pattern, sentence, re.IGNORECASE):
                    remaining_sentences = sentences[i:]
                    return ' '.join(remaining_sentences)
            
            # If we find a substantial sentence that's clearly content, use it
            if (len(sentence) > 80 and 
                sentence.count(',') >= 1 and  # Complex sentence structure
                any(word in sentence.lower() for word in ['economic', 'policy', 'federal', 'financial', 'monetary'])):
                remaining_sentences = sentences[i:]
                return ' '.join(remaining_sentences)
        
        # Final fallback: return first substantial sentence
        for sentence in sentences:
            if len(sentence.strip()) > 100:
                idx = sentences.index(sentence)
                return ' '.join(sentences[idx:])
        
        return text
    
    def save_raw_html(self, date_str, html_content, url):
        """
        Save raw HTML content to file
        """
        filename = f"data/fed-comms/speeches/raw/speech{date_str}.html"
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(f"<!-- Source URL: {url} -->\n")
            f.write(f"<!-- Scraped: {datetime.now().isoformat()} -->\n")
            f.write(html_content)
        return filename
    
    def format_date(self, date_str):
        """
        Convert YYYYMMDD to DD-MM-YYYY format
        """
        year = date_str[:4]
        month = date_str[4:6]
        day = date_str[6:8]
        return f"{day}-{month}-{year}"
    
    def save_clean_json(self, speech_info, text_content):
        """
        Save clean JSON file with required format for speeches
        """
        data = {
            "date": self.format_date(speech_info['date']),
            "title": speech_info['title'],
            "official": speech_info['speaker'],
            "event": speech_info['event'],
            "text": text_content
        }
        
        filename = f"data/fed-comms/speeches/clean/speech{speech_info['date']}.json"
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        return filename
    
    def scrape_speeches_for_year(self, year):
        """
        Scrape all speeches for a specific year
        """
        print(f"Scraping speeches for {year}...")
        
        # Get list of speeches for the year
        speeches = self.get_speeches_for_year(year)
        
        if not speeches:
            print(f"  No speeches found for {year}")
            return 0, 0
        
        successful = 0
        failed = 0
        
        for i, speech in enumerate(speeches, 1):
            # Check if already exists
            json_exists = os.path.exists(f"data/fed-comms/speeches/clean/speech{speech['date']}.json")
            
            if json_exists:
                print(f"  [{i}/{len(speeches)}] {speech['date']}: Already exists - skipping")
                continue
            
            # Handle potential encoding issues in titles
            safe_title = speech['title'].encode('ascii', 'ignore').decode('ascii')
            print(f"  [{i}/{len(speeches)}] {speech['date']}: {safe_title}")
            
            if self.scrape_individual_speech(speech):
                successful += 1
            else:
                failed += 1
            
            # Respectful delay with rate limiting
            self.rate_limit_delay(1.0, 2.0)
        
        return successful, failed
    
    def scrape_all_speeches(self):
        """
        Scrape all FOMC speeches from 2000 to 2025
        """
        total_successful = 0
        total_failed = 0
        current_year = datetime.now().year
        
        print(f"Starting FOMC speech scraper for years 2000-{current_year}...")
        print("=" * 60)
        
        for year in range(2000, current_year + 1):
            successful, failed = self.scrape_speeches_for_year(year)
            total_successful += successful
            total_failed += failed
            
            # Longer delay between years to be respectful
            self.rate_limit_delay(3.0, 5.0)
        
        print("=" * 60)
        print(f"Speech scraping complete!")
        print(f"Total successful: {total_successful}")
        print(f"Total failed: {total_failed}")
        print(f"Total speeches scraped: {total_successful}")

def main():
    scraper = FOMCSpeechScraper()
    scraper.scrape_all_speeches()

if __name__ == "__main__":
    main()