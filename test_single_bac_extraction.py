#!/usr/bin/env python3
"""
Simplified workflow scraper: Test with one bac type to debug extraction
"""

import asyncio
import json
import csv
from playwright.async_api import async_playwright
from datetime import datetime
import re

async def test_single_bac_extraction():
    """Test extraction with just one bac type"""
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context(
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36'
        )
        
        page = await context.new_page()
        
        print("🌐 Navigating to main page...")
        await page.goto('https://guide-orientation.rnu.tn/', wait_until='networkidle')
        await page.wait_for_timeout(3000)
        
        print("🔍 Finding bac dropdown...")
        bac_dropdown = await page.query_selector('select[name="fBac"]')
        
        if bac_dropdown:
            print("✅ Found bac dropdown")
            
            # Select first real bac type (value='1' - آداب)
            await bac_dropdown.select_option('1')
            await page.wait_for_timeout(2000)
            print("✅ Selected آداب")
            
            # Click search button
            search_button = await page.query_selector('input[name="submit"]')
            if search_button:
                print("🔍 Clicking search button...")
                await search_button.click()
                await page.wait_for_timeout(5000)
                
                # Take screenshot of results
                await page.screenshot(path='test_single_bac_results.png')
                
                print("📊 Extracting table data...")
                
                # Find the table
                table = await page.query_selector('table')
                if table:
                    rows = await table.query_selector_all('tr')
                    print(f"📊 Found table with {len(rows)} rows")
                    
                    results = []
                    
                    # Extract first few rows to test
                    for i, row in enumerate(rows[1:6], 1):  # Test first 5 data rows
                        try:
                            cells = await row.query_selector_all('td')
                            print(f"\nRow {i}: {len(cells)} cells")
                            
                            if len(cells) >= 8:
                                # Get text from each cell
                                cell_texts = []
                                for j, cell in enumerate(cells):
                                    text = await cell.inner_text()
                                    cell_texts.append(text.strip())
                                    print(f"  Cell {j}: '{text.strip()}'")
                                
                                # Extract ramz code and link from first cell
                                ramz_cell = cells[0]
                                ramz_text = cell_texts[0]
                                ramz_code = ""
                                ramz_link = ""
                                
                                # Extract ramz code (numbers)
                                ramz_match = re.search(r'(\d{5,6})', ramz_text)
                                if ramz_match:
                                    ramz_code = ramz_match.group(1)
                                    print(f"  📍 Ramz code: {ramz_code}")
                                
                                # Extract ramz link
                                ramz_link_element = await ramz_cell.query_selector('a')
                                if ramz_link_element:
                                    href = await ramz_link_element.get_attribute('href')
                                    print(f"  🔗 Raw href: {href}")
                                    
                                    if href and 'PopupCentrer' in href:
                                        # Try different regex patterns
                                        patterns = [
                                            r'PopupCentrer\("([^"]+)"',
                                            r"PopupCentrer\('([^']+)'",
                                            r'PopupCentrer\(([^)]+)\)',
                                        ]
                                        
                                        for pattern in patterns:
                                            try:
                                                url_match = re.search(pattern, href)
                                                if url_match:
                                                    relative_url = url_match.group(1).strip('\'"')
                                                    ramz_link = f"https://guide-orientation.rnu.tn/{relative_url}"
                                                    print(f"  ✅ Extracted link: {ramz_link}")
                                                    break
                                            except Exception as e:
                                                print(f"  ❌ Pattern failed: {pattern} - {e}")
                                                continue
                                
                                # Create record
                                record = {
                                    'bac_type': 'آداب',
                                    'ramz_code': ramz_code,
                                    'ramz_link': ramz_link,
                                    'specialization': cell_texts[1] if len(cell_texts) > 1 else '',
                                    'university': cell_texts[2] if len(cell_texts) > 2 else '',
                                    'institution': cell_texts[3] if len(cell_texts) > 3 else '',
                                    'governorate': cell_texts[4] if len(cell_texts) > 4 else '',
                                    'requirements': cell_texts[5] if len(cell_texts) > 5 else '',
                                    'capacity': cell_texts[6] if len(cell_texts) > 6 else '',
                                    'duration': cell_texts[7] if len(cell_texts) > 7 else '',
                                }
                                
                                results.append(record)
                                print(f"  ✅ Record created for {ramz_code}")
                        
                        except Exception as e:
                            print(f"❌ Error processing row {i}: {e}")
                    
                    # Save results
                    if results:
                        with open('test_single_bac_results.json', 'w', encoding='utf-8') as f:
                            json.dump(results, f, ensure_ascii=False, indent=2)
                        print(f"\n✅ Saved {len(results)} records to test_single_bac_results.json")
                        
                        # Show first record
                        if results:
                            print(f"\n📋 First record:")
                            for key, value in results[0].items():
                                print(f"   {key}: {value}")
                    
                else:
                    print("❌ No table found")
            else:
                print("❌ No search button found")
        else:
            print("❌ No bac dropdown found")
        
        await browser.close()

if __name__ == "__main__":
    asyncio.run(test_single_bac_extraction())
