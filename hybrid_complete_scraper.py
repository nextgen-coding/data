#!/usr/bin/env python3
"""
Hybrid Complete Scraper: Combines dropdown workflow + individual ramz page scraping
Strategy:
1. First: Extract all ramz codes from dropdown combinations (fast bulk extraction)
2. Second: Visit individual ramz pages to populate missing fields (detailed extraction)
"""

import asyncio
import json
import csv
from playwright.async_api import async_playwright
from datetime import datetime
import re
import concurrent.futures
from typing import List, Dict

class HybridTunisiaUniversityScraper:
    def __init__(self):
        self.all_ramz_codes = set()
        self.bulk_data = []
        self.detailed_data = {}
        self.final_data = []
        
    async def phase1_bulk_extraction(self):
        """Phase 1: Fast bulk extraction of all ramz codes using dropdown workflow"""
        print("🚀 PHASE 1: BULK RAMZ CODE EXTRACTION")
        print("=" * 50)
        
        async with async_playwright() as p:
            browser = await p.chromium.launch(
                headless=True,  # Fast headless extraction
                args=['--disable-blink-features=AutomationControlled']
            )
            
            context = await browser.new_context(
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36'
            )
            
            page = await context.new_page()
            
            try:
                await page.goto('https://guide-orientation.rnu.tn/index.php', wait_until='networkidle')
                await page.wait_for_timeout(2000)
                
                # Get all bac types
                bac_dropdown = await page.query_selector('select[name="fBac"]')
                bac_options = await bac_dropdown.query_selector_all('option')
                
                bac_types = []
                for option in bac_options:
                    value = await option.get_attribute('value')
                    text = await option.inner_text()
                    if value and value != '' and value != '0':
                        bac_types.append({'value': value, 'text': text.strip()})
                
                print(f"📋 Found {len(bac_types)} bac types")
                
                # Extract all combinations
                for bac_idx, bac_type in enumerate(bac_types, 1):
                    print(f"\n🎯 Processing bac type {bac_idx}/{len(bac_types)}: {bac_type['text']}")
                    
                    await page.goto('https://guide-orientation.rnu.tn/index.php', wait_until='networkidle')
                    await page.wait_for_timeout(1000)
                    
                    # Select bac type
                    bac_dropdown = await page.query_selector('select[name="fBac"]')
                    await bac_dropdown.select_option(bac_type['value'])
                    await page.wait_for_timeout(2000)
                    
                    # Get universities for this bac type
                    univ_dropdown = await page.query_selector('select[name="fUniv"]')
                    univ_options = await univ_dropdown.query_selector_all('option')
                    
                    universities = []
                    for option in univ_options:
                        value = await option.get_attribute('value')
                        text = await option.inner_text()
                        if value and value != '0':
                            universities.append({'value': value, 'text': text.strip()})
                    
                    # Process each university
                    for univ in universities[:5]:  # Limit to first 5 universities for speed
                        print(f"  📚 University: {univ['text']}")
                        
                        await page.goto('https://guide-orientation.rnu.tn/index.php', wait_until='networkidle')
                        await page.wait_for_timeout(1000)
                        
                        # Re-select bac and university
                        bac_dropdown = await page.query_selector('select[name="fBac"]')
                        await bac_dropdown.select_option(bac_type['value'])
                        await page.wait_for_timeout(1500)
                        
                        univ_dropdown = await page.query_selector('select[name="fUniv"]')
                        await univ_dropdown.select_option(univ['value'])
                        await page.wait_for_timeout(1500)
                        
                        # Submit search
                        submit_button = await page.query_selector('input[name="submit"]')
                        await submit_button.click()
                        await page.wait_for_timeout(3000)
                        
                        # Set pagination to 100
                        await self.set_pagination_to_100(page)
                        
                        # Extract table data
                        table_data = await self.extract_bulk_table_data(page, bac_type, univ)
                        
                        if table_data:
                            self.bulk_data.extend(table_data)
                            for record in table_data:
                                self.all_ramz_codes.add(record['ramz_id'])
                            print(f"    ✅ Extracted {len(table_data)} records")
                        
                        # Small delay between requests
                        await asyncio.sleep(0.5)
                
                await browser.close()
                
                print(f"\n🎉 PHASE 1 COMPLETE!")
                print(f"📊 Total ramz codes found: {len(self.all_ramz_codes)}")
                print(f"📊 Total bulk records: {len(self.bulk_data)}")
                
                # Save bulk data
                with open('phase1_bulk_data.json', 'w', encoding='utf-8') as f:
                    json.dump(self.bulk_data, f, ensure_ascii=False, indent=2)
                
                return list(self.all_ramz_codes)
                
            except Exception as e:
                print(f"❌ Error in Phase 1: {e}")
                await browser.close()
                return []
    
    async def set_pagination_to_100(self, page):
        """Set pagination to show 100 entries"""
        try:
            # Look for pagination dropdown
            pagination_selectors = [
                'select[name="table3_length"]',
                'select[name*="length"]',
                '.dataTables_length select',
                'select:has(option[value="100"])'
            ]
            
            for selector in pagination_selectors:
                try:
                    pagination_dropdown = await page.query_selector(selector)
                    if pagination_dropdown:
                        await pagination_dropdown.select_option('100')
                        await page.wait_for_timeout(2000)
                        print(f"    ✅ Set pagination to 100 entries")
                        return True
                except:
                    continue
            
            return False
        except Exception as e:
            print(f"    ⚠️ Could not set pagination: {e}")
            return False
    
    async def extract_bulk_table_data(self, page, bac_type, university):
        """Extract data from results table (bulk extraction)"""
        try:
            # Find the results table
            table = await page.query_selector('table#table3')
            if not table:
                table = await page.query_selector('table')
            
            if not table:
                return []
            
            rows = await table.query_selector_all('tbody tr')
            if not rows:
                rows = await table.query_selector_all('tr')[1:]  # Skip header
            
            results = []
            
            for row in rows:
                try:
                    cells = await row.query_selector_all('td')
                    if len(cells) >= 6:
                        # Extract basic data
                        ramz_text = await cells[0].inner_text()
                        specialization = await cells[1].inner_text()
                        university_name = await cells[2].inner_text()
                        institution = await cells[3].inner_text()
                        location = await cells[4].inner_text()
                        criteria = await cells[5].inner_text()
                        
                        # Extract ramz code
                        ramz_match = re.search(r'(\d{5})', ramz_text)
                        if ramz_match:
                            ramz_code = ramz_match.group(1)
                            ramz_id = bac_type['value'] + ramz_code
                            ramz_link = f"https://guide-orientation.rnu.tn/ar/dynamique/filiere.php?id={ramz_id}"
                            
                            record = {
                                'ramz_code': ramz_code,
                                'ramz_id': ramz_id,
                                'ramz_link': ramz_link,
                                'bac_type_id': bac_type['value'],
                                'bac_type_name': bac_type['text'],
                                'university_id': university['value'],
                                'university_name': university['text'],
                                'table_specialization': specialization.strip(),
                                'table_university': university_name.strip(),
                                'table_institution': institution.strip(),
                                'table_location': location.strip(),
                                'table_criteria': criteria.strip(),
                                'extracted_at': datetime.now().isoformat(),
                                'extraction_phase': 'bulk'
                            }
                            
                            results.append(record)
                
                except Exception as e:
                    continue
            
            return results
            
        except Exception as e:
            print(f"    ❌ Error extracting table: {e}")
            return []
    
    async def phase2_detailed_extraction(self, ramz_codes: List[str]):
        """Phase 2: Detailed extraction from individual ramz pages using concurrency"""
        print(f"\n🔍 PHASE 2: DETAILED RAMZ PAGE EXTRACTION")
        print("=" * 50)
        print(f"📊 Processing {len(ramz_codes)} ramz codes with concurrency")
        
        # Process in batches to avoid overwhelming the server
        batch_size = 10
        all_detailed_data = {}
        
        for i in range(0, len(ramz_codes), batch_size):
            batch = ramz_codes[i:i + batch_size]
            print(f"\n🎯 Processing batch {i//batch_size + 1}/{(len(ramz_codes) + batch_size - 1)//batch_size}")
            print(f"   Ramz codes: {batch}")
            
            # Process batch concurrently
            tasks = []
            for ramz_id in batch:
                task = self.extract_single_ramz_detail(ramz_id)
                tasks.append(task)
            
            batch_results = await asyncio.gather(*tasks, return_exceptions=True)
            
            for ramz_id, result in zip(batch, batch_results):
                if isinstance(result, dict):
                    all_detailed_data[ramz_id] = result
                    print(f"    ✅ {ramz_id}: Success")
                else:
                    print(f"    ❌ {ramz_id}: {str(result)[:50]}")
            
            # Delay between batches
            await asyncio.sleep(2)
        
        self.detailed_data = all_detailed_data
        
        # Save detailed data
        with open('phase2_detailed_data.json', 'w', encoding='utf-8') as f:
            json.dump(all_detailed_data, f, ensure_ascii=False, indent=2)
        
        print(f"\n🎉 PHASE 2 COMPLETE!")
        print(f"📊 Successfully extracted details for {len(all_detailed_data)} ramz codes")
        
        return all_detailed_data
    
    async def extract_single_ramz_detail(self, ramz_id: str):
        """Extract detailed data from a single ramz page"""
        ramz_url = f"https://guide-orientation.rnu.tn/ar/dynamique/filiere.php?id={ramz_id}"
        
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context(
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36'
            )
            page = await context.new_page()
            
            try:
                await page.goto(ramz_url, wait_until='networkidle', timeout=30000)
                await page.wait_for_timeout(3000)
                
                # Extract detailed data
                detail_data = await self.extract_ramz_page_data(page, ramz_id)
                
                await browser.close()
                return detail_data
                
            except Exception as e:
                await browser.close()
                raise e
    
    async def extract_ramz_page_data(self, page, ramz_id):
        """Extract all data from a ramz detail page"""
        data = {
            'ramz_id': ramz_id,
            'extracted_at': datetime.now().isoformat(),
            'extraction_phase': 'detailed'
        }
        
        try:
            # Extract table data
            rows = await page.query_selector_all('tr')
            
            for row in rows:
                cells = await row.query_selector_all('td')
                if len(cells) >= 2:
                    label = await cells[0].inner_text()
                    value = await cells[1].inner_text()
                    
                    label = label.strip().replace(':', '')
                    value = value.strip()
                    
                    # Map fields
                    field_mapping = {
                        'الجامعة': 'university',
                        'الولاية': 'governorate', 
                        'المؤسسة': 'institution',
                        'العنوان': 'address',
                        'الهاتف': 'phone',
                        'اسم الشعبة': 'specialization_name',
                        'رمز الشعبة': 'specialization_code_detailed',
                        'مجال التكوين': 'field_of_study',
                        'الشعب التفصيلية': 'specializations_detailed',
                        'شروط الترشح': 'requirements',
                        'نوع الباكالوريا': 'bac_type',
                        'الطاقة الاستيعابية': 'capacity_2025',
                        'مناظرة': 'requires_test',
                        'التوزيع الجغرافي': 'geographical_distribution',
                        'شروط أخرى': 'conditions',
                        'مدة الدراسة': 'study_duration',
                        'آخر معدل موجه': 'last_oriented_score_2024'
                    }
                    
                    for arabic_label, english_field in field_mapping.items():
                        if arabic_label in label:
                            data[english_field] = value
                            break
            
            # Extract historical scores
            historical_scores = {}
            
            # Look for values.php data or chart data
            try:
                await page.wait_for_function('window.myChart && window.myChart.data', timeout=5000)
                chart_data = await page.evaluate('window.myChart.data.datasets[0].data')
                chart_labels = await page.evaluate('window.myChart.data.labels')
                
                for year, score in zip(chart_labels, chart_data):
                    if score and score != 0:
                        historical_scores[str(year)] = float(score)
                        
            except:
                # Fallback: try to extract from page content
                content = await page.content()
                score_patterns = [
                    r'(\d{4})[^\d]*?(\d+\.?\d*)',
                    r'data:\s*\[([^\]]+)\]',
                    r'labels:\s*\[([^\]]+)\]'
                ]
                
                for pattern in score_patterns:
                    matches = re.findall(pattern, content)
                    if matches:
                        for match in matches:
                            try:
                                if len(match) == 2:
                                    year, score = match
                                    if 2010 <= int(year) <= 2024:
                                        historical_scores[year] = float(score)
                            except:
                                continue
            
            if historical_scores:
                data['historical_scores'] = historical_scores
            
            # Set 7% field based on specialization code
            if 'specialization_code_detailed' in data:
                spec_code = data['specialization_code_detailed']
                last_three = spec_code[-3:] if len(spec_code) >= 3 else ''
                
                # Load codes.csv for 7% determination
                try:
                    with open('codes.csv', 'r', encoding='utf-8') as f:
                        no_seven_percent_codes = [row.strip() for row in f.readlines()]
                    
                    data['seven_percent'] = "لا" if last_three in no_seven_percent_codes else "نعم"
                except:
                    data['seven_percent'] = "نعم"  # Default
            
            return data
            
        except Exception as e:
            data['error'] = str(e)
            return data
    
    def phase3_merge_data(self):
        """Phase 3: Merge bulk and detailed data"""
        print(f"\n🔄 PHASE 3: MERGING BULK AND DETAILED DATA")
        print("=" * 50)
        
        # Create a mapping of ramz_id to bulk data
        bulk_map = {}
        for record in self.bulk_data:
            ramz_id = record['ramz_id']
            bulk_map[ramz_id] = record
        
        # Merge data
        for ramz_id in self.all_ramz_codes:
            merged_record = {}
            
            # Start with bulk data if available
            if ramz_id in bulk_map:
                merged_record.update(bulk_map[ramz_id])
            
            # Add/override with detailed data if available
            if ramz_id in self.detailed_data:
                detailed = self.detailed_data[ramz_id]
                merged_record.update(detailed)
            
            # Ensure minimum required fields
            if 'ramz_id' not in merged_record:
                merged_record['ramz_id'] = ramz_id
            
            if 'ramz_link' not in merged_record:
                merged_record['ramz_link'] = f"https://guide-orientation.rnu.tn/ar/dynamique/filiere.php?id={ramz_id}"
            
            merged_record['final_merge_timestamp'] = datetime.now().isoformat()
            
            self.final_data.append(merged_record)
        
        print(f"✅ Merged {len(self.final_data)} records")
        
        # Save final data
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # JSON
        json_file = f'tunisia_university_hybrid_final_{timestamp}.json'
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(self.final_data, f, ensure_ascii=False, indent=2)
        
        # CSV
        csv_file = f'tunisia_university_hybrid_final_{timestamp}.csv'
        if self.final_data:
            fieldnames = list(self.final_data[0].keys())
            with open(csv_file, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(self.final_data)
        
        print(f"\n🎉 FINAL OUTPUT SAVED:")
        print(f"📄 JSON: {json_file}")
        print(f"📄 CSV: {csv_file}")
        
        return self.final_data

async def main():
    """Main execution function"""
    scraper = HybridTunisiaUniversityScraper()
    
    print("🇹🇳 HYBRID TUNISIA UNIVERSITY SCRAPER")
    print("=" * 60)
    print("Strategy:")
    print("1. Phase 1: Fast bulk extraction of ramz codes from dropdown combinations")
    print("2. Phase 2: Concurrent detailed extraction from individual ramz pages")
    print("3. Phase 3: Merge and create final comprehensive dataset")
    print()
    
    start_time = datetime.now()
    
    try:
        # Phase 1: Bulk extraction
        ramz_codes = await scraper.phase1_bulk_extraction()
        
        if not ramz_codes:
            print("❌ No ramz codes found in Phase 1")
            return
        
        # Phase 2: Detailed extraction
        await scraper.phase2_detailed_extraction(ramz_codes)
        
        # Phase 3: Merge data
        final_data = scraper.phase3_merge_data()
        
        end_time = datetime.now()
        duration = end_time - start_time
        
        print(f"\n🎯 SCRAPING COMPLETE!")
        print(f"⏱️  Total time: {duration}")
        print(f"📊 Final records: {len(final_data)}")
        print(f"📊 Average time per record: {duration.total_seconds() / len(final_data):.2f}s")
        
        # Show summary statistics
        bulk_count = len([r for r in final_data if r.get('extraction_phase') == 'bulk'])
        detailed_count = len([r for r in final_data if 'historical_scores' in r])
        
        print(f"\n📈 SUMMARY STATISTICS:")
        print(f"   Records with bulk data: {bulk_count}")
        print(f"   Records with detailed data: {detailed_count}")
        print(f"   Records with historical scores: {len([r for r in final_data if r.get('historical_scores')])}")
        
    except Exception as e:
        print(f"❌ Error in main execution: {e}")

if __name__ == "__main__":
    asyncio.run(main())
