#!/usr/bin/env python3
"""
Final Comprehensive Scraper with PHP Endpoint Discovery
Uses the discovered values.php endpoint for historical scores
"""

import requests
import json
import csv
import time
import pandas as pd
from bs4 import BeautifulSoup
import re
from datetime import datetime
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class TunisianUniversityScraperFinal:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'ar,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        })
        
        # Load codes for 7% bonus calculation
        self.non_bonus_codes = set()
        try:
            with open('codes.csv', 'r', encoding='utf-8') as f:
                reader = csv.reader(f)
                next(reader)  # Skip header
                for row in reader:
                    if row:
                        self.non_bonus_codes.add(row[0])
        except FileNotFoundError:
            logger.warning("codes.csv not found. 7% bonus calculation will be skipped.")
    
    def get_historical_scores_from_values_php(self, ramz_id):
        """
        Get historical scores using the discovered values.php endpoint
        This endpoint returns data in format: year/score/year/score/...
        """
        try:
            # First, visit the main page to set session
            main_url = f"https://guide-orientation.rnu.tn/ar/dynamique/filiere.php?id={ramz_id}"
            main_response = self.session.get(main_url, timeout=10)
            
            if main_response.status_code != 200:
                logger.error(f"Failed to load main page for {ramz_id}: {main_response.status_code}")
                return {}
            
            # Small delay to let session establish
            time.sleep(0.5)
            
            # Now get the values from values.php
            values_url = "https://guide-orientation.rnu.tn/ar/dynamique/values.php"
            values_response = self.session.get(values_url, timeout=10)
            
            if values_response.status_code != 200:
                logger.error(f"Failed to get values for {ramz_id}: {values_response.status_code}")
                return {}
            
            values_text = values_response.text.strip()
            logger.info(f"Values response for {ramz_id}: {values_text[:100]}...")
            
            if not values_text:
                logger.warning(f"Empty values response for {ramz_id}")
                return {}
            
            # Parse the year/score format: 2011/94.5/2012/96.725/...
            scores = {}
            parts = values_text.split('/')
            
            for i in range(0, len(parts)-1, 2):
                if i+1 < len(parts):
                    try:
                        year = parts[i].strip()
                        score = float(parts[i+1].strip())
                        scores[year] = score
                    except (ValueError, IndexError) as e:
                        logger.warning(f"Failed to parse year/score pair: {parts[i:i+2]} - {e}")
            
            logger.info(f"Extracted {len(scores)} historical scores for {ramz_id}")
            return scores
            
        except Exception as e:
            logger.error(f"Error getting historical scores for {ramz_id}: {e}")
            return {}
    
    def extract_specialization_data(self, ramz_id):
        """Extract comprehensive data for a single specialization using the main page"""
        
        try:
            url = f"https://guide-orientation.rnu.tn/ar/dynamique/filiere.php?id={ramz_id}"
            logger.info(f"Scraping: {url}")
            
            response = self.session.get(url, timeout=15)
            if response.status_code != 200:
                logger.error(f"Failed to fetch {url}: {response.status_code}")
                return None
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Extract basic information
            data = {
                'ramz_id': ramz_id,
                'ramz_link': url,
                'extraction_timestamp': datetime.now().isoformat(),
                'page_status': response.status_code
            }
            
            # Extract all <b> tag contents (these contain the key information)
            b_tags = soup.find_all('b')
            b_contents = [b.get_text().strip() for b in b_tags if b.get_text().strip()]
            
            logger.info(f"Found {len(b_contents)} filled <b> tags for {ramz_id}")
            
            # Map the <b> tag contents to fields based on their position and content
            if len(b_contents) >= 6:
                # Common pattern in the pages
                data['specialization_name'] = b_contents[0] if len(b_contents) > 0 else ''
                data['university_name'] = b_contents[1] if len(b_contents) > 1 else ''
                data['institution_name'] = b_contents[2] if len(b_contents) > 2 else ''
                data['degree_type'] = b_contents[3] if len(b_contents) > 3 else ''
                data['duration'] = b_contents[4] if len(b_contents) > 4 else ''
                data['specialization_field'] = b_contents[5] if len(b_contents) > 5 else ''
                
                # Additional fields if available
                if len(b_contents) > 6:
                    data['additional_info'] = ' | '.join(b_contents[6:])
                else:
                    data['additional_info'] = ''
            else:
                # If we have fewer fields, assign what we can
                data['specialization_name'] = b_contents[0] if len(b_contents) > 0 else ''
                data['university_name'] = b_contents[1] if len(b_contents) > 1 else ''
                data['institution_name'] = b_contents[2] if len(b_contents) > 2 else ''
                data['degree_type'] = b_contents[3] if len(b_contents) > 3 else ''
                data['duration'] = b_contents[4] if len(b_contents) > 4 else ''
                data['specialization_field'] = b_contents[5] if len(b_contents) > 5 else ''
                data['additional_info'] = ''
            
            # Get historical scores using the values.php endpoint
            historical_scores = self.get_historical_scores_from_values_php(ramz_id)
            
            # Add historical scores as individual columns
            for year in range(2011, 2025):
                year_str = str(year)
                data[f'score_{year}'] = historical_scores.get(year_str, '')
            
            # Calculate 7% geographical bonus
            specialization_code = ramz_id[-3:] if len(ramz_id) >= 3 else ramz_id
            data['has_7_percent_bonus'] = 'No' if specialization_code in self.non_bonus_codes else 'Yes'
            
            # Extract any additional text content
            page_text = soup.get_text()
            
            # Look for specific patterns
            bac_match = re.search(r'بكالوريا\s+([^\n]+)', page_text)
            data['bac_requirement'] = bac_match.group(1).strip() if bac_match else ''
            
            # Add raw data for debugging
            data['extracted_b_tags'] = b_contents
            data['total_b_tags_found'] = len(b_contents)
            
            logger.info(f"Successfully extracted data for {ramz_id}: {data['specialization_name']}")
            return data
            
        except Exception as e:
            logger.error(f"Error extracting data for {ramz_id}: {e}")
            return None
    
    def scrape_all_ramz_links(self, ramz_csv_file='ramz_links.csv'):
        """Scrape all ramz links from the CSV file"""
        
        try:
            df = pd.read_csv(ramz_csv_file)
            ramz_ids = df['ramz_id'].tolist()
            
            logger.info(f"Starting to scrape {len(ramz_ids)} ramz links")
            
            all_data = []
            failed_ids = []
            
            for i, ramz_id in enumerate(ramz_ids):
                logger.info(f"Processing {i+1}/{len(ramz_ids)}: {ramz_id}")
                
                data = self.extract_specialization_data(ramz_id)
                
                if data:
                    all_data.append(data)
                    logger.info(f"✅ Success: {ramz_id}")
                else:
                    failed_ids.append(ramz_id)
                    logger.error(f"❌ Failed: {ramz_id}")
                
                # Add delay to be respectful
                time.sleep(1)
                
                # Save progress every 50 entries
                if (i + 1) % 50 == 0:
                    self.save_data(all_data, f"progress_backup_{i+1}")
                    logger.info(f"💾 Progress saved at {i+1} entries")
            
            logger.info(f"Scraping complete! Successfully scraped: {len(all_data)}, Failed: {len(failed_ids)}")
            
            if failed_ids:
                logger.info(f"Failed IDs: {failed_ids}")
            
            return all_data, failed_ids
            
        except Exception as e:
            logger.error(f"Error in scrape_all_ramz_links: {e}")
            return [], []
    
    def save_data(self, data, filename_suffix=""):
        """Save scraped data to JSON and CSV files"""
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Save JSON
        json_filename = f"tunisia_university_final{filename_suffix}_{timestamp}.json"
        with open(json_filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        # Save CSV
        if data:
            csv_filename = f"tunisia_university_final{filename_suffix}_{timestamp}.csv"
            df = pd.DataFrame(data)
            df.to_csv(csv_filename, index=False, encoding='utf-8')
            
            logger.info(f"💾 Data saved to {json_filename} and {csv_filename}")
            logger.info(f"📊 Total records: {len(data)}")
            
            # Print summary statistics
            filled_specializations = sum(1 for d in data if d.get('specialization_name'))
            filled_universities = sum(1 for d in data if d.get('university_name'))
            filled_scores_2024 = sum(1 for d in data if d.get('score_2024'))
            
            logger.info(f"📈 Data quality:")
            logger.info(f"  Specializations with names: {filled_specializations}/{len(data)} ({filled_specializations/len(data)*100:.1f}%)")
            logger.info(f"  Entries with universities: {filled_universities}/{len(data)} ({filled_universities/len(data)*100:.1f}%)")
            logger.info(f"  Entries with 2024 scores: {filled_scores_2024}/{len(data)} ({filled_scores_2024/len(data)*100:.1f}%)")
        
        return json_filename, csv_filename

def main():
    """Main function to run the final comprehensive scraper"""
    
    print("🎯 FINAL COMPREHENSIVE TUNISIAN UNIVERSITY SCRAPER")
    print("=" * 60)
    print("Using discovered values.php endpoint for historical scores")
    print("=" * 60)
    
    scraper = TunisianUniversityScraperFinal()
    
    # Test with a few IDs first
    test_mode = input("Run in test mode with 5 entries? (y/n): ").lower() == 'y'
    
    if test_mode:
        print("🧪 Test mode: scraping first 5 entries...")
        test_ids = ["110101", "220518", "310101", "410201", "510301"]
        
        all_data = []
        for ramz_id in test_ids:
            data = scraper.extract_specialization_data(ramz_id)
            if data:
                all_data.append(data)
        
        if all_data:
            json_file, csv_file = scraper.save_data(all_data, "_test")
            print(f"✅ Test complete! Check {csv_file} for results")
    else:
        print("🚀 Full mode: scraping all ramz links...")
        all_data, failed_ids = scraper.scrape_all_ramz_links()
        
        if all_data:
            json_file, csv_file = scraper.save_data(all_data)
            print(f"✅ Scraping complete! Check {csv_file} for results")
            
            if failed_ids:
                print(f"⚠️  {len(failed_ids)} entries failed. You may want to retry these manually.")

if __name__ == "__main__":
    main()
