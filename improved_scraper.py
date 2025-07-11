#!/usr/bin/env python3
"""
Improved comprehensive scraper based on discovering that data is in page source
"""

import requests
import json
import csv
import pandas as pd
from bs4 import BeautifulSoup
import re
from datetime import datetime
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

def extract_comprehensive_data(ramz_code, ramz_link, codes_list):
    """Extract comprehensive data from a ramz page using improved parsing"""
    
    try:
        session = requests.Session()
        session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'ar,en;q=0.9',
        })
        
        response = session.get(ramz_link, timeout=10)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Extract ramz_id from URL for bac_id calculation
        ramz_id_match = re.search(r'id=(\d+)', ramz_link)
        ramz_id = ramz_id_match.group(1) if ramz_id_match else ""
        
        # Calculate bac_id (first digit of ramz_id)
        bac_id = ramz_id[0] if ramz_id else "1"
        
        # Initialize data structure
        data = {
            'ramz_code': ramz_code,
            'bac_id': bac_id,
            'ramz_id': ramz_id,
            'ramz_link': ramz_link,
            'university': '',
            'governorate': '',
            'institution': '',
            'address': '',
            'phone': '',
            'specialization_name': '',
            'specialization_code_detailed': '',
            'field_of_study': '',
            'specializations_detailed': '',
            'requirements': '',
            'bac_type': '',
            'capacity_2025': '',
            'requires_test': '',
            'geographical_distribution': '',
            'conditions': '',
            'study_duration': '',
            'last_oriented_score_2024': '',
            'historical_scores': {},
            'scraped_at': datetime.now().isoformat()
        }
        
        # Parse the main table with improved logic
        table = soup.find('table', class_='table')
        if table:
            rows = table.find_all('tr')
            for row in rows:
                cells = row.find_all('td')
                if len(cells) >= 2:
                    label = cells[0].get_text().strip()
                    
                    # Get the value from the second cell, but handle nested structure
                    value_cell = cells[1]
                    
                    # For nested rows (like the specializations_detailed), get all text
                    nested_rows = value_cell.find_all('tr')
                    if nested_rows:
                        # This is the nested structure with multiple fields
                        nested_data = {}
                        for nested_row in nested_rows:
                            nested_cells = nested_row.find_all('td')
                            if len(nested_cells) >= 2:
                                nested_label = nested_cells[0].get_text().strip()
                                nested_value = nested_cells[1].get_text().strip()
                                
                                # Extract specific nested fields
                                if 'المقياس' in nested_label:
                                    data['requirements'] = nested_value
                                elif 'نوع الباكالوريا' in nested_label:
                                    data['bac_type'] = nested_value
                                elif 'طاقة الإستعاب' in nested_label:
                                    data['capacity_2025'] = nested_value
                                elif 'شعبة تتطلب إختبار' in nested_label:
                                    data['requires_test'] = nested_value
                                elif 'التنفيل الجغرافي' in nested_label:
                                    data['geographical_distribution'] = nested_value
                                elif 'الشروط' in nested_label:
                                    data['conditions'] = nested_value
                                elif 'مدة الدراسة' in nested_label:
                                    data['study_duration'] = nested_value
                                elif 'مجموع آخر موجه 2024' in nested_label:
                                    data['last_oriented_score_2024'] = nested_value
                    else:
                        # Regular field
                        value = value_cell.get_text().strip()
                        
                        # Extract data based on Arabic labels
                        if 'الجامعة' in label:
                            data['university'] = value
                        elif 'الولاية' in label:
                            data['governorate'] = value
                        elif 'المؤسسة' in label:
                            data['institution'] = value
                            # Extract address and phone from institution cell
                            full_text = value_cell.get_text()
                            addr_match = re.search(r'العنوان\s*:\s*([^\n\r]+)', full_text)
                            if addr_match:
                                data['address'] = addr_match.group(1).strip()
                            phone_match = re.search(r'الهاتف\s*:\s*([^\n\r]+)', full_text)
                            if phone_match:
                                data['phone'] = phone_match.group(1).strip()
                        elif 'مجال التكوين' in label:
                            data['field_of_study'] = value
                        elif 'رمز الشعبة' in label and 'الإجازة' in label:
                            data['specialization_code_detailed'] = value
                        elif 'الشعبة / الإجازة' in label and 'رمز' not in label:
                            data['specialization_name'] = value
                        elif 'التخصصات' in label:
                            data['specializations_detailed'] = value
        
        # Extract historical scores from page source using improved patterns
        page_content = response.text
        
        # Look for JavaScript data patterns for historical scores
        score_patterns = [
            r'data\s*:\s*\[(.*?)\]',  # Chart data array
            r'series\s*:\s*\[\s*{\s*[^}]*data\s*:\s*\[(.*?)\]',  # Highcharts series data
            r'(20\d{2})[^\d]*(\d{2,3}(?:\.\d+)?)',  # Year followed by score
        ]
        
        for pattern in score_patterns:
            matches = re.findall(pattern, page_content, re.DOTALL | re.IGNORECASE)
            for match in matches:
                if isinstance(match, tuple) and len(match) == 2:
                    # Year-score pair
                    year, score = match
                    try:
                        if float(score) > 10:  # Likely a real score
                            data['historical_scores'][year] = float(score)
                    except ValueError:
                        pass
                else:
                    # Try to parse as data array
                    try:
                        # Look for number patterns in the match
                        numbers = re.findall(r'\d{2,3}(?:\.\d+)?', str(match))
                        if len(numbers) >= 2:
                            # Assume these are historical scores
                            for i, num in enumerate(numbers):
                                year = 2024 - len(numbers) + i + 1
                                if year >= 2011:
                                    data['historical_scores'][str(year)] = float(num)
                    except:
                        pass
        
        # Determine 7% benefit based on codes.csv
        ramz_code_str = str(ramz_code)
        last_three_digits = ramz_code_str[-3:] if len(ramz_code_str) >= 3 else ramz_code_str
        if last_three_digits in codes_list:
            data['seven_percent'] = 'لا'  # No benefit
        else:
            data['seven_percent'] = 'نعم'  # Has benefit
        
        return data
        
    except Exception as e:
        print(f"❌ Error extracting data for {ramz_code}: {e}")
        return None

