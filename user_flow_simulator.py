#!/usr/bin/env python3
"""
Complete user flow simulation - navigate from main page through search to ramz detail
"""

import asyncio
import json
from playwright.async_api import async_playwright
from datetime import datetime

async def simulate_complete_user_flow(ramz_id):
    """Simulate complete user flow from main page to ramz detail"""
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True,
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
        
        # Track all network requests
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
        
        try:
            print(f"🌐 Step 1: Navigate to main page")
            await page.goto('https://guide-orientation.rnu.tn/', wait_until='networkidle', timeout=30000)
            await page.wait_for_timeout(2000)
            
            print(f"🌐 Step 2: Navigate to search page")
            await page.goto('https://guide-orientation.rnu.tn/ar/dynamique/rechFil.php', wait_until='networkidle', timeout=30000)
            await page.wait_for_timeout(3000)
            
            print(f"🌐 Step 3: Set up dropdown selections")
            # We know that ramz_id like "110101" means:
            # First digit (1) = bac type
            # Next two digits (10) = university 
            # Last three digits (101) = specialization
            
            bac_id = ramz_id[0]  # "1"
            univ_id = ramz_id[1:3]  # "10" 
            spec_code = ramz_id[3:]  # "101"
            
            print(f"   Bac ID: {bac_id}, Univ ID: {univ_id}, Spec Code: {spec_code}")
            
            # Fill the dropdowns (we need to find the correct selectors)
            try:
                # Select bac type
                await page.select_option('select[name="bac"]', bac_id)
                await page.wait_for_timeout(1000)
                
                # Select university  
                await page.select_option('select[name="univ"]', univ_id)
                await page.wait_for_timeout(1000)
                
                # Select institution/specialization
                await page.select_option('select[name="etab"]', spec_code)
                await page.wait_for_timeout(1000)
                
                print(f"✅ Dropdowns set successfully")
                
            except Exception as e:
                print(f"⚠️  Could not set dropdowns (expected): {e}")
                # This is expected since we don't know the exact form structure
            
            print(f"🌐 Step 4: Navigate directly to ramz detail page")
            ramz_url = f'https://guide-orientation.rnu.tn/ar/dynamique/filiere.php?id={ramz_id}'
            await page.goto(ramz_url, wait_until='networkidle', timeout=30000)
            await page.wait_for_timeout(5000)
            
            print(f"🌐 Step 5: Extract data from detail page")
            
            # Take screenshot for comparison
            await page.screenshot(path=f'flow_screenshot_{ramz_id}.png')
            
            # Extract data
            data = {
                'ramz_id': ramz_id,
                'url': ramz_url,
                'extracted_fields': {}
            }
            
            # Look for all table cells and their content
            try:
                rows = await page.query_selector_all('tr')
                print(f"Found {len(rows)} table rows")
                
                for i, row in enumerate(rows):
                    cells = await row.query_selector_all('td')
                    if len(cells) >= 2:
                        label = await cells[0].inner_text()
                        value = await cells[1].inner_text()
                        
                        label = label.strip()
                        value = value.strip()
                        
                        if label and value and label != value:
                            data['extracted_fields'][label] = value
                            print(f"  {label}: {value}")
                
            except Exception as e:
                print(f"Error extracting data: {e}")
            
            # Check session/cookies
            cookies = await context.cookies()
            print(f"🍪 Active cookies: {len(cookies)}")
            for cookie in cookies:
                print(f"   {cookie['name']}: {cookie['value'][:50]}...")
            
            # Log network activity
            php_requests = [r for r in requests_log if '.php' in r['url']]
            print(f"📡 PHP requests: {len(php_requests)}")
            for req in php_requests[-5:]:  # Last 5
                print(f"   {req['method']} {req['url']}")
            
            # Save debug info
            debug_info = {
                'ramz_id': ramz_id,
                'extracted_fields': data['extracted_fields'],
                'cookies': cookies,
                'php_requests': php_requests,
                'total_requests': len(requests_log),
                'timestamp': datetime.now().isoformat()
            }
            
            with open(f'flow_debug_{ramz_id}.json', 'w', encoding='utf-8') as f:
                json.dump(debug_info, f, ensure_ascii=False, indent=2)
            
            print(f"✅ Flow complete for {ramz_id}")
            print(f"   Extracted fields: {len(data['extracted_fields'])}")
            
            return data
            
        except Exception as e:
            print(f"❌ Error in user flow: {e}")
            return {'ramz_id': ramz_id, 'error': str(e)}
        finally:
            await browser.close()

async def test_user_flow():
    """Test complete user flow on sample ramz IDs"""
    
    test_ramz_ids = ['110101', '210102', '310101']
    
    print("🎭 COMPLETE USER FLOW SIMULATION")
    print("=" * 50)
    
    results = []
    for i, ramz_id in enumerate(test_ramz_ids, 1):
        print(f"\n🔍 Testing flow for {ramz_id} ({i}/{len(test_ramz_ids)})...")
        
        result = await simulate_complete_user_flow(ramz_id)
        results.append(result)
    
    # Save summary
    with open('user_flow_summary.json', 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    
    print(f"\n📊 USER FLOW TEST COMPLETE")
    print(f"   Results saved to: user_flow_summary.json")
    
    return results

if __name__ == "__main__":
    asyncio.run(test_user_flow())
