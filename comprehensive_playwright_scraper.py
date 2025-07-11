#!/usr/bin/env python3
"""
Comprehensive Playwright scraper that handles JavaScript loading and values.php endpoint
"""

import asyncio
import json
import csv
import re
from playwright.async_api import async_playwright
from datetime import datetime

def parse_values_php(content):
    """Parse the values.php response to extract historical scores"""
    try:
        # Extract the body content
        if '<body>' in content and '</body>' in content:
            body = content.split('<body>')[1].split('</body>')[0]
        else:
            body = content
            
        # Parse the year/score pairs
        scores = {}
        if body.strip():
            # Split by '/' and group pairs
            parts = body.split('/')
            for i in range(0, len(parts)-1, 2):
                if i+1 < len(parts):
                    year = parts[i].strip()
                    score = parts[i+1].strip()
                    if year and score:
                        scores[year] = score
                        
        return scores
    except Exception as e:
        print(f"Error parsing values.php: {e}")
        return {}

async def extract_ramz_data(url, ramz_id):
    """Extract all data for a single ramz URL"""
    
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
        
        # Store network responses
        values_response = None
        
        async def handle_response(response):
            nonlocal values_response
            if 'values.php' in response.url:
                try:
                    values_response = await response.text()
                except:
                    pass
        
        page.on('response', handle_response)
        
        try:
            print(f"🌐 Loading {ramz_id}: {url}")
            
            # Navigate and wait for page to fully load
            await page.goto(url, wait_until='networkidle', timeout=30000)
            
            # Wait for JavaScript to populate data
            await page.wait_for_timeout(5000)
            
            # Extract main data
            data = {
                'ramz_id': ramz_id,
                'url': url,
                'university_name': '',
                'state_name': '',
                'institution_name': '',
                'institution_address': '',
                'institution_phone': '',
                'training_field': '',
                'specialization_code': '',
                'specialization_name': '',
                'specializations': '',
                'scale': '',
                'bac_type': '',
                'capacity_2025': '',
                'requires_test': '',
                'geographical_bonus_7_percent': '',
                'conditions': '',
                'study_duration': '',
                'last_oriented_score_2024': '',
                'historical_scores': {}
            }
            
            # Method 1: Extract from table structure
            try:
                rows = await page.query_selector_all('tr')
                for row in rows:
                    cells = await row.query_selector_all('td')
                    if len(cells) >= 2:
                        label_elem = cells[0]
                        value_elem = cells[1]
                        
                        label = await label_elem.inner_text()
                        value = await value_elem.inner_text()
                        
                        label = label.strip()
                        value = value.strip()
                        
                        # Map Arabic labels to our fields
                        if 'الجامعة' in label:
                            data['university_name'] = value
                        elif 'الولاية' in label:
                            data['state_name'] = value
                        elif 'المؤسسة' in label:
                            # Extract institution name, address, phone
                            lines = value.split('\\n')
                            if len(lines) >= 1:
                                data['institution_name'] = lines[0].strip()
                            if len(lines) >= 2:
                                data['institution_address'] = lines[1].replace('العنوان :', '').strip()
                            if len(lines) >= 3:
                                data['institution_phone'] = lines[2].replace('الهاتف :', '').strip()
                        elif 'مجال التكوين' in label:
                            data['training_field'] = value
                        elif 'رمز الشعبة' in label:
                            data['specialization_code'] = value
                        elif 'الشعبة / الإجازة' in label:
                            data['specialization_name'] = value
                        elif 'التخصصات' in label:
                            data['specializations'] = value
                        elif 'المقياس' in label:
                            data['scale'] = value
                        elif 'نوع الباكالوريا' in label:
                            data['bac_type'] = value
                        elif 'طاقة الإستعاب' in label:
                            data['capacity_2025'] = value
                        elif 'شعبة تتطلب إختبار' in label:
                            data['requires_test'] = value
                        elif 'التنفيل الجغرافي' in label:
                            data['geographical_bonus_7_percent'] = value
                        elif 'الشروط' in label:
                            data['conditions'] = value
                        elif 'مدة الدراسة' in label:
                            data['study_duration'] = value
                        elif 'مجموع آخر موجه 2024' in label:
                            data['last_oriented_score_2024'] = value
            except Exception as e:
                print(f"Error extracting table data: {e}")
            
            # Method 2: Try JavaScript evaluation to get data
            try:
                # Check if there are JavaScript variables we can access
                js_data = await page.evaluate("""
                    () => {
                        // Try to find data in global variables or DOM
                        const result = {};
                        
                        // Look for specific text content
                        const elements = document.querySelectorAll('td');
                        for (let td of elements) {
                            const text = td.textContent.trim();
                            if (text.includes('الجامعة')) {
                                const next = td.nextElementSibling;
                                if (next) result.university = next.textContent.trim();
                            }
                            if (text.includes('الولاية')) {
                                const next = td.nextElementSibling;
                                if (next) result.state = next.textContent.trim();
                            }
                            if (text.includes('المؤسسة')) {
                                const next = td.nextElementSibling;
                                if (next) result.institution = next.textContent.trim();
                            }
                            if (text.includes('الشعبة / الإجازة')) {
                                const next = td.nextElementSibling;
                                if (next) result.specialization = next.textContent.trim();
                            }
                        }
                        
                        return result;
                    }
                """)
                
                if js_data:
                    data['university_name'] = js_data.get('university', data['university_name'])
                    data['state_name'] = js_data.get('state', data['state_name'])
                    data['institution_name'] = js_data.get('institution', data['institution_name'])
                    data['specialization_name'] = js_data.get('specialization', data['specialization_name'])
                    
            except Exception as e:
                print(f"Error with JavaScript evaluation: {e}")
            
            # Extract historical scores from values.php
            if values_response:
                data['historical_scores'] = parse_values_php(values_response)
                print(f"📊 Extracted {len(data['historical_scores'])} historical scores")
            
            # If we didn't get values.php from the response, try direct request
            if not data['historical_scores']:
                try:
                    values_url = "https://guide-orientation.rnu.tn/ar/dynamique/values.php"
                    response = await page.goto(values_url, wait_until='networkidle', timeout=15000)
                    content = await page.content()
                    data['historical_scores'] = parse_values_php(content)
                    print(f"📊 Direct request: extracted {len(data['historical_scores'])} historical scores")
                except Exception as e:
                    print(f"Error with direct values.php request: {e}")
            
            print(f"✅ Extracted data for {ramz_id}")
            print(f"   University: {data['university_name']}")
            print(f"   State: {data['state_name']}")
            print(f"   Institution: {data['institution_name']}")
            print(f"   Specialization: {data['specialization_name']}")
            print(f"   7% bonus: {data['geographical_bonus_7_percent']}")
            print(f"   Historical scores: {len(data['historical_scores'])}")
            
            return data
            
        except Exception as e:
            print(f"❌ Error processing {ramz_id}: {e}")
            return {
                'ramz_id': ramz_id,
                'url': url,
                'error': str(e),
                'historical_scores': {}
            }
        finally:
            await browser.close()