def load_codes_csv():
    """Load codes.csv to determine which specializations don't get 7% bonus"""
    try:
        df = pd.read_csv('codes.csv')
        codes = set(df['الرمز'].dropna().astype(str).tolist())
        print(f"Loaded {len(codes)} codes that don't benefit from 7% bonus")
        return codes
    except Exception as e:
        print(f"Error loading codes.csv: {e}")
        return set()

def load_ramz_links():
    """Load ramz links from CSV"""
    try:
        df = pd.read_csv('ramz_links.csv')
        ramz_links = [(row['ramz_code'], row['ramz_link']) for _, row in df.iterrows()]
        print(f"Loaded {len(ramz_links)} ramz links")
        return ramz_links
    except Exception as e:
        print(f"Error loading ramz_links.csv: {e}")
        return []

def process_ramz_links_parallel(ramz_links, codes_list, max_workers=15):
    """Process ramz links in parallel with improved extraction"""
    
    results = []
    
    def process_single_ramz(ramz_info):
        ramz_code, ramz_link = ramz_info
        time.sleep(0.3)  # Rate limiting
        return extract_comprehensive_data(ramz_code, ramz_link, codes_list)
    
    print(f"🚀 Starting improved parallel processing of {len(ramz_links)} ramz links...")
    
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        # Submit all tasks
        future_to_ramz = {
            executor.submit(process_single_ramz, ramz_info): ramz_info 
            for ramz_info in ramz_links
        }
        
        # Process completed tasks
        for i, future in enumerate(as_completed(future_to_ramz), 1):
            ramz_info = future_to_ramz[future]
            try:
                result = future.result()
                if result:
                    results.append(result)
                
                if i % 25 == 0:
                    print(f"Progress: {i}/{len(ramz_links)} ({len(results)} successful)")
                    
            except Exception as e:
                ramz_code = ramz_info[0]
                print(f"Error processing {ramz_code}: {e}")
    
    print(f"✅ Improved processing complete: {len(results)}/{len(ramz_links)} successful")
    return results

