#!/usr/bin/env python3
"""
Test script to extract correct historical scores for ramz_id 222103
"""

import asyncio
import json
from playwright.async_api import async_playwright
import re

async def parse_values_response(content, ramz_id):
    """Parse values.php response content and extract historical scores"""
    scores = {}
    
    print(f"🔍 Parsing values.php content for {ramz_id}...")
    print(f"📄 Content type: {type(content)}")
    print(f"📄 Content length: {len(content) if content else 0}")
    
    if not content or not content.strip():
        print("❌ Empty content")
        return scores
    
    try:
        # Method 1: Try to parse as JSON
        try:
            values_data = json.loads(content)
            print(f"✅ Parsed as JSON: {values_data}")
            
            # Handle different JSON structures
            if isinstance(values_data, list) and len(values_data) >= 2:
                years = values_data[0] if isinstance(values_data[0], list) else []
                score_values = values_data[1] if isinstance(values_data[1], list) else []
                
                for year, score in zip(years, score_values):
                    if score and score != 0:
                        scores[str(year)] = float(score)
                        
            elif isinstance(values_data, dict):
                # Handle direct year:score mapping
                for year, score in values_data.items():
                    try:
                        year_int = int(year)
                        score_float = float(score)
                        if 2010 <= year_int <= 2024 and 0 <= score_float <= 220:
                            scores[str(year_int)] = score_float
                    except:
                        continue
                        
            print(f"📊 JSON parsing result: {scores}")
            
        except json.JSONDecodeError:
            print("📄 Not valid JSON, trying other formats...")
            
            # Method 2: Parse as delimited text (like "2020/109.82251/2021/93.4883/")
            if '/' in content:
                parts = content.strip().split('/')
                print(f"📄 Found {len(parts)} parts in delimited format")
                
                # Parse pairs of year/score
                for i in range(0, len(parts) - 1, 2):
                    try:
                        year = parts[i].strip()
                        score = parts[i + 1].strip()
                        
                        year_int = int(year)
                        score_float = float(score)
                        
                        if 2010 <= year_int <= 2024 and 0 <= score_float <= 220:
                            scores[str(year_int)] = score_float
                            print(f"   ✅ {year_int}: {score_float}")
                            
                    except (ValueError, IndexError) as e:
                        print(f"   ❌ Failed to parse pair {i//2 + 1}: {e}")
                        continue
            
            # Method 3: Parse as comma-separated values
            elif ',' in content:
                # Try different CSV formats
                lines = content.strip().split('\n')
                for line in lines:
                    if ',' in line:
                        parts = line.split(',')
                        if len(parts) >= 2:
                            try:
                                year = int(parts[0].strip())
                                score = float(parts[1].strip())
                                
                                if 2010 <= year <= 2024 and 0 <= score <= 220:
                                    scores[str(year)] = score
                                    
                            except:
                                continue
            
            # Method 4: Look for year:score patterns in text
            else:
                patterns = [
                    r'(\d{4})[^\d]*?(\d+\.?\d*)',  # Year followed by score
                    r'"(\d{4})"\s*:\s*(\d+\.?\d*)',  # JSON-like year:score
                    r'(\d{4})\s*[=:]\s*(\d+\.?\d*)',  # Year = or : score
                ]
                
                for pattern in patterns:
                    matches = re.findall(pattern, content)
                    print(f"📄 Pattern '{pattern}' found {len(matches)} matches")
                    
                    for match in matches:
                        try:
                            year, score = match
                            year_int = int(year)
                            score_float = float(score)
                            
                            if 2010 <= year_int <= 2024 and 0 <= score_float <= 220:
                                scores[str(year_int)] = score_float
                                print(f"   ✅ Pattern match: {year_int}: {score_float}")
                                
                        except:
                            continue
    
    except Exception as e:
        print(f"❌ Error parsing values.php content: {e}")
    
    print(f"🎯 Final parsed scores: {scores}")
    return scores

