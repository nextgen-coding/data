#!/usr/bin/env python3
"""
Comprehensive scraper to extract full data from all ramz links
"""

import csv
import json
import requests
from bs4 import BeautifulSoup
import re
from datetime import datetime
import time
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
import os

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('scraping.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)

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

def extract_field_value(soup, arabic_label):
    """Extract field value by finding Arabic label in table"""
    try:
        # Find all table rows
        rows = soup.find_all('tr')
        for row in rows:
            cells = row.find_all('td')
            if len(cells) >= 2:
                label_text = cells[0].get_text().strip()
                if arabic_label in label_text:
                    value_cell = cells[1]
                    # Get text from bold tags first, then fallback to cell text
                    bold_tags = value_cell.find_all('b')
                    if bold_tags:
                        values = [b.get_text().strip() for b in bold_tags if b.get_text().strip()]
                        if values:
                            return ' '.join(values)
                    # Fallback to cell text
                    value = value_cell.get_text().strip()
                    return value if value else ''
        return ''
    except Exception as e:
        logging.debug(f"Error extracting field {arabic_label}: {e}")
        return ''

def extract_historical_scores(soup):
    """Extract historical scores from JavaScript or page content"""
    historical_scores = {}
    try:
        # Look for script tags with score data
        scripts = soup.find_all('script')
        for script in scripts:
            if script.string:
                script_content = script.string
                # Look for year and score patterns
                year_score_patterns = [
                    r'(20\d{2})[^\d]*(\d+(?:\.\d+)?)',  # Year followed by score
                    r'(\d{4})[^\d]*(\d+\.\d+)',        # 4-digit year with decimal score
                ]
                
                for pattern in year_score_patterns:
                    matches = re.findall(pattern, script_content)
                    for year, score in matches:
                        if 2011 <= int(year) <= 2024 and len(score) >= 2:
                            try:
                                historical_scores[year] = float(score)
                            except:
                                historical_scores[year] = score
        
        # Also look in page text for historical data
        page_text = soup.get_text()
        score_matches = re.findall(r'(20\d{2})[^\d]*(\d+\.\d+)', page_text)
        for year, score in score_matches:
            if 2011 <= int(year) <= 2024:
                try:
                    historical_scores[year] = float(score)
                except:
                    historical_scores[year] = score
                    
    except Exception as e:
        logging.debug(f"Error extracting historical scores: {e}")
    
    return historical_scores

def scrape_single_ramz(ramz_info, codes_set):
    """Scrape detailed data from a single ramz link"""
    
    ramz_code = ramz_info['ramz_code']
    ramz_link = ramz_info['ramz_link']
    
    try:
        logging.info(f"Scraping {ramz_code}: {ramz_link}")
        
        # Make request with proper headers
        session = requests.Session()
        session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'ar,en;q=0.9',
            'Connection': 'keep-alive',
        })
        
        response = session.get(ramz_link, timeout=15)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Extract ramz_id from URL for bac_id calculation
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
            'university': extract_field_value(soup, 'الجامعة'),
            'governorate': extract_field_value(soup, 'الولاية'),
            'institution': extract_field_value(soup, 'المؤسسة'),
            'address': '',
            'phone': '',
            
            # Academic information
            'specialization_name': extract_field_value(soup, 'الشعبة / الإجازة'),
            'specialization_code_detailed': extract_field_value(soup, 'رمز الشعبة'),
            'field_of_study': extract_field_value(soup, 'مجال التكوين'),
            'specializations_detailed': extract_field_value(soup, 'التخصصات'),
            'requirements': extract_field_value(soup, 'المقياس'),
            'bac_type': extract_field_value(soup, 'نوع الباكالوريا'),
            
            # Program details
            'capacity_2025': extract_field_value(soup, 'طاقة الإستعاب'),
            'requires_test': extract_field_value(soup, 'شعبة تتطلب إختبار'),
            'geographical_distribution': extract_field_value(soup, 'التنفيل الجغرافي'),
            'conditions': extract_field_value(soup, 'الشروط'),
            'study_duration': extract_field_value(soup, 'مدة الدراسة'),
            
            # Admission scores
            'last_oriented_score_2024': extract_field_value(soup, 'مجموع آخر موجه 2024'),
            'historical_scores': extract_historical_scores(soup),
            
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

