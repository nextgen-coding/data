#!/usr/bin/env python3
"""
Comprehensive production scraper using the correct workflow and ramz URL format
"""

import asyncio
import json
import csv
from playwright.async_api import async_playwright
from datetime import datetime
import re

async def comprehensive_data_extraction():
    """Extract comprehensive data using the correct workflow and ramz URL format"""
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=False,  # Keep visible for monitoring
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
        
        print("🇹🇳 TUNISIA UNIVERSITY COMPREHENSIVE SCRAPER")
        print("=" * 60)
        print("Using correct ramz URL format: /ar/dynamique/filiere.php?id=XXXXXX")
        print("Testing 3x3x3 combinations: 3 bac types × 3 universities × 3 institutions")
        print()
        
        all_results = []
        
        try:
            print("🌐 Step 1: Navigating to main page...")
            await page.goto('https://guide-orientation.rnu.tn/index.php', wait_until='networkidle')
            await page.wait_for_timeout(3000)
            
            print("🔍 Step 2: Finding bac dropdown...")
            bac_dropdown = await page.query_selector('select[name="fBac"]')
            
            if not bac_dropdown:
                print("❌ Could not find bac dropdown")
                return []
            
            print("✅ Found bac dropdown")
            
            # Get all bac options
            bac_options = await bac_dropdown.query_selector_all('option')
            bac_types = []
            
            for option in bac_options:
                value = await option.get_attribute('value')
                text = await option.inner_text()
                if value and value != '' and value != '0':
                    bac_types.append({'value': value, 'text': text.strip()})
            
            print(f"📋 Found {len(bac_types)} bac types:")
            for bt in bac_types:
                print(f"  {bt['value']}: {bt['text']}")
            
            # Process first 3 bac types
            test_bac_types = bac_types[:3]
            
            for bac_idx, bac_type in enumerate(test_bac_types, 1):
                print(f"\n🎯 Processing bac type {bac_idx}/{len(test_bac_types)}: {bac_type['text']}")
                
                try:
                    # Navigate back to main page
                    await page.goto('https://guide-orientation.rnu.tn/index.php', wait_until='networkidle')
                    await page.wait_for_timeout(2000)
                    
                    # Re-find dropdown
                    bac_dropdown = await page.query_selector('select[name="fBac"]')
                    
                    # Select bac type
                    await bac_dropdown.select_option(bac_type['value'])
                    await page.wait_for_timeout(3000)  # Wait for chained selects
                    
                    print(f"✅ Selected bac type: {bac_type['text']}")
                    
                    # Get university options
                    univ_dropdown = await page.query_selector('select[name="fUniv"]')
                    if univ_dropdown:
                        univ_options = await univ_dropdown.query_selector_all('option')
                        print(f"📋 University dropdown populated with {len(univ_options)} options")
                        
                        # Get first 3 university options (skip "إختر الجامعة" option)
                        valid_univ_options = []
                        for option in univ_options:
                            value = await option.get_attribute('value')
                            text = await option.inner_text()
                            if value and value != '' and value != '0' and 'إختر' not in text:
                                valid_univ_options.append({'value': value, 'text': text.strip()})
                        
                        test_univ_options = valid_univ_options[:3]  # First 3 universities
                        print(f"📋 Testing with {len(test_univ_options)} universities")
                        
                        # Process each university
                        for univ_idx, univ_option in enumerate(test_univ_options, 1):
                            print(f"\n  🏛️ University {univ_idx}/{len(test_univ_options)}: {univ_option['text']}")
                            
                            try:
                                # Navigate back and re-select bac type
                                await page.goto('https://guide-orientation.rnu.tn/index.php', wait_until='networkidle')
                                await page.wait_for_timeout(2000)
                                
                                bac_dropdown = await page.query_selector('select[name="fBac"]')
                                await bac_dropdown.select_option(bac_type['value'])
                                await page.wait_for_timeout(3000)
                                
                                # Select university
                                univ_dropdown = await page.query_selector('select[name="fUniv"]')
                                await univ_dropdown.select_option(univ_option['value'])
                                await page.wait_for_timeout(3000)  # Wait for institution dropdown to populate
                                
                                print(f"  ✅ Selected university: {univ_option['text']}")
                                
                                # Get institution options
                                etab_dropdown = await page.query_selector('select[name="fEtab"]')
                                if etab_dropdown:
                                    etab_options = await etab_dropdown.query_selector_all('option')
                                    print(f"  📋 Institution dropdown populated with {len(etab_options)} options")
                                    
                                    # Get first 3 institution options
                                    valid_etab_options = []
                                    for option in etab_options:
                                        value = await option.get_attribute('value')
                                        text = await option.inner_text()
                                        if value and value != '' and value != '0' and 'إختر' not in text:
                                            valid_etab_options.append({'value': value, 'text': text.strip()})
                                    
                                    test_etab_options = valid_etab_options[:3]  # First 3 institutions
                                    print(f"  📋 Testing with {len(test_etab_options)} institutions")
                                    
                                    # Process each institution
                                    for etab_idx, etab_option in enumerate(test_etab_options, 1):
                                        print(f"\n    🏢 Institution {etab_idx}/{len(test_etab_options)}: {etab_option['text']}")
                                        
                                        try:
                                            # Navigate back and re-select all dropdowns
                                            await page.goto('https://guide-orientation.rnu.tn/index.php', wait_until='networkidle')
                                            await page.wait_for_timeout(2000)
                                            
                                            # Select bac type
                                            bac_dropdown = await page.query_selector('select[name="fBac"]')
                                            await bac_dropdown.select_option(bac_type['value'])
                                            await page.wait_for_timeout(3000)
                                            
                                            # Select university
                                            univ_dropdown = await page.query_selector('select[name="fUniv"]')
                                            await univ_dropdown.select_option(univ_option['value'])
                                            await page.wait_for_timeout(3000)
                                            
                                            # Select institution
                                            etab_dropdown = await page.query_selector('select[name="fEtab"]')
                                            await etab_dropdown.select_option(etab_option['value'])
                                            await page.wait_for_timeout(2000)
                                            
                                            print(f"    ✅ Selected institution: {etab_option['text']}")
                                            
                                            # Submit the form
                                            submit_button = await page.query_selector('input[name="submit"]')
                                            if submit_button:
                                                print("    🔍 Clicking search button...")
                                                await submit_button.click()
                                                await page.wait_for_timeout(5000)
                                                
                                                # Set pagination to show 100 entries
                                                await set_pagination_to_100(page)
                                                
                                                # Take screenshot after pagination
                                                combo_id = f"bac{bac_type['value']}_univ{univ_option['value']}_etab{etab_option['value']}"
                                                await page.screenshot(path=f'combo_results_{combo_id}.png')
                                                
                                                # Extract table data with combination info
                                                combination_info = {
                                                    'bac_type': bac_type,
                                                    'university': univ_option,
                                                    'institution': etab_option
                                                }
                                                
                                                table_data = await extract_table_data_with_combinations(page, combination_info)
                                                
                                                if table_data:
                                                    print(f"    ✅ Extracted {len(table_data)} records")
                                                    all_results.extend(table_data)
                                                    
                                                    # Save intermediate results
                                                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                                                    combo_file = f'combo_bac{bac_type["value"]}_univ{univ_option["value"]}_etab{etab_option["value"]}_{timestamp}.json'
                                                    with open(combo_file, 'w', encoding='utf-8') as f:
                                                        json.dump(table_data, f, ensure_ascii=False, indent=2)
                                                else:
                                                    print(f"    ❌ No data found for this combination")
                                            
                                            else:
                                                print("    ❌ Submit button not found")
                                        
                                        except Exception as e:
                                            print(f"    ❌ Error processing institution {etab_option['text']}: {e}")
                                            continue
                                
                                else:
                                    print("  ❌ Institution dropdown not found")
                            
                            except Exception as e:
                                print(f"  ❌ Error processing university {univ_option['text']}: {e}")
                                continue
                    
                    else:
                        print("❌ University dropdown not found")
                
                except Exception as e:
                    print(f"❌ Error processing bac type {bac_type['text']}: {e}")
                    continue
            
            # Save final results
            if all_results:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                
                # Save JSON
                json_file = f'tunisia_comprehensive_correct_urls_{timestamp}.json'
                with open(json_file, 'w', encoding='utf-8') as f:
                    json.dump(all_results, f, ensure_ascii=False, indent=2)
                
                # Save CSV
                csv_file = f'tunisia_comprehensive_correct_urls_{timestamp}.csv'
                if all_results:
                    fieldnames = list(all_results[0].keys())
                    with open(csv_file, 'w', newline='', encoding='utf-8') as f:
                        writer = csv.DictWriter(f, fieldnames=fieldnames)
                        writer.writeheader()
                        writer.writerows(all_results)
                
                # Create ramz links CSV with correct format
                ramz_links_file = f'ramz_links_correct_format_{timestamp}.csv'
                with open(ramz_links_file, 'w', newline='', encoding='utf-8') as f:
                    writer = csv.writer(f)
                    writer.writerow(['ramz_code', 'ramz_link'])
                    for record in all_results:
                        if record.get('full_ramz_id'):
                            full_ramz_id = record['full_ramz_id']
                            ramz_link = f"https://guide-orientation.rnu.tn/ar/dynamique/filiere.php?id={full_ramz_id}"
                            writer.writerow([full_ramz_id, ramz_link])
                
                print(f"\n🎉 EXTRACTION COMPLETE!")
                print(f"📊 Total records: {len(all_results)}")
                print(f"📁 Files saved:")
                print(f"   📄 JSON: {json_file}")
                print(f"   📄 CSV: {csv_file}")
                print(f"   📄 Ramz Links: {ramz_links_file}")
                
                # Show breakdown by combination
                combination_counts = {}
                bac_counts = {}
                for record in all_results:
                    bac_name = record.get('bac_type_name', 'Unknown')
                    univ_name = record.get('university_name', 'Unknown')
                    etab_name = record.get('institution_name', 'Unknown')
                    
                    combo_key = f"{bac_name} → {univ_name} → {etab_name}"
                    combination_counts[combo_key] = combination_counts.get(combo_key, 0) + 1
                    bac_counts[bac_name] = bac_counts.get(bac_name, 0) + 1
                
                print(f"\n📋 Breakdown by bac type:")
                for bac_name, count in bac_counts.items():
                    print(f"   {bac_name}: {count} specializations")
                
                print(f"\n📋 Breakdown by combination:")
                for combo, count in list(combination_counts.items())[:10]:  # Show first 10 combinations
                    print(f"   {combo}: {count} specializations")
                if len(combination_counts) > 10:
                    print(f"   ... and {len(combination_counts) - 10} more combinations")
            
            else:
                print("❌ No data extracted")
        
        except Exception as e:
            print(f"❌ Error in main extraction: {e}")
        
        finally:
            await browser.close()
        
        return all_results