async def test_comprehensive_extraction():
    """Test comprehensive extraction on sample URLs"""
    
    test_cases = [
        {'ramz_id': '110101', 'url': 'https://guide-orientation.rnu.tn/ar/dynamique/filiere.php?id=110101'},
        {'ramz_id': '210102', 'url': 'https://guide-orientation.rnu.tn/ar/dynamique/filiere.php?id=210102'},
        {'ramz_id': '310101', 'url': 'https://guide-orientation.rnu.tn/ar/dynamique/filiere.php?id=310101'}
    ]
    
    print("🎭 COMPREHENSIVE PLAYWRIGHT EXTRACTION")
    print("=" * 50)
    
    results = []
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n🔍 Processing {test_case['ramz_id']} ({i}/{len(test_cases)})...")
        
        result = await extract_ramz_data(test_case['url'], test_case['ramz_id'])
        results.append(result)
    
    # Save results
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Save JSON
    json_filename = f'tunisia_university_comprehensive_{timestamp}.json'
    with open(json_filename, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    
    # Save CSV
    csv_filename = f'tunisia_university_comprehensive_{timestamp}.csv'
    if results:
        # Flatten historical scores for CSV
        csv_data = []
        for result in results:
            row = result.copy()
            # Remove historical_scores dict and add individual year columns
            historical = row.pop('historical_scores', {})
            for year in range(2011, 2025):
                row[f'score_{year}'] = historical.get(str(year), '')
            csv_data.append(row)
        
        # Write CSV
        if csv_data:
            fieldnames = csv_data[0].keys()
            with open(csv_filename, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(csv_data)
    
    print(f"\n📊 COMPREHENSIVE EXTRACTION COMPLETE")
    print(f"   Results saved to:")
    print(f"   - {json_filename}")
    print(f"   - {csv_filename}")
    
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
        pass
    
    # Run the test
    asyncio.run(test_comprehensive_extraction())