def scrape_all_parallel(ramz_links, codes_set, max_workers=20):
    """Scrape all ramz links in parallel"""
    
    results = []
    total = len(ramz_links)
    
    def scrape_with_delay(ramz_info):
        time.sleep(0.5)  # Rate limiting
        return scrape_single_ramz(ramz_info, codes_set)
    
    logging.info(f"🚀 Starting parallel scraping of {total} ramz links with {max_workers} workers...")
    
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        # Submit all tasks
        future_to_ramz = {
            executor.submit(scrape_with_delay, ramz_info): ramz_info 
            for ramz_info in ramz_links
        }
        
        # Process completed tasks
        completed = 0
        for future in as_completed(future_to_ramz):
            ramz_info = future_to_ramz[future]
            completed += 1
            
            try:
                result = future.result()
                if result:
                    results.append(result)
                
                if completed % 25 == 0 or completed == total:
                    success_rate = len(results) / completed * 100
                    logging.info(f"Progress: {completed}/{total} ({success_rate:.1f}% success)")
                    
            except Exception as e:
                logging.error(f"Error processing {ramz_info['ramz_code']}: {e}")
    
    logging.info(f"✅ Parallel scraping complete: {len(results)}/{total} successful ({len(results)/total*100:.1f}%)")
    return results

def save_results(data, filename_prefix="tunisia_university_data"):
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
    
    # Display summary
    logging.info(f"📊 Dataset Summary:")
    logging.info(f"   Total records: {len(data)}")
    
    # Count 7% distribution
    seven_percent_counts = {}
    for record in data:
        value = record.get('seven_percent', 'Unknown')
        seven_percent_counts[value] = seven_percent_counts.get(value, 0) + 1
    
    logging.info(f"   7% Geographic Bonus Distribution:")
    for value, count in seven_percent_counts.items():
        logging.info(f"      {value}: {count} records")
    
    # Count field completeness
    field_completeness = {}
    important_fields = ['university', 'specialization_name', 'last_oriented_score_2024', 'historical_scores']
    for field in important_fields:
        complete_count = sum(1 for record in data if record.get(field) and record.get(field) != '')
        field_completeness[field] = (complete_count, len(data), complete_count/len(data)*100)
    
    logging.info(f"   Field Completeness:")
    for field, (complete, total, percentage) in field_completeness.items():
        logging.info(f"      {field}: {complete}/{total} ({percentage:.1f}%)")
    
    return json_file, csv_file

def main():
    """Main execution function"""
    
    print("🇹🇳 TUNISIA UNIVERSITY COMPREHENSIVE DATA SCRAPER")
    print("=" * 60)
    
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
    choice = input(f"\nChoose processing mode:\n1. Test with 5 links\n2. Test with 50 links\n3. Process all {len(ramz_links)} links\nEnter choice (1-3): ")
    
    if choice == '1':
        selected_links = ramz_links[:5]
        print(f"🧪 Testing with {len(selected_links)} links...")
    elif choice == '2':
        selected_links = ramz_links[:50]
        print(f"🧪 Testing with {len(selected_links)} links...")
    else:
        selected_links = ramz_links
        print(f"🚀 Processing all {len(selected_links)} links...")
    
    # Step 4: Scrape the data
    print(f"\n⚡ Step 3: Scraping {len(selected_links)} ramz links...")
    start_time = time.time()
    results = scrape_all_parallel(selected_links, codes_set)
    end_time = time.time()
    
    if not results:
        print("❌ No data was successfully scraped")
        return
    
    # Step 5: Save results
    print(f"\n💾 Step 4: Saving {len(results)} records...")
    json_file, csv_file = save_results(results)
    
    print(f"\n🎉 SCRAPING COMPLETE!")
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

if __name__ == "__main__":
    main()