async def extract_table_data_with_combinations(page, combination_info):
    """Extract table data with combination information included"""
    
    results = []
    
    try:
        # Wait for table to load
        await page.wait_for_timeout(3000)
        
        # Find the results table - look for table with actual data
        tables = await page.query_selector_all('table')
        results_table = None
        
        for table in tables:
            rows = await table.query_selector_all('tr')
            if len(rows) > 3:  # Look for table with substantial data
                # Check if first row has headers
                first_row_cells = await rows[0].query_selector_all('td, th')
                if len(first_row_cells) >= 6:  # Minimum expected columns
                    results_table = table
                    break
        
        if not results_table:
            print("    ❌ No results table found")
            return results
        
        rows = await results_table.query_selector_all('tr')
        print(f"    📊 Found results table with {len(rows)} rows (including header)")
        
        # Process data rows (skip header) - now handles up to 100+ entries
        processed_count = 0
        for i, row in enumerate(rows[1:], 1):
            try:
                cells = await row.query_selector_all('td')
                
                if len(cells) >= 6:  # Minimum required columns
                    # Extract cell text
                    cell_texts = []
                    for cell in cells:
                        text = await cell.inner_text()
                        cell_texts.append(text.strip())
                    
                    # Extract ramz code from first cell
                    ramz_code = ""
                    if cell_texts[0]:
                        # Look for 5-6 digit code
                        ramz_match = re.search(r'(\d{5,6})', cell_texts[0])
                        if ramz_match:
                            ramz_code = ramz_match.group(1)
                    
                    # Only process if we have a ramz code
                    if ramz_code:
                        # Construct correct 6-digit ramz ID: bac_type_id + ramz_code
                        full_ramz_id = f"{combination_info['bac_type']['value']}{ramz_code}"
                        ramz_link = f"https://guide-orientation.rnu.tn/ar/dynamique/filiere.php?id={full_ramz_id}"
                        
                        # Create comprehensive record with combination info
                        record = {
                            'bac_type_id': combination_info['bac_type']['value'],
                            'bac_type_name': combination_info['bac_type']['text'],
                            'university_id': combination_info['university']['value'],
                            'university_name': combination_info['university']['text'],
                            'institution_id': combination_info['institution']['value'],
                            'institution_name': combination_info['institution']['text'],
                            'ramz_code': ramz_code,
                            'full_ramz_id': full_ramz_id,
                            'ramz_link': ramz_link,
                            'table_specialization': cell_texts[1] if len(cell_texts) > 1 else '',
                            'table_university': cell_texts[2] if len(cell_texts) > 2 else '',
                            'table_institution': cell_texts[3] if len(cell_texts) > 3 else '',
                            'table_location': cell_texts[4] if len(cell_texts) > 4 else '',
                            'table_criteria': cell_texts[5] if len(cell_texts) > 5 else '',
                            'table_capacity': cell_texts[6] if len(cell_texts) > 6 else '',
                            'table_duration': cell_texts[7] if len(cell_texts) > 7 else '',
                            'table_last_score': cell_texts[8] if len(cell_texts) > 8 else '',
                            'extracted_at': datetime.now().isoformat()
                        }
                        
                        results.append(record)
                        processed_count += 1
                        print(f"      ✅ Row {i}: {full_ramz_id} - {cell_texts[1][:30]}")
            
            except Exception as e:
                print(f"    ❌ Error processing row {i}: {e}")
                continue
        
        print(f"    ✅ Successfully extracted {len(results)} records from combination ({processed_count} processed)")
        
        # If we got close to 100 records, mention that pagination was likely successful
        if len(results) >= 90:
            print(f"    🎉 Large dataset extracted ({len(results)} records) - pagination likely set to 100!")
        elif len(results) >= 10:
            print(f"    ✅ Good dataset extracted ({len(results)} records)")
        else:
            print(f"    ⚠️ Small dataset ({len(results)} records) - check if more entries are available")
        
    except Exception as e:
        print(f"    ❌ Error extracting table data: {e}")
    
    return results

