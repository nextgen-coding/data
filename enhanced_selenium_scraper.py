#!/usr/bin/env python3
"""
Enhanced Selenium scraper with better field extraction and debugging
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
        logging.FileHandler('enhanced_selenium.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)

class EnhancedSeleniumRamzScraper:
    def __init__(self, headless=False):  # Changed to False for debugging
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
            
            logging.info("✅ Enhanced Chrome WebDriver initialized successfully")
            
        except Exception as e:
            logging.error(f"❌ Failed to setup WebDriver: {e}")
            raise

    def save_debug_html(self, ramz_code, page_source):
        """Save HTML for debugging purposes"""
        with open(f'debug_selenium_{ramz_code}.html', 'w', encoding='utf-8') as f:
            f.write(page_source)

    def extract_field_value_enhanced(self, arabic_label, ramz_code=""):
        """Enhanced field extraction with multiple strategies"""
        try:
            # Strategy 1: Find by exact label match in table
            rows = self.driver.find_elements(By.TAG_NAME, "tr")
            for row in rows:
                cells = row.find_elements(By.TAG_NAME, "td")
                if len(cells) >= 2:
                    label_text = cells[0].text.strip()
                    if arabic_label in label_text:
                        # Get text from the second cell
                        value_cell = cells[1]
                        
                        # Try multiple extraction methods
                        # Method 1: Bold tags
                        bold_elements = value_cell.find_elements(By.TAG_NAME, "b")
                        if bold_elements:
                            values = []
                            for b in bold_elements:
                                text = b.text.strip()
                                if text and text not in ['العنوان :', 'الهاتف :']:
                                    values.append(text)
                            if values:
                                result = ' '.join(values)
                                logging.debug(f"  Found {arabic_label}: '{result}' (via bold tags)")
                                return result
                        
                        # Method 2: Direct cell text
                        value = value_cell.text.strip()
                        if value and value not in ['العنوان :   الهاتف :', 'العنوان : الهاتف :']:
                            logging.debug(f"  Found {arabic_label}: '{value}' (via cell text)")
                            return value
            
            # Strategy 2: Try with partial matches and variations
            variations = [
                arabic_label,
                arabic_label.replace(' :', ':'),
                arabic_label.replace(':', ' :'),
                arabic_label + ' :',
                arabic_label.replace(' ', '')
            ]
            
            for variation in variations:
                for row in rows:
                    cells = row.find_elements(By.TAG_NAME, "td")
                    if len(cells) >= 2:
                        label_text = cells[0].text.strip()
                        if variation in label_text or label_text in variation:
                            value_cell = cells[1]
                            bold_elements = value_cell.find_elements(By.TAG_NAME, "b")
                            if bold_elements:
                                values = [b.text.strip() for b in bold_elements if b.text.strip()]
                                if values:
                                    result = ' '.join(values)
                                    logging.debug(f"  Found {arabic_label}: '{result}' (via variation '{variation}')")
                                    return result
                            
                            value = value_cell.text.strip()
                            if value:
                                logging.debug(f"  Found {arabic_label}: '{value}' (via variation '{variation}')")
                                return value
            
            logging.debug(f"  Field {arabic_label} not found for {ramz_code}")
            return ''
            
        except Exception as e:
            logging.debug(f"Error extracting field {arabic_label}: {e}")
            return ''

    def extract_all_table_data(self, ramz_code):
        """Extract all table data for debugging"""
        try:
            table_data = {}
            rows = self.driver.find_elements(By.TAG_NAME, "tr")
            
            logging.info(f"🔍 Analyzing table structure for {ramz_code}:")
            logging.info(f"  Found {len(rows)} table rows")
            
            for i, row in enumerate(rows):
                cells = row.find_elements(By.TAG_NAME, "td")
                if len(cells) >= 2:
                    label = cells[0].text.strip()
                    value = cells[1].text.strip()
                    
                    # Also check for bold tags in value cell
                    bold_elements = cells[1].find_elements(By.TAG_NAME, "b")
                    bold_values = [b.text.strip() for b in bold_elements if b.text.strip()]
                    
                    table_data[f"row_{i}"] = {
                        'label': label,
                        'value': value,
                        'bold_values': bold_values
                    }
                    
                    logging.info(f"    Row {i}: '{label}' -> '{value}' (bold: {bold_values})")
            
            return table_data
            
        except Exception as e:
            logging.error(f"Error analyzing table for {ramz_code}: {e}")
            return {}

    def extract_historical_scores_enhanced(self, ramz_code):
        """Enhanced historical scores extraction"""
        historical_scores = {}
        try:
            # Wait for charts to load
            time.sleep(5)
            
            # Method 1: Try to extract from Highcharts
            try:
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
                        return {error: e.toString()};
                    }
                """)
                
                if chart_data and isinstance(chart_data, list):
                    for point in chart_data:
                        if point and 'year' in point and 'score' in point:
                            year_str = str(point['year'])
                            if year_str.isdigit() and 2011 <= int(year_str) <= 2024:
                                historical_scores[year_str] = point['score']
                    
                    logging.info(f"  📊 Extracted {len(historical_scores)} scores from Highcharts for {ramz_code}")
                    
                elif chart_data and isinstance(chart_data, dict) and 'error' in chart_data:
                    logging.debug(f"  ⚠️ Highcharts error for {ramz_code}: {chart_data['error']}")
                    
            except Exception as e:
                logging.debug(f"  ❌ Highcharts extraction failed for {ramz_code}: {e}")
            
            # Method 2: Extract from page source if Highcharts failed
            if not historical_scores:
                page_source = self.driver.page_source
                
                # Look for score patterns in various formats
                patterns = [
                    r'(20\d{2})[^\d]*(\d+\.\d+)',
                    r'(\d{4})[^\d]*(\d+\.\d+)',
                    r'year["\']?\s*:\s*["\']?(20\d{2})["\']?.*?score["\']?\s*:\s*["\']?(\d+\.?\d*)',
                    r'(20\d{2}).*?(\d{2,3}\.\d+)'
                ]
                
                for pattern in patterns:
                    matches = re.findall(pattern, page_source)
                    for year, score in matches:
                        if 2011 <= int(year) <= 2024:
                            try:
                                historical_scores[year] = float(score)
                            except:
                                historical_scores[year] = score
                
                if historical_scores:
                    logging.info(f"  📊 Extracted {len(historical_scores)} scores from page source for {ramz_code}")
                else:
                    logging.warning(f"  ⚠️ No historical scores found for {ramz_code}")
                    
        except Exception as e:
            logging.error(f"❌ Error extracting historical scores for {ramz_code}: {e}")
        
        return historical_scores

    def scrape_single_ramz_enhanced(self, ramz_info, codes_set):
        """Enhanced scraping of a single ramz link"""
        
        ramz_code = str(ramz_info['ramz_code'])
        ramz_link = ramz_info['ramz_link']
        
        try:
            logging.info(f"🔍 Enhanced scraping {ramz_code}: {ramz_link}")
            
            # Load the page
            self.driver.get(ramz_link)
            
            # Wait for page to load completely
            WebDriverWait(self.driver, 15).until(
                EC.presence_of_element_located((By.TAG_NAME, "table"))
            )
            
            # Additional wait for JavaScript to load data
            time.sleep(8)  # Increased wait time
            
            # Save debug HTML
            self.save_debug_html(ramz_code, self.driver.page_source)
            
            # Extract all table data for analysis
            table_data = self.extract_all_table_data(ramz_code)
            
            # Extract ramz_id from URL
            ramz_id_match = re.search(r'id=(\d+)', ramz_link)
            ramz_id = ramz_id_match.group(1) if ramz_id_match else ""
            
            # Calculate bac_id (first digit of ramz_id)
            bac_id = ramz_id[0] if ramz_id and len(ramz_id) > 0 else "1"
            
            # Enhanced field extraction
            data = {
                'ramz_code': ramz_code,
                'bac_id': bac_id,
                'ramz_id': ramz_id,
                'ramz_link': ramz_link,
                
                # Basic university information (enhanced extraction)
                'university': self.extract_field_value_enhanced('الجامعة', ramz_code),
                'governorate': self.extract_field_value_enhanced('الولاية', ramz_code),
                'institution': self.extract_field_value_enhanced('المؤسسة', ramz_code),
                'address': '',
                'phone': '',
                
                # Academic information (enhanced extraction)
                'specialization_name': self.extract_field_value_enhanced('الشعبة / الإجازة', ramz_code),
                'specialization_code_detailed': self.extract_field_value_enhanced('رمز الشعبة', ramz_code),
                'field_of_study': self.extract_field_value_enhanced('مجال التكوين', ramz_code),
                'specializations_detailed': self.extract_field_value_enhanced('التخصصات', ramz_code),
                'requirements': self.extract_field_value_enhanced('المقياس', ramz_code),
                'bac_type': self.extract_field_value_enhanced('نوع الباكالوريا', ramz_code),
                
                # Program details (enhanced extraction)
                'capacity_2025': self.extract_field_value_enhanced('طاقة الإستعاب', ramz_code),
                'requires_test': self.extract_field_value_enhanced('شعبة تتطلب إختبار', ramz_code),
                'geographical_distribution': self.extract_field_value_enhanced('التنفيل الجغرافي', ramz_code),
                'conditions': self.extract_field_value_enhanced('الشروط', ramz_code),
                'study_duration': self.extract_field_value_enhanced('مدة الدراسة', ramz_code),
                
                # Admission scores
                'last_oriented_score_2024': self.extract_field_value_enhanced('مجموع آخر موجه 2024', ramz_code),
                'historical_scores': self.extract_historical_scores_enhanced(ramz_code),
                
                # Debug information
                'table_analysis': table_data,
                
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
            
            # Log extraction summary
            non_empty_fields = sum(1 for k, v in data.items() 
                                 if k not in ['table_analysis', 'historical_scores', 'scraped_at'] 
                                 and v and str(v).strip() and v != '-')
            historical_count = len(data['historical_scores'])
            
            logging.info(f"✅ Enhanced extraction for {ramz_code}: {non_empty_fields} fields, {historical_count} historical scores")
            return data
            
        except Exception as e:
            logging.error(f"❌ Enhanced extraction failed for {ramz_code}: {e}")
            return None

    def close(self):
        """Close the WebDriver"""
        if self.driver:
            self.driver.quit()
            logging.info("🔒 Enhanced WebDriver closed")

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

def save_results(data, filename_prefix="tunisia_university_enhanced"):
    """Save results in JSON and CSV formats"""
    
    if not data:
        logging.error("No data to save")
        return
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Create clean data (remove debug info for main files)
    clean_data = []
    for record in data:
        clean_record = record.copy()
        clean_record.pop('table_analysis', None)  # Remove debug info
        clean_data.append(clean_record)
    
    # Save enhanced JSON (with debug info)
    debug_json_file = f"{filename_prefix}_debug_{timestamp}.json"
    with open(debug_json_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    # Save clean JSON
    json_file = f"{filename_prefix}_{timestamp}.json"
    with open(json_file, 'w', encoding='utf-8') as f:
        json.dump(clean_data, f, ensure_ascii=False, indent=2)
    
    # Prepare CSV data (flatten historical scores)
    csv_data = []
    for record in clean_data:
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
    
    logging.info(f"📁 Enhanced files saved:")
    logging.info(f"   📄 Clean JSON: {json_file}")
    logging.info(f"   📄 Debug JSON: {debug_json_file}")
    logging.info(f"   📄 CSV: {csv_file}")
    
    return json_file, csv_file

def main():
    """Main execution function for enhanced scraping"""
    
    print("🇹🇳 TUNISIA UNIVERSITY ENHANCED SELENIUM SCRAPER")
    print("=" * 60)
    
    scraper = None
    try:
        # Load dependencies
        print("📋 Loading codes.csv...")
        codes_set = load_codes_csv()
        
        print("🔗 Loading ramz links...")
        ramz_links = load_ramz_links()
        
        if not ramz_links:
            print("❌ No ramz links found. Check if ramz_links.csv exists.")
            return
        
        # Test with only 3 links as requested
        selected_links = ramz_links[:3]
        print(f"🧪 Testing enhanced extraction with {len(selected_links)} links...")
        
        # Initialize enhanced scraper
        print("🌐 Initializing enhanced Selenium scraper...")
        scraper = EnhancedSeleniumRamzScraper(headless=False)  # Visible for debugging
        
        # Scrape the data
        print(f"⚡ Enhanced scraping {len(selected_links)} ramz links...")
        results = []
        
        for i, ramz_info in enumerate(selected_links, 1):
            print(f"\n--- Processing {i}/{len(selected_links)}: {ramz_info['ramz_code']} ---")
            result = scraper.scrape_single_ramz_enhanced(ramz_info, codes_set)
            if result:
                results.append(result)
                
                # Show key extracted fields
                important_fields = ['university', 'specialization_name', 'requirements', 'bac_type']
                print(f"Key fields extracted:")
                for field in important_fields:
                    value = result.get(field, 'N/A')
                    status = "✅" if value and value.strip() else "❌"
                    print(f"  {status} {field}: {value}")
                
                historical_count = len(result.get('historical_scores', {}))
                print(f"  📊 Historical scores: {historical_count} years")
            
            time.sleep(2)  # Pause between requests
        
        if not results:
            print("❌ No data was successfully scraped")
            return
        
        # Save results
        print(f"\n💾 Saving {len(results)} enhanced records...")
        json_file, csv_file = save_results(results)
        
        print(f"\n🎉 ENHANCED SCRAPING COMPLETE!")
        print(f"   Successfully scraped: {len(results)}/{len(selected_links)} records")
        print(f"   Files saved: {json_file}, {csv_file}")
        print(f"   Debug HTML files: debug_selenium_*.html")
        
    finally:
        if scraper:
            scraper.close()

if __name__ == "__main__":
    main()
