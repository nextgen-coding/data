#!/usr/bin/env python3
"""
Debug version of the comprehensive scraper to understand field extraction issues
"""

import csv
import json
import time
import logging
import os
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException
from webdriver_manager.chrome import ChromeDriverManager
import re

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('debug_scraper.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)

class DebugComprehensiveScraper:
    def __init__(self, headless=False):
        self.headless = headless
        self.driver = None
        self.setup_driver()
        
    def setup_driver(self):
        """Setup Chrome WebDriver with proper options"""
        try:
            chrome_options = Options()
            if self.headless:
                chrome_options.add_argument('--headless')
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-dev-shm-usage')
            chrome_options.add_argument('--disable-gpu')
            chrome_options.add_argument('--window-size=1920,1080')
            chrome_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36')
            
            service = Service(ChromeDriverManager().install())
            self.driver = webdriver.Chrome(service=service, options=chrome_options)
            logging.info("✅ Chrome WebDriver initialized successfully")
            
        except Exception as e:
            logging.error(f"❌ Failed to initialize WebDriver: {e}")
            raise
    
    def reinitialize_driver(self):
        """Reinitialize driver if it crashes"""
        try:
            if self.driver:
                self.driver.quit()
        except:
            pass
        self.setup_driver()

    def save_debug_html(self, ramz_code, page_source):
        """Save HTML for debugging purposes"""
        with open(f'debug_{ramz_code}.html', 'w', encoding='utf-8') as f:
            f.write(page_source)
        logging.info(f"Saved debug HTML: debug_{ramz_code}.html")

    def analyze_page_structure(self, ramz_code):
        """Debug function to analyze page structure"""
        try:
            logging.info(f"🔍 Analyzing page structure for {ramz_code}")
            
            # Find all tables
            tables = self.driver.find_elements(By.TAG_NAME, "table")
            logging.info(f"Found {len(tables)} tables")
            
            # Analyze each table
            for table_idx, table in enumerate(tables):
                rows = table.find_elements(By.TAG_NAME, "tr")
                logging.info(f"  Table {table_idx}: {len(rows)} rows")
                
                for row_idx, row in enumerate(rows[:5]):  # Only first 5 rows
                    cells = row.find_elements(By.TAG_NAME, "td")
                    if len(cells) >= 2:
                        label = cells[0].text.strip()
                        value = cells[1].text.strip()
                        logging.info(f"    Row {row_idx}: '{label}' -> '{value[:50]}...'")
            
            # Save debug HTML
            self.save_debug_html(ramz_code, self.driver.page_source)
            
        except Exception as e:
            logging.error(f"Error analyzing page structure: {e}")

    def extract_field_value_debug(self, label, ramz_code=""):
        """Extract field value with detailed debugging"""
        try:
            logging.info(f"🔎 Looking for field: '{label}'")
            
            # Find all table rows
            rows = self.driver.find_elements(By.XPATH, "//table//tr")
            logging.info(f"Found {len(rows)} total rows")
            
            matches_found = []
            
            for row_idx, row in enumerate(rows):
                try:
                    cells = row.find_elements(By.TAG_NAME, "td")
                    if len(cells) >= 2:
                        # Get the label cell (first cell)
                        label_cell = cells[0]
                        label_text = label_cell.text.strip()
                        
                        # Check for partial matches too
                        if label in label_text or label_text in label:
                            value_cell = cells[1]
                            value_text = value_cell.text.strip()
                            
                            matches_found.append({
                                'row': row_idx,
                                'label': label_text,
                                'value': value_text[:100]  # Truncate for logging
                            })
                            
                            logging.info(f"  Match found at row {row_idx}: '{label_text}' -> '{value_text[:50]}...'")
                            
                            # If exact match, return this value
                            if label == label_text:
                                # Try to get bold text first
                                bold_elements = value_cell.find_elements(By.TAG_NAME, "b")
                                if bold_elements:
                                    bold_texts = []
                                    for bold_elem in bold_elements:
                                        bold_text = bold_elem.text.strip()
                                        if bold_text and bold_text not in ['العنوان :', 'الهاتف :']:
                                            bold_texts.append(bold_text)
                                    
                                    if bold_texts:
                                        result = ' '.join(bold_texts)
                                        logging.info(f"  ✅ Returning bold text: '{result}'")
                                        return result
                                
                                # Clean up the full text
                                if value_text and not value_text.startswith('العنوان :'):
                                    cleaned_text = value_text.replace('العنوان :', '').replace('الهاتف :', '').strip()
                                    if cleaned_text:
                                        logging.info(f"  ✅ Returning cleaned text: '{cleaned_text}'")
                                        return cleaned_text
                                    else:
                                        logging.info(f"  ✅ Returning full text: '{value_text}'")
                                        return value_text
                                
                except Exception as e:
                    continue  # Skip problematic rows
            
            if matches_found:
                logging.info(f"  Found {len(matches_found)} partial matches but no exact match")
                # Return the first match if any
                first_match = matches_found[0]
                value_text = first_match['value']
                if value_text and not value_text.startswith('العنوان :'):
                    return value_text
            else:
                logging.info(f"  ❌ No matches found for '{label}'")
            
            return ""  # Not found
            
        except Exception as e:
            logging.warning(f"Error extracting field '{label}': {e}")
            return ""

    def scrape_ramz_data_debug(self, ramz_code, ramz_link, codes_set):
        """Scrape comprehensive data with debug output"""
        try:
            logging.info(f"🔍 Scraping {ramz_code}: {ramz_link}")
            
            # Check if driver is still valid
            try:
                self.driver.title
            except:
                logging.warning("Driver session invalid, reinitializing...")
                self.reinitialize_driver()
            
            # Load the page
            self.driver.get(ramz_link)
            
            # Wait for page to load
            WebDriverWait(self.driver, 15).until(
                EC.presence_of_element_located((By.TAG_NAME, "table"))
            )
            
            # Additional wait for JavaScript content
            time.sleep(5)
            
            # Debug: analyze page structure
            self.analyze_page_structure(ramz_code)
            
            # Extract ramz_id from URL
            ramz_id_match = re.search(r'id=(\d+)', ramz_link)
            ramz_id = ramz_id_match.group(1) if ramz_id_match else ""
            
            # Calculate bac_id (first digit of ramz_id)
            bac_id = ramz_id[0] if ramz_id and len(ramz_id) > 0 else "1"
            
            # Extract all fields with debug output
            fields_to_extract = [
                ('الجامعة', 'university'),
                ('الولاية', 'governorate'),
                ('المؤسسة', 'institution'),
                ('الشعبة / الإجازة', 'specialization_name'),
                ('رمز الشعبة', 'specialization_code_detailed'),
                ('مجال التكوين', 'field_of_study'),
                ('التخصصات', 'specializations_detailed'),
                ('المقياس', 'requirements'),
                ('نوع الباكالوريا', 'bac_type'),
                ('طاقة الإستعاب', 'capacity_2025'),
                ('شعبة تتطلب إختبار', 'requires_test'),
                ('التنفيل الجغرافي', 'geographical_distribution'),
                ('الشروط', 'conditions'),
                ('مدة الدراسة', 'study_duration'),
                ('مجموع آخر موجه 2024', 'last_oriented_score_2024')
            ]
            
            data = {
                'ramz_code': ramz_code,
                'bac_id': bac_id,
                'ramz_id': ramz_id,
                'ramz_link': ramz_link,
                'scraped_at': datetime.now().isoformat()
            }
            
            # Extract each field with debug output
            for arabic_label, english_key in fields_to_extract:
                value = self.extract_field_value_debug(arabic_label, ramz_code)
                data[english_key] = value
                logging.info(f"  {english_key}: '{value}'")
            
            # Initialize empty fields
            data['address'] = ""
            data['phone'] = ""
            data['historical_scores'] = {}
            
            # Extract address and phone from institution field if available
            institution_text = data['institution']
            if institution_text:
                # Look for address and phone patterns
                parts = institution_text.split()
                address_parts = []
                phone_parts = []
                
                found_address = False
                found_phone = False
                
                for i, part in enumerate(parts):
                    if 'العنوان' in part:
                        found_address = True
                        continue
                    elif 'الهاتف' in part:
                        found_phone = True
                        found_address = False
                        continue
                    
                    if found_address and not found_phone:
                        address_parts.append(part)
                    elif found_phone:
                        phone_parts.append(part)
                
                data['address'] = ' '.join(address_parts).strip()
                data['phone'] = ' '.join(phone_parts).strip()
            
            # Determine 7% benefit based on codes.csv
            last_three_digits = ramz_code[-3:] if len(ramz_code) >= 3 else ramz_code
            if last_three_digits in codes_set:
                data['seven_percent'] = 'لا'  # No benefit
            else:
                data['seven_percent'] = 'نعم'  # Has benefit
            
            # Log extraction summary
            non_empty_fields = sum(1 for k, v in data.items() 
                                 if k not in ['historical_scores', 'scraped_at'] 
                                 and v and str(v).strip())
            
            logging.info(f"✅ Extracted for {ramz_code}: {non_empty_fields} non-empty fields")
            return data
            
        except Exception as e:
            logging.error(f"❌ Extraction failed for {ramz_code}: {e}")
            return None

    def close(self):
        """Close the WebDriver"""
        if self.driver:
            self.driver.quit()
            logging.info("🔒 WebDriver closed")

def load_codes_csv():
    """Load codes.csv to determine which specializations don't get 7% bonus"""
    try:
        with open('codes.csv', 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            codes = set()
            for row in reader:
                if 'الرمز' in row and row['الرمز']:
                    codes.add(str(row['الرمز']).strip())
        logging.info(f"Loaded {len(codes)} codes that don't benefit from 7% bonus")
        return codes
    except Exception as e:
        logging.error(f"Error loading codes.csv: {e}")
        return set()

def load_ramz_links(limit=1):
    """Load ramz links from CSV file"""
    ramz_links = []
    try:
        with open('ramz_links.csv', 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for i, row in enumerate(reader):
                if limit and i >= limit:
                    break
                ramz_links.append({
                    'ramz_code': row['ramz_code'],
                    'ramz_link': row['ramz_link']
                })
        logging.info(f"Loaded {len(ramz_links)} ramz links")
        return ramz_links
    except Exception as e:
        logging.error(f"Error loading ramz_links.csv: {e}")
        return []

def main():
    """Main execution function"""
    logging.info("🚀 Starting debug scraping")
    
    # Load necessary data
    codes_set = load_codes_csv()
    
    # Load only 1 ramz link for debugging
    ramz_links = load_ramz_links(limit=1)
    
    if not ramz_links:
        logging.error("❌ No ramz links loaded")
        return
    
    scraper = None
    
    try:
        scraper = DebugComprehensiveScraper(headless=False)  # Not headless for debugging
        
        ramz_item = ramz_links[0]
        ramz_code = ramz_item['ramz_code']
        ramz_link = ramz_item['ramz_link']
        
        data = scraper.scrape_ramz_data_debug(ramz_code, ramz_link, codes_set)
        if data:
            print(f"\n✅ Successfully scraped {ramz_code}")
            print(f"Data extracted: {json.dumps(data, ensure_ascii=False, indent=2)}")
        else:
            print(f"❌ Failed to scrape {ramz_code}")
    
    except Exception as e:
        logging.error(f"❌ Main execution error: {e}")
    
    finally:
        if scraper:
            scraper.close()

if __name__ == "__main__":
    main()