async def extract_table_data_with_correct_ramz_urls(page, bac_type):
    """Extract table data using correct ramz URL format"""
    
    results = []
    
    try:
        # Wait for table to load
        await page.wait_for_timeout(3000)
        
        # Find the results table - look for table with actual data
        tables = await page.query_selector_all('table')
        results_table = None
        
        for table in tables:
            rows = await table.query_selector_all('tr')
            if len(rows) > 5:  # Look for table with substantial data
                # Check if first row has headers
                first_row_cells = await rows[0].query_selector_all('td, th')
                if len(first_row_cells) >= 6:  # Minimum expected columns
                    results_table = table
                    break
        
        if not results_table:
            print("❌ No results table found")
            return results
        
        rows = await results_table.query_selector_all('tr')
        print(f"📊 Found results table with {len(rows)} rows")
        
        # Process data rows (skip header)
        for i, row in enumerate(rows[1:], 1):
            try:
                cells = await row.query_selector_all('td')
                
                if len(cells) >= 6:  # Minimum required columns
                    # Extract cell text
                    cell_texts = []
                    for cell in cells:
                        text = await cell.inner_text()
                        cell_texts.append(text.strip())
                    
                    # Extract ramz code from first cell
                    ramz_code = ""
                    if cell_texts[0]:
                        # Look for 5-6 digit code
                        ramz_match = re.search(r'(\d{5,6})', cell_texts[0])
                        if ramz_match:
                            ramz_code = ramz_match.group(1)
                    
                    # Only process if we have a ramz code
                    if ramz_code:
                        # Construct correct 6-digit ramz ID: bac_type_id + ramz_code
                        full_ramz_id = f"{bac_type['value']}{ramz_code}"
                        ramz_link = f"https://guide-orientation.rnu.tn/ar/dynamique/filiere.php?id={full_ramz_id}"
                        
                        # Create comprehensive record
                        record = {
                            'bac_type_id': bac_type['value'],
                            'bac_type_name': bac_type['text'],
                            'ramz_code': ramz_code,
                            'ramz_link': ramz_link,
                            'table_specialization': cell_texts[1] if len(cell_texts) > 1 else '',
                            'table_university': cell_texts[2] if len(cell_texts) > 2 else '',
                            'table_institution': cell_texts[3] if len(cell_texts) > 3 else '',
                            'table_location': cell_texts[4] if len(cell_texts) > 4 else '',
                            'table_criteria': cell_texts[5] if len(cell_texts) > 5 else '',
                            'table_capacity': cell_texts[6] if len(cell_texts) > 6 else '',
                            'table_duration': cell_texts[7] if len(cell_texts) > 7 else '',
                            'table_last_score': cell_texts[8] if len(cell_texts) > 8 else '',
                            'extracted_at': datetime.now().isoformat()
                        }
                        
                        results.append(record)
                        print(f"  ✅ Row {i}: {ramz_code} - {cell_texts[1][:50]}")
            
            except Exception as e:
                print(f"❌ Error processing row {i}: {e}")
                continue
        
        print(f"✅ Successfully extracted {len(results)} records")
        
    except Exception as e:
        print(f"❌ Error extracting table data: {e}")
    
    return results