def save_comprehensive_data(data, prefix="tunisia_university_improved"):
    """Save data in both JSON and CSV formats"""
    
    if not data:
        print("❌ No data to save")
        return
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Save JSON
    json_file = f"{prefix}_{timestamp}.json"
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
    csv_file = f"{prefix}_{timestamp}.csv"
    if csv_data:
        df = pd.DataFrame(csv_data)
        df.to_csv(csv_file, index=False, encoding='utf-8')
    
    print(f"\n📁 Files saved:")
    print(f"   📄 JSON: {json_file}")
    print(f"   📄 CSV: {csv_file}")
    
    # Display summary
    print(f"\n📊 Dataset Summary:")
    print(f"   Total records: {len(data)}")
    
    # Field completeness analysis
    field_stats = {}
    for field in ['university', 'specialization_name', 'requirements', 'historical_scores']:
        complete_count = sum(1 for record in data if record.get(field))
        field_stats[field] = (complete_count, len(data))
    
    print(f"\n📈 Field Completeness:")
    for field, (complete, total) in field_stats.items():
        percentage = (complete / total) * 100 if total > 0 else 0
        print(f"   {field}: {complete}/{total} ({percentage:.1f}%)")
    
    # Count 7% distribution
    seven_percent_counts = {}
    for record in data:
        value = record.get('seven_percent', 'Unknown')
        seven_percent_counts[value] = seven_percent_counts.get(value, 0) + 1
    
    print(f"\n🎯 7% Geographic Bonus Distribution:")
    for value, count in seven_percent_counts.items():
        print(f"   {value}: {count} records")
    
    return json_file, csv_file

def main():
    """Main execution function"""
    
    print("🇹🇳 IMPROVED TUNISIA UNIVERSITY DATA SCRAPER")
    print("=" * 60)
    print("Enhanced extraction with better field parsing and historical scores")
    
    # Load dependencies
    print("\n📋 Loading dependencies...")
    codes_list = load_codes_csv()
    ramz_links = load_ramz_links()
    
    if not ramz_links:
        print("❌ No ramz links found")
        return
    
    # Ask user for processing mode
    print(f"\n🎯 Found {len(ramz_links)} ramz links to process")
    
    choice = input("Choose processing mode:\n1. Test with 5 links\n2. Test with 50 links\n3. Process all links\nEnter choice (1-3): ")
    
    if choice == '1':
        test_links = ramz_links[:5]
        print(f"🧪 Testing with {len(test_links)} links...")
    elif choice == '2':
        test_links = ramz_links[:50]
        print(f"🧪 Testing with {len(test_links)} links...")
    else:
        test_links = ramz_links
        print(f"🚀 Processing all {len(test_links)} links...")
    
    # Process the links
    print(f"\n⚡ Processing {len(test_links)} ramz links with improved extraction...")
    results = process_ramz_links_parallel(test_links, codes_list)
    
    if not results:
        print("❌ No data was successfully extracted")
        return
    
    # Save results
    print(f"\n💾 Saving {len(results)} records...")
    json_file, csv_file = save_comprehensive_data(results)
    
    print(f"\n🎉 IMPROVED SCRAPING COMPLETE!")
    print(f"   Successfully extracted {len(results)} comprehensive records")
    print(f"   Enhanced field parsing and historical score extraction")
    
    # Show sample data
    if results:
        print(f"\n📋 Sample record (first one):")
        sample = results[0]
        important_fields = [
            'ramz_code', 'university', 'specialization_name', 'requires_test',
            'geographical_distribution', 'seven_percent', 'last_oriented_score_2024'
        ]
        for field in important_fields:
            value = sample.get(field, 'N/A')
            print(f"   {field}: {value}")
        
        historical_count = len(sample.get('historical_scores', {}))
        print(f"   historical_scores: {historical_count} years of data")

if __name__ == "__main__":
    main()
