#!/usr/bin/env python3
"""
Complete workflow scraper: Select dropdowns -> Click search -> Extract table data
"""

import asyncio
import json
import csv
from playwright.async_api import async_playwright
from datetime import datetime
import re
import time

async def scrape_with_dropdown_workflow():
    """Follow the complete user workflow to get populated data"""
    
    async with async_playwright() as p:
        # Launch browser 
        browser = await p.chromium.launch(
            headless=False,  # Keep visible to debug
            args=[
                '--disable-blink-features=AutomationControlled',
                '--no-first-run',
                '--disable-default-apps'
            ]
        )
        
        context = await browser.new_context(
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36',
            viewport={'width': 1920, 'height': 1080}
        )
        
        page = await context.new_page()
        
        print("🌐 Step 1: Navigating to main page...")
        
        # Navigate to main page
        await page.goto('https://guide-orientation.rnu.tn/', wait_until='networkidle')
        await page.wait_for_timeout(3000)
        
        # Take screenshot for debugging
        await page.screenshot(path='debug_01_main_page.png')
        
        print("🔍 Step 2: Finding dropdown elements...")
        
        # Find the form elements
        try:
            # Look for the bac type dropdown (correct name is fBac with capital B)
            bac_dropdown = await page.query_selector('select[name="fBac"]')
            if not bac_dropdown:
                bac_dropdown = await page.query_selector('#fBac')
            
            if bac_dropdown:
                print("✅ Found bac dropdown")
                
                # Get all bac options
                bac_options = await bac_dropdown.query_selector_all('option')
                print(f"📋 Found {len(bac_options)} bac options:")
                
                bac_types = []
                for option in bac_options:
                    value = await option.get_attribute('value')
                    text = await option.inner_text()
                    if value and value != '0':  # Skip empty/default options
                        bac_types.append({'value': value, 'text': text.strip()})
                        print(f"  {value}: {text.strip()}")
                
                # Test with first 5 bac types
                test_bac_types = bac_types[:5]
                all_results = []
                
                for i, bac_type in enumerate(test_bac_types, 1):
                    print(f"\n🎯 Step 3.{i}: Testing bac type {bac_type['value']} - {bac_type['text']}")
                    
                    try:
                        # Select the bac type
                        await bac_dropdown.select_option(bac_type['value'])
                        await page.wait_for_timeout(2000)  # Wait for cascading dropdowns to load
                        
                        print(f"✅ Selected bac type: {bac_type['text']}")
                        
                        # Take screenshot after selection
                        await page.screenshot(path=f'debug_02_selected_bac_{bac_type["value"]}.png')
                        
                        # Find and click the search button
                        search_button = await page.query_selector('input[name="submit"]')
                        if not search_button:
                            search_button = await page.query_selector('input[type="submit"]')
                        if not search_button:
                            search_button = await page.query_selector('button[type="submit"]')
                        
                        if search_button:
                            print("🔍 Found search button, clicking...")
                            await search_button.click()
                            
                            # Wait for results to load
                            await page.wait_for_timeout(5000)
                            
                            # Take screenshot of results
                            await page.screenshot(path=f'debug_03_results_bac_{bac_type["value"]}.png')
                            
                            print("📊 Step 4: Extracting table data...")
                            
                            # Extract the results table
                            table_data = await extract_results_table(page, bac_type)
                            
                            if table_data:
                                print(f"✅ Extracted {len(table_data)} records for bac type {bac_type['value']}")
                                all_results.extend(table_data)
                                
                                # Save intermediate results
                                with open(f'results_bac_{bac_type["value"]}.json', 'w', encoding='utf-8') as f:
                                    json.dump(table_data, f, ensure_ascii=False, indent=2)
                            else:
                                print(f"❌ No data found for bac type {bac_type['value']}")
                        
                        else:
                            print("❌ Could not find search button")
                    
                    except Exception as e:
                        print(f"❌ Error processing bac type {bac_type['value']}: {e}")
                    
                    # Go back to main page for next iteration
                    if i < len(test_bac_types):
                        print("🔄 Going back to main page...")
                        await page.goto('https://guide-orientation.rnu.tn/', wait_until='networkidle')
                        await page.wait_for_timeout(2000)
                        
                        # Re-find the dropdown after navigation (correct name is fBac with capital B)
                        bac_dropdown = await page.query_selector('select[name="fBac"]')
                        if not bac_dropdown:
                            bac_dropdown = await page.query_selector('#fBac')
                
                # Save all results
                if all_results:
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    
                    # Save JSON
                    json_file = f'tunisia_complete_workflow_{timestamp}.json'
                    with open(json_file, 'w', encoding='utf-8') as f:
                        json.dump(all_results, f, ensure_ascii=False, indent=2)
                    
                    # Save CSV
                    csv_file = f'tunisia_complete_workflow_{timestamp}.csv'
                    if all_results:
                        fieldnames = list(all_results[0].keys())
                        with open(csv_file, 'w', newline='', encoding='utf-8') as f:
                            writer = csv.DictWriter(f, fieldnames=fieldnames)
                            writer.writeheader()
                            writer.writerows(all_results)
                    
                    print(f"\n🎉 WORKFLOW COMPLETE!")
                    print(f"📊 Total records extracted: {len(all_results)}")
                    print(f"📁 Files saved:")
                    print(f"   📄 JSON: {json_file}")
                    print(f"   📄 CSV: {csv_file}")
                    
                    # Show sample data
                    print(f"\n📋 Sample record:")
                    sample = all_results[0]
                    for key, value in list(sample.items())[:10]:  # Show first 10 fields
                        print(f"   {key}: {value}")
                
                else:
                    print("❌ No data was extracted from any bac type")
            
            else:
                print("❌ Could not find bac dropdown")
        
        except Exception as e:
            print(f"❌ Error in workflow: {e}")
        
        finally:
            await browser.close()
        
        return all_results

