#!/usr/bin/env python3
"""
Fixed Playwright-based scraper to debug and extract correct data
"""

import asyncio
import json
import csv
from playwright.async_api import async_playwright
from datetime import datetime
import re

async def debug_with_playwright(url, ramz_id):
    """Use Playwright to debug what's really happening on the page"""
    
    async with async_playwright() as p:
        # Launch browser in headless mode to avoid issues
        browser = await p.chromium.launch(
            headless=True,  # Changed to headless for stability
            args=[
                '--disable-blink-features=AutomationControlled',
                '--no-first-run',
                '--disable-default-apps',
                '--disable-infobars'
            ]
        )
        
        context = await browser.new_context(
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36',
            viewport={'width': 1920, 'height': 1080}
        )
        
        page = await context.new_page()
        
        # Track network requests
        requests_log = []
        responses_log = []
        
        def log_request(request):
            requests_log.append({
                'url': request.url,
                'method': request.method,
                'headers': dict(request.headers)
            })
        
        def log_response(response):
            responses_log.append({
                'url': response.url,
                'status': response.status,
                'headers': dict(response.headers)
            })
        
        page.on('request', log_request)
        page.on('response', log_response)
        
        print(f"🌐 Navigating to: {url}")
        
        try:
            # Navigate to page
            await page.goto(url, wait_until='networkidle', timeout=30000)
            
            # Wait for potential JavaScript to load
            await page.wait_for_timeout(3000)
            
            # Take screenshots for debugging
            await page.screenshot(path=f'debug_playwright_{ramz_id}.png')
            
            # Get page content
            content = await page.content()
            with open(f'debug_playwright_{ramz_id}.html', 'w', encoding='utf-8') as f:
                f.write(content)
            
            # Extract table data using better selectors
            print(f"🔍 Extracting data from page...")
            
            # Look for the main table
            table_data = {}
            
            # Try different table extraction methods
            try:
                # Method 1: Find all table rows
                rows = await page.query_selector_all('tr')
                print(f"Found {len(rows)} table rows")
                
                for i, row in enumerate(rows):
                    try:
                        cells = await row.query_selector_all('td')
                        if len(cells) >= 2:
                            label_element = cells[0]
                            value_element = cells[1]
                            
                            label = await label_element.inner_text()
                            value = await value_element.inner_text()
                            
                            label = label.strip()
                            value = value.strip()
                            
                            if label and label != value and len(label) > 0:
                                table_data[label] = value
                                print(f"  Row {i}: '{label}' -> '{value}'")
                    except Exception as e:
                        print(f"Error processing row {i}: {e}")
                        continue
                        
            except Exception as e:
                print(f"Error extracting table data: {e}")
            
            # Method 2: Look for specific elements by text content
            try:
                # Look for specific fields we know should exist
                specialization_elements = await page.query_selector_all('*:has-text("الاختصاص")')
                for elem in specialization_elements:
                    text = await elem.inner_text()
                    print(f"Found specialization element: {text}")
                
                university_elements = await page.query_selector_all('*:has-text("الجامعة")')
                for elem in university_elements:
                    text = await elem.inner_text()
                    print(f"Found university element: {text}")
                    
            except Exception as e:
                print(f"Error with specific element search: {e}")
            
            # Check for values.php requests
            values_requests = [r for r in requests_log if 'values.php' in r['url']]
            print(f"📊 Found {len(values_requests)} values.php requests:")
            for req in values_requests:
                print(f"  {req['method']} {req['url']}")
            
            # Try to get values.php data manually
            print(f"🎯 Testing values.php endpoint...")
            
            try:
                # Test direct access to values.php
                values_url = f"https://guide-orientation.rnu.tn/ar/dynamique/values.php"
                values_response = await page.goto(values_url, wait_until='networkidle', timeout=15000)
                values_content = await page.content()
                
                print(f"Values.php status: {values_response.status}")
                print(f"Values.php content preview: {values_content[:200]}")
                
                with open(f'debug_values_{ramz_id}.txt', 'w', encoding='utf-8') as f:
                    f.write(values_content)
                    
            except Exception as e:
                print(f"Error accessing values.php: {e}")
            
            # Save debug info
            debug_info = {
                'ramz_id': ramz_id,
                'url': url,
                'table_data': table_data,
                'requests_count': len(requests_log),
                'responses_count': len(responses_log),
                'values_requests': len(values_requests),
                'timestamp': datetime.now().isoformat()
            }
            
            with open(f'debug_info_{ramz_id}.json', 'w', encoding='utf-8') as f:
                json.dump(debug_info, f, ensure_ascii=False, indent=2)
            
            print(f"📁 Debug files saved:")
            print(f"  - debug_playwright_{ramz_id}.png (screenshot)")
            print(f"  - debug_playwright_{ramz_id}.html (page HTML)")
            print(f"  - debug_values_{ramz_id}.txt (values.php response)")
            print(f"  - debug_info_{ramz_id}.json (extracted data)")
            
            return debug_info
            
        except Exception as e:
            print(f"❌ Error during page processing: {e}")
            return {
                'ramz_id': ramz_id,
                'url': url,
                'error': str(e),
                'table_data': {},
                'timestamp': datetime.now().isoformat()
            }
        finally:
            await browser.close()

async def test_playwright_scraping():
    """Test Playwright scraping on a few sample URLs"""
    
    # Test cases - same URLs as before
    test_cases = [
        {'ramz_id': '110101', 'url': 'https://guide-orientation.rnu.tn/ar/dynamique/filiere.php?id=110101'},
        {'ramz_id': '210102', 'url': 'https://guide-orientation.rnu.tn/ar/dynamique/filiere.php?id=210102'},
        {'ramz_id': '310101', 'url': 'https://guide-orientation.rnu.tn/ar/dynamique/filiere.php?id=310101'}
    ]
    
    print("🎭 PLAYWRIGHT DEBUG SESSION")
    print("=" * 50)
    
    results = []
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n🔍 Testing {test_case['ramz_id']} ({i}/{len(test_cases)})...")
        
        try:
            result = await debug_with_playwright(test_case['url'], test_case['ramz_id'])
            results.append(result)
            
            print(f"✅ Completed {test_case['ramz_id']}")
            print(f"   Table data fields: {len(result.get('table_data', {}))}")
            
        except Exception as e:
            print(f"❌ Failed {test_case['ramz_id']}: {e}")
            results.append({
                'ramz_id': test_case['ramz_id'],
                'url': test_case['url'],
                'error': str(e),
                'table_data': {},
                'timestamp': datetime.now().isoformat()
            })
    
    # Save summary
    summary = {
        'test_run': datetime.now().isoformat(),
        'total_tested': len(test_cases),
        'results': results
    }
    
    with open('playwright_debug_summary.json', 'w', encoding='utf-8') as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)
    
    print(f"\n📊 SUMMARY:")
    print(f"   Tested: {len(test_cases)} URLs")
    print(f"   Results saved to: playwright_debug_summary.json")
    
    return results

if __name__ == "__main__":
    # Install playwright browsers if needed
    print("Installing Playwright browsers if needed...")
    import subprocess
    import sys
    
    try:
        subprocess.run([sys.executable, "-m", "playwright", "install", "chromium"], 
                      check=True, capture_output=True)
    except:
        pass  # Browsers might already be installed
    
    # Run the test
    asyncio.run(test_playwright_scraping())
