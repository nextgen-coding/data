#!/usr/bin/env python3
"""
Selenium-based comprehensive scraper for all ramz links with JavaScript execution
"""

import csv
import json
import time
import logging
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
        logging.FileHandler('selenium_scraping.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)

class SeleniumRamzScraper:
    def __init__(self, headless=True):
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
            self.driver.set_page_load_timeout(30)
            
            logging.info("✅ Chrome WebDriver initialized successfully")
            
        except Exception as e:
            logging.error(f"❌ Failed to setup WebDriver: {e}")
            raise

    def extract_field_value(self, arabic_label):
        """Extract field value by finding Arabic label in table"""
        try:
            # Find table rows
            rows = self.driver.find_elements(By.TAG_NAME, "tr")
            for row in rows:
                cells = row.find_elements(By.TAG_NAME, "td")
                if len(cells) >= 2:
                    label_text = cells[0].text.strip()
                    if arabic_label in label_text:
                        # Get text from the second cell
                        value_cell = cells[1]
                        # Try to get text from bold tags first
                        bold_elements = value_cell.find_elements(By.TAG_NAME, "b")
                        if bold_elements:
                            values = [b.text.strip() for b in bold_elements if b.text.strip()]
                            if values:
                                return ' '.join(values)
                        # Fallback to cell text
                        value = value_cell.text.strip()
                        return value if value else ''
            return ''
        except Exception as e:
            logging.debug(f"Error extracting field {arabic_label}: {e}")
            return ''

    def extract_historical_scores(self):
        """Extract historical scores from JavaScript/page content"""
        historical_scores = {}
        try:
            # Wait for any potential JavaScript to load
            time.sleep(2)
            
            # Execute JavaScript to get chart data if available
            try:
                # Check if Highcharts is loaded and has data
                chart_data = self.driver.execute_script("""
                    if (typeof Highcharts !== 'undefined' && Highcharts.charts.length > 0) {
                        var chart = Highcharts.charts[0];
                        if (chart && chart.series && chart.series.length > 0) {
                            return chart.series[0].data.map(function(point) {
                                return {year: point.category || point.name, score: point.y};
                            });
                        }
                    }
                    return null;
                """)
                
                if chart_data:
                    for point in chart_data:
                        if point and 'year' in point and 'score' in point:
                            year_str = str(point['year'])
                            if year_str.isdigit() and 2011 <= int(year_str) <= 2024:
                                historical_scores[year_str] = point['score']
                    
                    logging.debug(f"Extracted {len(historical_scores)} historical scores from chart")
                    
            except Exception as e:
                logging.debug(f"Failed to extract chart data: {e}")
            
            # Also look for embedded data in page source
            if not historical_scores:
                page_source = self.driver.page_source
                score_matches = re.findall(r'(20\d{2})[^\d]*(\d+\.\d+)', page_source)
                for year, score in score_matches:
                    if 2011 <= int(year) <= 2024:
                        try:
                            historical_scores[year] = float(score)
                        except:
                            historical_scores[year] = score
                            
        except Exception as e:
            logging.debug(f"Error extracting historical scores: {e}")
        
        return historical_scores

    def scrape_single_ramz(self, ramz_info, codes_set):
        """Scrape detailed data from a single ramz link using Selenium"""
        
        ramz_code = str(ramz_info['ramz_code'])
        ramz_link = ramz_info['ramz_link']
        
        try:
            logging.info(f"Scraping {ramz_code}: {ramz_link}")
            
            # Load the page
            self.driver.get(ramz_link)
            
            # Wait for page to load
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, "table"))
            )
            
            # Additional wait for JavaScript to potentially modify content
            time.sleep(3)
            
            # Extract ramz_id from URL
            ramz_id_match = re.search(r'id=(\d+)', ramz_link)
            ramz_id = ramz_id_match.group(1) if ramz_id_match else ""
            
            # Calculate bac_id (first digit of ramz_id)
            bac_id = ramz_id[0] if ramz_id and len(ramz_id) > 0 else "1"
            
            # Initialize comprehensive data structure
            data = {
                'ramz_code': ramz_code,
                'bac_id': bac_id,
                'ramz_id': ramz_id,
                'ramz_link': ramz_link,
                
                # Basic university information
                'university': self.extract_field_value('الجامعة'),
                'governorate': self.extract_field_value('الولاية'),
                'institution': self.extract_field_value('المؤسسة'),
                'address': '',
                'phone': '',
                
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
                addr_match = re.search(r'العنوان\s*:\s*([^\n\r]+)', institution_text)
                if addr_match:
                    data['address'] = addr_match.group(1).strip()
                
                phone_match = re.search(r'الهاتف\s*:\s*([^\n\r]+)', institution_text)
                if phone_match:
                    data['phone'] = phone_match.group(1).strip()
            
            # Determine 7% benefit based on codes.csv
            last_three_digits = ramz_code[-3:] if len(ramz_code) >= 3 else ramz_code
            if last_three_digits in codes_set:
                data['seven_percent'] = 'لا'  # No benefit
            else:
                data['seven_percent'] = 'نعم'  # Has benefit
            
            logging.info(f"✅ Successfully scraped {ramz_code}")
            return data
            
        except Exception as e:
            logging.error(f"❌ Error scraping {ramz_code}: {e}")
            return None

    def scrape_multiple_ramz(self, ramz_links, codes_set, limit=None):
        """Scrape multiple ramz links"""
        
        if limit:
            ramz_links = ramz_links[:limit]
        
        results = []
        total = len(ramz_links)
        
        logging.info(f"🚀 Starting Selenium scraping of {total} ramz links...")
        
        for i, ramz_info in enumerate(ramz_links, 1):
            try:
                result = self.scrape_single_ramz(ramz_info, codes_set)
                if result:
                    results.append(result)
                
                if i % 10 == 0 or i == total:
                    success_rate = len(results) / i * 100
                    logging.info(f"Progress: {i}/{total} ({success_rate:.1f}% success)")
                
                # Small delay between requests
                time.sleep(1)
                
            except Exception as e:
                logging.error(f"Error processing ramz {ramz_info.get('ramz_code', 'unknown')}: {e}")
        
        logging.info(f"✅ Selenium scraping complete: {len(results)}/{total} successful ({len(results)/total*100:.1f}%)")
        return results

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

def load_ramz_links():
    """Load ramz links from CSV file"""
    ramz_links = []
    try:
        with open('ramz_links.csv', 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                ramz_links.append({
                    'ramz_code': row['ramz_code'],
                    'ramz_link': row['ramz_link']
                })
        logging.info(f"Loaded {len(ramz_links)} ramz links")
        return ramz_links
    except Exception as e:
        logging.error(f"Error loading ramz_links.csv: {e}")
        return []

def save_results(data, filename_prefix="tunisia_university_selenium"):
    """Save results in JSON and CSV formats"""
    
    if not data:
        logging.error("No data to save")
        return
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Save JSON
    json_file = f"{filename_prefix}_{timestamp}.json"
    with open(json_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    # Prepare CSV data (flatten historical scores)
    csv_data = []
    for record in data:
        flat_record = record.copy()
        
        # Convert historical_scores dict to individual year columns
        historical_scores = flat_record.pop('historical_scores', {})
        for year in range(2011, 2025):  # Years 2011-2024
            year_str = str(year)
            flat_record[f'score_{year}'] = historical_scores.get(year_str, '')
        
        csv_data.append(flat_record)
    
    # Save CSV
    csv_file = f"{filename_prefix}_{timestamp}.csv"
    if csv_data:
        fieldnames = list(csv_data[0].keys())
        with open(csv_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(csv_data)
    
    logging.info(f"📁 Files saved:")
    logging.info(f"   📄 JSON: {json_file}")
    logging.info(f"   📄 CSV: {csv_file}")
    
    return json_file, csv_file

def main():
    """Main execution function"""
    
    print("🇹🇳 TUNISIA UNIVERSITY SELENIUM SCRAPER")
    print("=" * 50)
    
    scraper = None
    try:
        # Step 1: Load codes for 7% determination
        print("📋 Step 1: Loading codes.csv...")
        codes_set = load_codes_csv()
        
        # Step 2: Load ramz links
        print("🔗 Step 2: Loading ramz links...")
        ramz_links = load_ramz_links()
        
        if not ramz_links:
            print("❌ No ramz links found. Check if ramz_links.csv exists.")
            return
        
        print(f"✅ Found {len(ramz_links)} ramz links to scrape")
        
        # Step 3: Ask user for processing mode
        choice = input(f"\nChoose processing mode:\n1. Test with 3 links\n2. Test with 25 links\n3. Process all {len(ramz_links)} links\nEnter choice (1-3): ")
        
        if choice == '1':
            selected_links = ramz_links[:3]
            print(f"🧪 Testing with {len(selected_links)} links...")
        elif choice == '2':
            selected_links = ramz_links[:25]
            print(f"🧪 Testing with {len(selected_links)} links...")
        else:
            selected_links = ramz_links
            print(f"🚀 Processing all {len(selected_links)} links...")
        
        # Step 4: Initialize Selenium scraper
        print(f"\n🌐 Step 3: Initializing Selenium scraper...")
        scraper = SeleniumRamzScraper(headless=True)
        
        # Step 5: Scrape the data
        print(f"\n⚡ Step 4: Scraping {len(selected_links)} ramz links...")
        start_time = time.time()
        results = scraper.scrape_multiple_ramz(selected_links, codes_set)
        end_time = time.time()
        
        if not results:
            print("❌ No data was successfully scraped")
            return
        
        # Step 6: Save results
        print(f"\n💾 Step 5: Saving {len(results)} records...")
        json_file, csv_file = save_results(results)
        
        print(f"\n🎉 SELENIUM SCRAPING COMPLETE!")
        print(f"   Successfully scraped: {len(results)}/{len(selected_links)} records ({len(results)/len(selected_links)*100:.1f}%)")
        print(f"   Total time: {end_time - start_time:.2f} seconds")
        print(f"   Average time per record: {(end_time - start_time)/len(selected_links):.2f} seconds")
        print(f"   Files saved: {json_file}, {csv_file}")
        
        # Show sample data
        if results:
            print(f"\n📋 Sample record (first one):")
            sample = results[0]
            important_fields = [
                'ramz_code', 'university', 'specialization_name', 
                'seven_percent', 'last_oriented_score_2024', 'bac_id'
            ]
            for field in important_fields:
                value = sample.get(field, 'N/A')
                print(f"   {field}: {value}")
            
            historical_count = len(sample.get('historical_scores', {}))
            print(f"   historical_scores: {historical_count} years of data")
    
    finally:
        if scraper:
            scraper.close()

if __name__ == "__main__":
    main()