async def set_pagination_to_100(page):
    """Set the results table to show 100 entries per page"""
    
    try:
        print("    📄 Setting pagination to show 100 entries...")
        
        # Look for the pagination dropdown - common selectors for DataTables
        pagination_selectors = [
            'select[name="table3_length"]',  # DataTables default name
            'select[name*="length"]',        # Any select with "length" in name
            'select.form-control',           # Bootstrap form control
            'select[aria-controls*="table"]', # ARIA controls referencing table
            '.dataTables_length select',     # DataTables wrapper
        ]
        
        pagination_dropdown = None
        
        for selector in pagination_selectors:
            try:
                pagination_dropdown = await page.query_selector(selector)
                if pagination_dropdown:
                    print(f"    ✅ Found pagination dropdown with selector: {selector}")
                    break
            except Exception:
                continue
        
        if pagination_dropdown:
            # Get all options to see available values
            options = await pagination_dropdown.query_selector_all('option')
            print(f"    📋 Pagination options available: {len(options)}")
            
            # Look for option with value 100 or text containing 100
            target_option = None
            for option in options:
                value = await option.get_attribute('value')
                text = await option.inner_text()
                print(f"      Option: value='{value}', text='{text.strip()}'")
                
                if value == '100' or '100' in text:
                    target_option = value
                    break
            
            if target_option:
                print(f"    🎯 Selecting pagination option: {target_option}")
                await pagination_dropdown.select_option(target_option)
                await page.wait_for_timeout(3000)  # Wait for table to reload
                print(f"    ✅ Successfully set pagination to show 100 entries")
            else:
                print(f"    ⚠️ No 100-entry option found, using default pagination")
                
        else:
            print(f"    ⚠️ No pagination dropdown found, table may show default entries")
            
            # Alternative approach: look for any element that might control pagination
            print(f"    🔍 Looking for alternative pagination controls...")
            
            # Look for buttons or links with "100" text
            pagination_links = await page.query_selector_all('a, button, span')
            for link in pagination_links:
                try:
                    text = await link.inner_text()
                    if '100' in text and ('entries' in text.lower() or 'مُدخلات' in text):
                        print(f"    🎯 Found pagination control: {text}")
                        await link.click()
                        await page.wait_for_timeout(3000)
                        print(f"    ✅ Clicked pagination control")
                        break
                except Exception:
                    continue
    
    except Exception as e:
        print(f"    ❌ Error setting pagination: {e}")
        print(f"    ⚠️ Continuing with default pagination...")

if __name__ == "__main__":
    asyncio.run(comprehensive_data_extraction())