async def extract_results_table(page, bac_type):
    """Extract data from the results table after search"""
    
    results = []
    
    try:
        # Wait for table to load
        await page.wait_for_timeout(3000)
        
        # Look for the results table
        table = await page.query_selector('table')
        if not table:
            print("❌ No table found")
            return results
        
        # Get all table rows
        rows = await table.query_selector_all('tr')
        print(f"📊 Found table with {len(rows)} rows")
        
        # Skip header row, process data rows
        for i, row in enumerate(rows[1:], 1):  # Skip header
            try:
                cells = await row.query_selector_all('td')
                if len(cells) >= 8:  # Ensure we have enough columns
                    
                    # Extract cell data
                    ramz_cell = cells[0]
                    specialization_cell = cells[1]
                    university_cell = cells[2]
                    institution_cell = cells[3]
                    governorate_cell = cells[4]
                    requirements_cell = cells[5]
                    capacity_cell = cells[6]
                    duration_cell = cells[7]
                    
                    # Get text content
                    ramz_text = await ramz_cell.inner_text()
                    specialization = await specialization_cell.inner_text()
                    university = await university_cell.inner_text()
                    institution = await institution_cell.inner_text()
                    governorate = await governorate_cell.inner_text()
                    requirements = await requirements_cell.inner_text()
                    capacity = await capacity_cell.inner_text()
                    duration = await duration_cell.inner_text()
                    
                    # Extract ramz code and link from first cell
                    ramz_code = ""
                    ramz_link = ""
                    
                    # Look for ramz code (usually a number at the start)
                    ramz_match = re.search(r'(\d{5,6})', ramz_text)
                    if ramz_match:
                        ramz_code = ramz_match.group(1)
                    
                    # Look for the ramz link in href attribute
                    ramz_link_element = await ramz_cell.query_selector('a')
                    if ramz_link_element:
                        href = await ramz_link_element.get_attribute('href')
                        if href and 'javascript:PopupCentrer' in href:
                            # Extract URL from javascript call
                            url_match = re.search(r'PopupCentrer\("([^"]+)"', href)
                            if url_match:
                                relative_url = url_match.group(1)
                                ramz_link = f"https://guide-orientation.rnu.tn/{relative_url}"
                    
                    # Get last score if available (usually in the last column)
                    last_score = ""
                    if len(cells) > 8:
                        last_score_cell = cells[8]
                        last_score = await last_score_cell.inner_text()
                    
                    # Create record
                    record = {
                        'bac_type_id': bac_type['value'],
                        'bac_type_name': bac_type['text'],
                        'ramz_code': ramz_code.strip(),
                        'ramz_link': ramz_link,
                        'specialization_name': specialization.strip(),
                        'university': university.strip(),
                        'institution': institution.strip(),
                        'governorate': governorate.strip(),
                        'requirements': requirements.strip(),
                        'capacity': capacity.strip(),
                        'duration': duration.strip(),
                        'last_score_2024': last_score.strip(),
                        'extracted_at': datetime.now().isoformat()
                    }
                    
                    # Only add if we have meaningful data
                    if ramz_code and specialization.strip():
                        results.append(record)
                        print(f"  Row {i}: {ramz_code} - {specialization[:50]}")
                    
            except Exception as e:
                print(f"❌ Error extracting row {i}: {e}")
                continue
        
        print(f"✅ Extracted {len(results)} valid records from table")
        
    except Exception as e:
        print(f"❌ Error extracting table: {e}")
    
    return results

def main():
    """Main execution function"""
    
    print("🇹🇳 TUNISIA UNIVERSITY COMPLETE WORKFLOW SCRAPER")
    print("=" * 60)
    print("This scraper follows the complete user workflow:")
    print("1. Navigate to main page")
    print("2. Select bac type from dropdown")
    print("3. Click search button (ib7ath)")
    print("4. Extract populated table data")
    print("5. Get ramz links and complete information")
    print()
    
    # Run the workflow
    try:
        results = asyncio.run(scrape_with_dropdown_workflow())
        
        if results:
            print(f"\n🎯 FINAL SUMMARY:")
            print(f"   Total specializations found: {len(results)}")
            
            # Count by bac type
            bac_counts = {}
            for record in results:
                bac_type = record['bac_type_name']
                bac_counts[bac_type] = bac_counts.get(bac_type, 0) + 1
            
            print(f"   Breakdown by bac type:")
            for bac_type, count in bac_counts.items():
                print(f"     {bac_type}: {count} specializations")
                
        else:
            print("❌ No results were extracted")
    
    except Exception as e:
        print(f"❌ Error in main execution: {e}")

if __name__ == "__main__":
    main()
