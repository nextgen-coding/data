#!/usr/bin/env python3
"""
Final comprehensive scraper for all ramz data with improved field extraction
Based on the working test_comprehensive_extraction.py logic
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
        logging.FileHandler('final_comprehensive_scraper.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)

class FinalComprehensiveScraper:
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

    def extract_field_value(self, label):
        """Extract field value using the proven table traversal method"""
        try:
            # Find all table rows
            rows = self.driver.find_elements(By.XPATH, "//table//tr")
            
            for row in rows:
                try:
                    cells = row.find_elements(By.TAG_NAME, "td")
                    if len(cells) >= 2:
                        # Get the label cell (first cell)
                        label_cell = cells[0]
                        label_text = label_cell.text.strip()
                        
                        # Check if this row contains our target label
                        if label in label_text:
                            # Get the value cell (second cell)
                            value_cell = cells[1]
                            
                            # First try to get bold text within the value cell
                            bold_elements = value_cell.find_elements(By.TAG_NAME, "b")
                            if bold_elements:
                                bold_texts = []
                                for bold_elem in bold_elements:
                                    bold_text = bold_elem.text.strip()
                                    if bold_text and bold_text not in ['العنوان :', 'الهاتف :']:
                                        bold_texts.append(bold_text)
                                
                                if bold_texts:
                                    return ' '.join(bold_texts)
                            
                            # If no meaningful bold text, get the full cell text
                            full_text = value_cell.text.strip()
                            
                            # Clean up common artifacts
                            if full_text and not full_text.startswith('العنوان :'):
                                # Remove common prefixes/suffixes
                                cleaned_text = full_text.replace('العنوان :', '').replace('الهاتف :', '').strip()
                                if cleaned_text:
                                    return cleaned_text
                                else:
                                    return full_text
                            
                except Exception as e:
                    continue  # Skip problematic rows
            
            return ""  # Not found
            
        except Exception as e:
            logging.warning(f"Error extracting field '{label}': {e}")
            return ""

    def extract_historical_scores(self):
        """Extract historical scores from JavaScript charts"""
        historical_scores = {}
        try:
            # Wait for charts to load
            time.sleep(3)
            
            # Try to extract from Highcharts
            chart_data = self.driver.execute_script("""
                try {
                    if (typeof Highcharts !== 'undefined' && Highcharts.charts && Highcharts.charts.length > 0) {
                        var chart = Highcharts.charts[0];
                        if (chart && chart.series && chart.series.length > 0) {
                            var series = chart.series[0];
                            if (series.data && series.data.length > 0) {
                                return series.data.map(function(point) {
                                    return {
                                        year: point.category || point.name || point.x,
                                        score: point.y || point.value
                                    };
                                });
                            }
                        }
                    }
                    return null;
                } catch(e) {
                    return null;
                }
            """)
            
            if chart_data and isinstance(chart_data, list):
                for point in chart_data:
                    if point and 'year' in point and 'score' in point:
                        year_str = str(point['year'])
                        score = point['score']
                        if year_str and str(score).replace('.', '').isdigit():
                            historical_scores[year_str] = float(score)
            
            # Alternative method: try to find data in script tags
            if not historical_scores:
                try:
                    scripts = self.driver.find_elements(By.TAG_NAME, "script")
                    for script in scripts:
                        script_content = script.get_attribute("innerHTML") or ""
                        if "data:" in script_content and "[" in script_content:
                            # Look for data arrays in JavaScript
                            data_matches = re.findall(r'data:\s*\[([\d\.,\s]+)\]', script_content)
                            if data_matches:
                                # This would need more specific parsing based on the actual format
                                pass
                except Exception as e:
                    logging.debug(f"Alternative extraction failed: {e}")
            
            logging.info(f"Extracted {len(historical_scores)} historical scores")
            return historical_scores
            
        except Exception as e:
            logging.warning(f"Error extracting historical scores: {e}")
            return {}

    def scrape_ramz_data(self, ramz_code, ramz_link, codes_set):
        """Scrape comprehensive data from a ramz detail page"""
        try:
            logging.info(f"🔍 Scraping {ramz_code}: {ramz_link}")
            
            # Load the page
            self.driver.get(ramz_link)
            
            # Wait for page to load
            WebDriverWait(self.driver, 15).until(
                EC.presence_of_element_located((By.TAG_NAME, "table"))
            )
            
            # Additional wait for JavaScript content
            time.sleep(5)
            
            # Extract ramz_id from URL
            ramz_id_match = re.search(r'id=(\d+)', ramz_link)
            ramz_id = ramz_id_match.group(1) if ramz_id_match else ""
            
            # Calculate bac_id (first digit of ramz_id)
            bac_id = ramz_id[0] if ramz_id and len(ramz_id) > 0 else "1"
            
            # Extract all fields using the proven method
            data = {
                'ramz_code': ramz_code,
                'bac_id': bac_id,
                'ramz_id': ramz_id,
                'ramz_link': ramz_link,
                
                # Basic information
                'university': self.extract_field_value('الجامعة'),
                'governorate': self.extract_field_value('الولاية'),
                'institution': self.extract_field_value('المؤسسة'),
                
                # Academic information
                'specialization_name': self.extract_field_value('الشعبة / الإجازة'),
                'specialization_code_detailed': self.extract_field_value('رمز الشعبة'),
                'field_of_study': self.extract_field_value('مجال التكوين'),
                'specializations_detailed': self.extract_field_value('التخصصات'),
                'requirements': self.extract_field_value('المقياس'),
                'bac_type': self.extract_field_value('نوع الباكالوريا'),
                
                # Program details
                'capacity_2025': self.extract_field_value('طاقة الإستعاب'),
                'requires_test': self.extract_field_value('شعبة تتطلب إختبار'),
                'geographical_distribution': self.extract_field_value('التنفيل الجغرافي'),
                'conditions': self.extract_field_value('الشروط'),
                'study_duration': self.extract_field_value('مدة الدراسة'),
                
                # Admission scores
                'last_oriented_score_2024': self.extract_field_value('مجموع آخر موجه 2024'),
                'historical_scores': self.extract_historical_scores(),
                
                # Metadata
                'scraped_at': datetime.now().isoformat()
            }
            
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
            else:
                data['address'] = ""
                data['phone'] = ""
            
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
            historical_count = len(data['historical_scores'])
            
            logging.info(f"✅ Extracted for {ramz_code}: {non_empty_fields} fields, {historical_count} historical scores")
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

def load_ramz_links(limit=None):
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

def save_results(data, filename_prefix="tunisia_university_final"):
    """Save results in JSON and CSV formats"""
    
    if not data:
        logging.error("No data to save")
        return
    
    # Create data directory if it doesn't exist
    os.makedirs('data', exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Save JSON
    json_filename = f"data/{filename_prefix}_{timestamp}.json"
    with open(json_filename, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    logging.info(f"💾 Saved JSON: {json_filename}")
    
    # Prepare CSV data (flatten historical scores)
    csv_data = []
    for record in data:
        # Create base record without historical scores
        csv_record = {k: v for k, v in record.items() if k != 'historical_scores'}
        
        # Add historical scores as separate columns
        historical = record.get('historical_scores', {})
        for year in range(2018, 2025):  # Common year range
            year_key = f'score_{year}'
            csv_record[year_key] = historical.get(str(year), '')
        
        csv_data.append(csv_record)
    
    # Save CSV
    csv_filename = f"data/{filename_prefix}_{timestamp}.csv"
    if csv_data:
        fieldnames = csv_data[0].keys()
        with open(csv_filename, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(csv_data)
        logging.info(f"💾 Saved CSV: {csv_filename}")
    
    logging.info(f"🎉 Final results saved: {len(data)} records")
    return json_filename, csv_filename

def main():
    """Main execution function"""
    logging.info("🚀 Starting final comprehensive scraping")
    
    # Load necessary data
    codes_set = load_codes_csv()
    
    # For testing, load first 3 ramz links
    ramz_links = load_ramz_links(limit=3)
    
    if not ramz_links:
        logging.error("❌ No ramz links loaded")
        return
    
    scraper = None
    all_data = []
    
    try:
        scraper = FinalComprehensiveScraper(headless=False)  # Not headless for debugging
        
        for i, ramz_item in enumerate(ramz_links):
            ramz_code = ramz_item['ramz_code']
            ramz_link = ramz_item['ramz_link']
            
            logging.info(f"📋 Processing {i+1}/{len(ramz_links)}: {ramz_code}")
            
            data = scraper.scrape_ramz_data(ramz_code, ramz_link, codes_set)
            if data:
                all_data.append(data)
                logging.info(f"✅ Successfully scraped {ramz_code}")
            else:
                logging.warning(f"⚠️ Failed to scrape {ramz_code}")
            
            # Small delay between requests
            time.sleep(2)
    
    except Exception as e:
        logging.error(f"❌ Main execution error: {e}")
    
    finally:
        if scraper:
            scraper.close()
    
    # Save results
    if all_data:
        json_file, csv_file = save_results(all_data)
        logging.info(f"🎉 Scraping completed! {len(all_data)} records saved")
        print(f"\n📁 Files saved:")
        print(f"   JSON: {json_file}")
        print(f"   CSV: {csv_file}")
    else:
        logging.error("❌ No data collected")

if __name__ == "__main__":
    main()
