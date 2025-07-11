#!/usr/bin/env python3
"""
Playwright-based scraper to debug and extract correct data
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
        # Launch browser with real user behavior
        browser = await p.chromium.launch(
            headless=False,  # Keep visible for debugging
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
        
        # Navigate to page
        await page.goto(url, wait_until='networkidle')
        
        # Wait for potential JavaScript to load
        await page.wait_for_timeout(5000)
        
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
        try:
            # Find all table rows
            rows = await page.query_selector_all('tr')
            print(f"Found {len(rows)} table rows")
            
            for i, row in enumerate(rows):
                cells = await row.query_selector_all('td')
                if len(cells) >= 2:
                    label_element = cells[0]
                    value_element = cells[1]
                    
                    label = await label_element.inner_text()
                    value = await value_element.inner_text()
                    
                    label = label.strip()
                    value = value.strip()
                    
                    if label and label != value:
                        table_data[label] = value
                        print(f"  Row {i}: '{label}' -> '{value}'")
        
        except Exception as e:
            print(f"Error extracting table data: {e}")
        
        # Check for values.php requests
        values_requests = [r for r in requests_log if 'values.php' in r['url']]
        print(f"📊 Found {len(values_requests)} values.php requests:")
        for req in values_requests:
            print(f"  {req['method']} {req['url']}")
        
        # Try to get values.php data manually
        values_url = f"https://guide-orientation.rnu.tn/ar/dynamique/values.php"
        print(f"🎯 Testing values.php endpoint...")
        
        try:
            # Navigate to values.php in the same session
            values_response = await page.goto(values_url, wait_until='networkidle')
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
        
        await browser.close()
        
        return debug_info

async def test_playwright_scraping():
    """Test Playwright scraping on a few sample URLs"""
    
    test_urls = [
        {
            'ramz_id': '110101',
            'url': 'https://guide-orientation.rnu.tn/ar/dynamique/filiere.php?id=110101'
        },
        {
            'ramz_id': '220518', 
            'url': 'https://guide-orientation.rnu.tn/ar/dynamique/filiere.php?id=220518'
        },
        {
            'ramz_id': '310101',
            'url': 'https://guide-orientation.rnu.tn/ar/dynamique/filiere.php?id=310101'
        }
    ]
    
    print("🎭 PLAYWRIGHT DEBUG SESSION")
    print("=" * 50)
    
    results = []
    
    for test_case in test_urls:
        print(f"\n🔍 Testing {test_case['ramz_id']}...")
        
        result = await debug_with_playwright(test_case['url'], test_case['ramz_id'])
        results.append(result)
        
        print(f"✅ Completed {test_case['ramz_id']}")
        print(f"   Table data fields: {len(result['table_data'])}")
        print(f"   Network requests: {result['requests_count']}")
        
        # Wait between tests
        await asyncio.sleep(2)
    
    # Save combined results
    with open('playwright_debug_results.json', 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    
    print(f"\n📊 SUMMARY:")
    print(f"   Tested {len(results)} URLs")
    print(f"   Debug files generated for each test")
    print(f"   Combined results: playwright_debug_results.json")
    
    return results

if __name__ == "__main__":
    # Install playwright if needed
    print("Installing Playwright browsers if needed...")
    import subprocess
    try:
        subprocess.run(['playwright', 'install', 'chromium'], check=True, capture_output=True)
    except:
        print("Note: Run 'playwright install chromium' if you get browser errors")
    
    # Run the debug session
    asyncio.run(test_playwright_scraping())