async def test_historical_scores_extraction(ramz_id):
    """Test extracting historical scores for a specific ramz_id"""
    
    ramz_url = f"https://guide-orientation.rnu.tn/ar/dynamique/filiere.php?id={ramz_id}"
    print(f"🎯 Testing historical scores extraction for ramz_id: {ramz_id}")
    print(f"🔗 URL: {ramz_url}")
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)  # Fast headless mode
        context = await browser.new_context(
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36'
        )
        
        page = await context.new_page()
        
        # Track network requests to find values.php
        network_requests = []
        def log_request(request):
            network_requests.append({
                'url': request.url,
                'method': request.method
            })
        page.on('request', log_request)
        
        try:
            print("📄 Navigating to ramz page...")
            await page.goto(ramz_url, wait_until='networkidle', timeout=15000)
            await page.wait_for_timeout(2000)  # Reduced wait time
            
            # Take screenshot for debugging
            await page.screenshot(path=f'debug_scores_{ramz_id}.png')
            
            print("🔍 Method 1: Looking for chart data in JavaScript...")
            
            # Method 1: Try to get chart data from JavaScript
            try:
                await page.wait_for_function('window.myChart && window.myChart.data', timeout=5000)
                chart_data = await page.evaluate('window.myChart.data.datasets[0].data')
                chart_labels = await page.evaluate('window.myChart.data.labels')
                
                print(f"✅ Found chart data!")
                print(f"   Labels: {chart_labels}")
                print(f"   Data: {chart_data}")
                
                historical_scores = {}
                for year, score in zip(chart_labels, chart_data):
                    if score and score != 0:
                        historical_scores[str(year)] = float(score)
                
                print(f"📊 Method 1 - Chart data scores: {historical_scores}")
                
            except Exception as e:
                print(f"❌ Method 1 failed: {e}")
                historical_scores = {}
            
            print("\n🔍 Method 2: Looking for values.php requests...")
            
            # Method 2: Check for values.php requests
            values_requests = [req for req in network_requests if 'values.php' in req['url']]
            print(f"📊 Found {len(values_requests)} values.php requests:")
            for req in values_requests:
                print(f"   {req['method']} {req['url']}")
            
            print("\n🔍 Method 3: Multiple approaches to access values.php...")
            
            # Method 3A: Try to access values.php directly with ramz_id
            values_url = f"https://guide-orientation.rnu.tn/ar/dynamique/values.php?id={ramz_id}"
            print(f"🎯 Method 3A - Direct access: {values_url}")
            
            try:
                values_response = await page.goto(values_url, wait_until='networkidle')
                values_content = await page.content()
                
                print(f"📄 Values.php response status: {values_response.status}")
                print(f"📄 Values.php content preview: {values_content[:300]}")
                
                # Save the values.php response for analysis
                with open(f'debug_values_response_{ramz_id}.txt', 'w', encoding='utf-8') as f:
                    f.write(values_content)
                
                # Parse different formats from values.php
                method3a_scores = await parse_values_response(values_content, ramz_id)
                print(f"📊 Method 3A scores: {method3a_scores}")
                
            except Exception as e:
                print(f"❌ Method 3A failed: {e}")
                method3a_scores = {}
            
            # Method 3B: Use fetch API from the ramz page context
            print(f"\n🎯 Method 3B - Fetch from page context...")
            try:
                # Go back to the ramz page first
                await page.goto(ramz_url, wait_until='networkidle')
                await page.wait_for_timeout(1000)  # Reduced wait time
                
                # Use fetch API to get values.php data from the page context
                fetch_result = await page.evaluate(f"""
                    async () => {{
                        try {{
                            const response = await fetch('/ar/dynamique/values.php?id={ramz_id}');
                            const text = await response.text();
                            return {{
                                status: response.status,
                                content: text,
                                url: response.url
                            }};
                        }} catch (error) {{
                            return {{
                                error: error.message
                            }};
                        }}
                    }}
                """)
                
                print(f"📄 Fetch result: {fetch_result}")
                
                if 'content' in fetch_result:
                    method3b_scores = await parse_values_response(fetch_result['content'], ramz_id)
                    print(f"📊 Method 3B scores: {method3b_scores}")
                else:
                    method3b_scores = {}
                
            except Exception as e:
                print(f"❌ Method 3B failed: {e}")
                method3b_scores = {}
            
            # Method 3C: Try POST request to values.php
            print(f"\n🎯 Method 3C - POST request...")
            try:
                post_result = await page.evaluate(f"""
                    async () => {{
                        try {{
                            const formData = new FormData();
                            formData.append('id', '{ramz_id}');
                            
                            const response = await fetch('/ar/dynamique/values.php', {{
                                method: 'POST',
                                body: formData
                            }});
                            const text = await response.text();
                            return {{
                                status: response.status,
                                content: text,
                                url: response.url
                            }};
                        }} catch (error) {{
                            return {{
                                error: error.message
                            }};
                        }}
                    }}
                """)
                
                print(f"📄 POST result: {post_result}")
                
                if 'content' in post_result:
                    method3c_scores = await parse_values_response(post_result['content'], ramz_id)
                    print(f"📊 Method 3C scores: {method3c_scores}")
                else:
                    method3c_scores = {}
                    
            except Exception as e:
                print(f"❌ Method 3C failed: {e}")
                method3c_scores = {}
            
            # Method 3D: Look for AJAX calls in network tab
            print(f"\n🎯 Method 3D - Monitor AJAX calls...")
            try:
                # Go back to ramz page and monitor network
                ajax_data = []
                
                def capture_response(response):
                    if 'values.php' in response.url:
                        ajax_data.append({
                            'url': response.url,
                            'status': response.status
                        })
                
                page.on('response', capture_response)
                
                # Reload the page to trigger AJAX calls
                await page.goto(ramz_url, wait_until='networkidle')
                await page.wait_for_timeout(5000)
                
                print(f"📊 Captured AJAX calls to values.php: {len(ajax_data)}")
                for call in ajax_data:
                    print(f"   {call}")
                
                # Try to get the response content
                if ajax_data:
                    for call in ajax_data:
                        try:
                            ajax_response = await page.goto(call['url'], wait_until='networkidle')
                            ajax_content = await page.content()
                            
                            print(f"� AJAX response content preview: {ajax_content[:200]}")
                            
                            method3d_scores = await parse_values_response(ajax_content, ramz_id)
                            print(f"📊 Method 3D scores: {method3d_scores}")
                            break
                            
                        except Exception as e:
                            print(f"❌ Failed to get AJAX response: {e}")
                            continue
                else:
                    method3d_scores = {}
                    
            except Exception as e:
                print(f"❌ Method 3D failed: {e}")
                method3d_scores = {}
            
            # Combine all Method 3 results
            all_method3_scores = {}
            for scores in [method3a_scores, method3b_scores, method3c_scores, method3d_scores]:
                if scores:
                    all_method3_scores.update(scores)
                    
            print(f"📊 Combined Method 3 scores: {all_method3_scores}")
            
            print("\n🔍 Method 4: Looking for score data in page content...")
            
            # Method 4: Search page content for score patterns
            page_content = await page.content()
            
            # Save page content for analysis
            with open(f'debug_page_content_{ramz_id}.html', 'w', encoding='utf-8') as f:
                f.write(page_content)
            
            # Look for various score patterns
            score_patterns = [
                r'data:\s*\[([^\]]+)\]',  # Chart data array
                r'labels:\s*\[([^\]]+)\]',  # Chart labels array
                r'(\d{4})[^\d]*?(\d+\.?\d*)',  # Year followed by score
                r'"(\d{4})"\s*:\s*(\d+\.?\d*)',  # JSON-like year:score
            ]
            
            method4_scores = {}
            for pattern in score_patterns:
                matches = re.findall(pattern, page_content)
                if matches:
                    print(f"📊 Found pattern matches for '{pattern[:30]}...': {len(matches)} matches")
                    for match in matches[:5]:  # Show first 5 matches
                        print(f"   Match: {match}")
                        
                        if len(match) == 2:
                            try:
                                year, score = match
                                year = int(year)
                                score = float(score)
                                if 2010 <= year <= 2024 and 0 <= score <= 220:
                                    method4_scores[str(year)] = score
                            except:
                                continue
            
            print(f"📊 Method 4 - page content scores: {method4_scores}")
            
            print(f"\n📋 SUMMARY FOR RAMZ_ID {ramz_id}:")
            print(f"   Method 1 (Chart): {len(historical_scores)} scores")
            print(f"   Method 3 (values.php): {len(all_method3_scores)} scores")
            print(f"   Method 4 (page content): {len(method4_scores)} scores")
            
            # Return the best method's results (prioritize Method 3 - values.php)
            if all_method3_scores:
                print(f"✅ Using Method 3 (values.php) results")
                return all_method3_scores
            elif historical_scores:
                print(f"✅ Using Method 1 (Chart) results")
                return historical_scores
            elif method4_scores:
                print(f"✅ Using Method 4 (page content) results")
                return method4_scores
            else:
                print("❌ No valid scores found from any method")
                return {}
                
        except Exception as e:
            print(f"❌ Error testing ramz_id {ramz_id}: {e}")
            return {}
        
        finally:
            await browser.close()

