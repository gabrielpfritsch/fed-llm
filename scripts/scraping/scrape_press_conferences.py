import requests
import json
import os
import re
from datetime import datetime
import time
import PyPDF2
from io import BytesIO

class FOMCPressConferenceScraper:
    def __init__(self):
        self.base_url = "https://www.federalreserve.gov"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        
        # Create directories
        os.makedirs('data/fed-comms/press-confs/raw', exist_ok=True)
        os.makedirs('data/fed-comms/press-confs/clean', exist_ok=True)
    
    def get_known_press_conference_dates(self):
        """
        Get comprehensive list of known FOMC press conference dates from 2011-2025
        Based on research of Federal Reserve press conference schedule
        """
        # Press conferences started in 2011 and initially were quarterly (with SEP meetings)
        # Starting in 2019, they occur after every FOMC meeting
        
        known_dates = [
            # 2011 (First year - Chair Bernanke, quarterly)
            "20110427", "20110622", "20111102",
            
            # 2012 (quarterly)
            "20120425", "20120620", "20120913", "20121212",
            
            # 2013 (quarterly)
            "20130320", "20130619", "20130918", "20131218",
            
            # 2014 (quarterly)
            "20140319", "20140618", "20140917", "20141217",
            
            # 2015 (quarterly)
            "20150318", "20150617", "20150917", "20151216",
            
            # 2016 (quarterly)
            "20160316", "20160615", "20160921", "20161214",
            
            # 2017 (quarterly - Chair Yellen)
            "20170315", "20170614", "20170920", "20171213",
            
            # 2018 (quarterly - Chair Powell)
            "20180321", "20180613", "20180926", "20181219",
            
            # 2019 onwards (every meeting - Chair Powell announced this change)
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
            
            # 2025 (actual dates through July 24, 2025)
            "20250129", "20250319", "20250507", "20250618"
        ]
        
        return sorted(known_dates)
    
    def construct_press_conference_urls(self, date_str):
        """
        Construct possible URLs for FOMC press conference PDFs
        """
        urls = []
        
        # Primary PDF URL pattern
        urls.append(f"{self.base_url}/mediacenter/files/FOMCpresconf{date_str}.pdf")
        
        # Alternative patterns (some variations exist)
        urls.append(f"{self.base_url}/mediacenter/files/fomcpresconf{date_str}.pdf")
        urls.append(f"{self.base_url}/mediacenter/files/FOMC_presconf{date_str}.pdf")
        
        return urls
    
    def save_raw_pdf(self, date_str, pdf_content, url):
        """
        Save raw PDF content to file
        """
        filename = f"data/fed-comms/press-confs/raw/pressconf{date_str}.pdf"
        with open(filename, 'wb') as f:
            f.write(pdf_content)
        
        # Also save metadata
        metadata_file = f"data/fed-comms/press-confs/raw/pressconf{date_str}.meta"
        with open(metadata_file, 'w', encoding='utf-8') as f:
            f.write(f"Source URL: {url}\n")
            f.write(f"Downloaded: {datetime.now().isoformat()}\n")
            f.write(f"File size: {len(pdf_content)} bytes\n")
        
        return filename
    
    def extract_text_from_pdf(self, pdf_content):
        """
        Extract text from PDF content using PyPDF2
        """
        try:
            pdf_file = BytesIO(pdf_content)
            pdf_reader = PyPDF2.PdfReader(pdf_file)
            
            text_pages = []
            for page_num in range(len(pdf_reader.pages)):
                page = pdf_reader.pages[page_num]
                text = page.extract_text()
                if text.strip():
                    text_pages.append(text)
            
            # Join all pages
            full_text = '\n\n'.join(text_pages)
            return full_text
            
        except Exception as e:
            print(f"    Error extracting PDF text: {str(e)}")
            return None
    
    def clean_press_conference_text(self, raw_text):
        """
        Clean the extracted press conference transcript text
        Remove PDF headers, footers, and artifacts using regex patterns
        """
        if not raw_text:
            return ""
        
        # First, remove common PDF header/footer patterns using regex
        pdf_artifacts_patterns = [
            # Headers with date and chairman name (e.g., "December 19, 2018 Chairman Powell's Press Conference FINAL")
            r'[A-Za-z]+ \d{1,2},?\s+\d{4}\s+Chair(?:man|woman)?\s+[A-Za-z]+(?:\'s)?\s+Press Conference(?:\s+FINAL)?',
            
            # Date only headers (e.g., "December 18, 2024")
            r'^[A-Za-z]+ \d{1,2},?\s+\d{4}$',
            
            # Page numbers (e.g., "Page 1 of 22", "1 of 26", "FINAL 1 of 26")
            r'(?:FINAL\s+)?\d+\s+of\s+\d+',
            r'Page\s+\d+\s+of\s+\d+',
            r'^\s*Page\s*$',  # Standalone "Page" word
            
            # Standalone page numbers
            r'^\s*\d+\s*$',
            
            # Board of Governors references
            r'Board of Governors of the Federal Reserve System',
            
            # Website references
            r'www\.federalreserve\.gov',
            
            # FOMC references at start of lines
            r'^Federal Open Market Committee$',
            
            # FINAL markers
            r'^\s*FINAL\s*$',
            
            # Chairman/Chair references that appear alone
            r'^Chair(?:man|woman)?\s+[A-Za-z]+(?:\'s)?\s+Press Conference$'
        ]
        
        # Apply regex patterns to remove PDF artifacts
        cleaned_text = raw_text
        for pattern in pdf_artifacts_patterns:
            cleaned_text = re.sub(pattern, '', cleaned_text, flags=re.MULTILINE | re.IGNORECASE)
        
        # Remove any remaining scattered header elements across multiple lines
        comprehensive_cleanup_patterns = [
            # Complete header blocks that span multiple lines
            r'[A-Za-z]+ \d{1,2},?\s+\d{4}\s+Chair(?:man|woman)?\s+[A-Za-z]+(?:\'s)?\s+Press Conference[^\n]*\n',
            # Any line that starts with a date followed by Chair
            r'^[A-Za-z]+ \d{1,2},?\s+\d{4}.*?Chair.*?Press Conference.*?$',
            # Any line that just contains a date
            r'^[A-Za-z]+ \d{1,2},?\s+\d{4}\s*$',
        ]
        
        for pattern in comprehensive_cleanup_patterns:
            cleaned_text = re.sub(pattern, '', cleaned_text, flags=re.MULTILINE | re.IGNORECASE)
        
        # Split into lines for further processing
        lines = cleaned_text.split('\n')
        cleaned_lines = []
        
        content_started = False
        for line in lines:
            line = line.strip()
            
            # Skip empty lines initially
            if not line:
                if content_started:
                    # Keep empty lines once content has started (for paragraph breaks)
                    cleaned_lines.append('')
                continue
            
            # Look for the start of actual transcript content
            if not content_started:
                start_indicators = [
                    'CHAIR',
                    'Good afternoon',
                    'Good morning', 
                    'Thank you',
                    'My colleagues and I',
                    'The Federal Open Market Committee'
                ]
                
                if any(indicator.lower() in line.lower() for indicator in start_indicators):
                    content_started = True
                    cleaned_lines.append(line)
                continue
            
            # Once content started, include the line
            cleaned_lines.append(line)
        
        # Join lines back together
        full_text = '\n'.join(cleaned_lines)
        
        # Additional cleanup patterns for any remaining artifacts
        additional_cleanup_patterns = [
            # Remove any remaining transcript headers
            r'Transcript of Chair.*?Press Conference.*?\n',
            
            # Remove Federal Reserve Bank references
            r'Federal Reserve Bank of.*?\n',
            
            # Remove any remaining website references
            r'www\.federalreserve\.gov.*?\n',
            
            # Remove repeated "FINAL" words
            r'\bFINAL\b',
            
            # Clean up multiple consecutive newlines (more than 2)
            r'\n\s*\n\s*\n+',
        ]
        
        for pattern in additional_cleanup_patterns:
            if pattern == r'\n\s*\n\s*\n+':
                # Special handling for multiple newlines - replace with double newline
                full_text = re.sub(pattern, '\n\n', full_text)
            else:
                full_text = re.sub(pattern, '', full_text, flags=re.IGNORECASE)
        
        # Clean up extra whitespace
        full_text = re.sub(r' +', ' ', full_text)  # Multiple spaces to single
        full_text = full_text.strip()
        
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
        Save clean JSON file with required format for press conferences
        """
        data = {
            "meeting_date": self.format_date(date_str),
            "type": "press conference",
            "text": text_content
        }
        
        filename = f"data/fed-comms/press-confs/clean/pressconf{date_str}.json"
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        return filename
    
    def scrape_press_conference(self, date_str):
        """
        Scrape FOMC press conference transcript for a single meeting date
        """
        urls = self.construct_press_conference_urls(date_str)
        
        for url in urls:
            try:
                print(f"  Trying: {url}")
                response = self.session.get(url, timeout=30)
                
                if response.status_code == 200:
                    pdf_content = response.content
                    
                    # Validate this is a PDF file
                    if pdf_content.startswith(b'%PDF'):
                        # Extract text from PDF
                        raw_text = self.extract_text_from_pdf(pdf_content)
                        
                        if raw_text and len(raw_text) > 1000:  # Press conferences should be substantial
                            # Clean the text
                            clean_text = self.clean_press_conference_text(raw_text)
                            
                            if len(clean_text) > 500:
                                # Save raw PDF
                                raw_file = self.save_raw_pdf(date_str, pdf_content, url)
                                
                                # Save clean JSON
                                json_file = self.save_clean_json(date_str, clean_text)
                                
                                print(f"  SUCCESS! Saved to {raw_file} and {json_file}")
                                print(f"  Text length: {len(clean_text)} characters")
                                return True
                            else:
                                print(f"  Cleaned text too short ({len(clean_text)} chars)")
                        else:
                            print(f"  Could not extract sufficient text from PDF")
                    else:
                        print(f"  Response is not a valid PDF file")
                else:
                    print(f"  HTTP {response.status_code}")
                    
            except Exception as e:
                print(f"  Error: {str(e)}")
            
            # Small delay between URL attempts
            time.sleep(0.5)
        
        return False
    
    def scrape_all_press_conferences(self):
        """
        Scrape all FOMC press conferences from 2011 to 2025
        """
        conference_dates = self.get_known_press_conference_dates()
        successful = 0
        failed = 0
        skipped = 0
        
        print(f"Starting FOMC press conference scraper for {len(conference_dates)} dates...")
        print("=" * 60)
        
        for i, date_str in enumerate(conference_dates, 1):
            # Check if already exists
            raw_exists = os.path.exists(f"data/fed-comms/press-confs/raw/pressconf{date_str}.pdf")
            json_exists = os.path.exists(f"data/fed-comms/press-confs/clean/pressconf{date_str}.json")
            
            if raw_exists and json_exists:
                print(f"[{i}/{len(conference_dates)}] {date_str}: Already exists - skipping")
                skipped += 1
                continue
            
            print(f"[{i}/{len(conference_dates)}] {date_str}: Scraping press conference...")
            
            if self.scrape_press_conference(date_str):
                successful += 1
            else:
                failed += 1
                print(f"  Failed to find press conference for {date_str}")
            
            # Respectful delay between meetings
            time.sleep(2)
        
        print("=" * 60)
        print(f"Scraping complete!")
        print(f"Successful: {successful}")
        print(f"Failed: {failed}")
        print(f"Skipped: {skipped}")
        print(f"Total processed: {successful + failed + skipped}")
        print(f"Final press conference count: {successful}")

def main():
    scraper = FOMCPressConferenceScraper()
    scraper.scrape_all_press_conferences()

if __name__ == "__main__":
    main()