async def main():
    """Main test function"""
    print("🇹🇳 HISTORICAL SCORES EXTRACTION TEST")
    print("=" * 50)
    
    # Test ramz_id 222103 as requested
    ramz_id = "222103"
    
    scores = await test_historical_scores_extraction(ramz_id)
    
    print(f"\n🎯 FINAL RESULT FOR {ramz_id}:")
    if scores:
        print(f"✅ Successfully extracted {len(scores)} historical scores:")
        for year, score in sorted(scores.items()):
            print(f"   {year}: {score}")
    else:
        print("❌ No valid scores extracted")
    
    # Compare with current finale.json data
    print(f"\n🔍 COMPARISON WITH CURRENT DATA:")
    try:
        with open('data/finale.json', 'r', encoding='utf-8') as f:
            finale_data = json.load(f)
        
        # Find the record for ramz_id 222103
        current_record = None
        for record in finale_data:
            if record.get('ramz_id') == ramz_id:
                current_record = record
                break
        
        if current_record and 'historical_scores' in current_record:
            current_scores = current_record['historical_scores']
            print(f"📊 Current scores in finale.json:")
            for year, score in sorted(current_scores.items()):
                print(f"   {year}: {score}")
            
            print(f"\n📈 SCORE VALIDATION:")
            valid_current = sum(1 for score in current_scores.values() if 0 <= float(score) <= 220)
            print(f"   Current valid scores (0-220): {valid_current}/{len(current_scores)}")
            
            if scores:
                valid_new = sum(1 for score in scores.values() if 0 <= float(score) <= 220)
                print(f"   New extracted valid scores (0-220): {valid_new}/{len(scores)}")
        
    except Exception as e:
        print(f"❌ Error reading finale.json: {e}")

if __name__ == "__main__":
    asyncio.run(main())
