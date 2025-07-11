#!/usr/bin/env python3
"""
Corrected historical scores extraction method using values.php
"""

import asyncio
import json
import re
from playwright.async_api import async_playwright

async def extract_correct_historical_scores(ramz_id):
    """Extract correct historical scores using values.php endpoint"""
    
    values_url = f"https://guide-orientation.rnu.tn/ar/dynamique/values.php?id={ramz_id}"
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)  # Fast headless
        context = await browser.new_context()
        page = await context.new_page()
        
        try:
            print(f"🎯 Extracting scores for {ramz_id}...")
            
            # Go directly to values.php
            response = await page.goto(values_url, wait_until='networkidle', timeout=15000)
            
            if response.status == 200:
                content = await page.content()
                
                # Extract the body content which contains the scores
                body_match = re.search(r'<body>(.*?)</body>', content, re.DOTALL)
                if body_match:
                    scores_text = body_match.group(1).strip()
                    print(f"   Raw scores text: {scores_text}")
                    
                    # Parse the format: 2011/0/2012/0/2013/0/...2020/109.82251/2021/93.4883/...
                    historical_scores = {}
                    
                    # Split by '/' and process pairs
                    parts = scores_text.split('/')
                    
                    for i in range(0, len(parts) - 1, 2):
                        try:
                            year = parts[i]
                            score = parts[i + 1]
                            
                            # Validate year and score
                            year_int = int(year)
                            score_float = float(score)
                            
                            if 2010 <= year_int <= 2024:
                                # Only include non-zero scores
                                if score_float > 0:
                                    historical_scores[str(year_int)] = score_float
                                    print(f"   ✅ {year_int}: {score_float}")
                        
                        except (ValueError, IndexError):
                            continue
                    
                    await browser.close()
                    return historical_scores
                
            else:
                print(f"   ❌ Failed to get values.php: status {response.status}")
                
        except Exception as e:
            print(f"   ❌ Error extracting scores: {e}")
        
        await browser.close()
        return {}

async def test_multiple_ramz_scores():
    """Test the corrected extraction on multiple ramz codes"""
    
    print("🇹🇳 CORRECTED HISTORICAL SCORES EXTRACTION TEST")
    print("=" * 60)
    
    # Test with different ramz codes from finale.json
    test_ramz_codes = ["222103", "210209", "110101", "310102", "410101"]
    
    results = {}
    
    for ramz_id in test_ramz_codes:
        scores = await extract_correct_historical_scores(ramz_id)
        results[ramz_id] = scores
        
        if scores:
            print(f"✅ {ramz_id}: Found {len(scores)} valid scores")
        else:
            print(f"❌ {ramz_id}: No valid scores found")
        
        await asyncio.sleep(1)  # Small delay between requests
    
    print(f"\n📋 SUMMARY OF CORRECTED EXTRACTION:")
    for ramz_id, scores in results.items():
        print(f"\n🎯 RAMZ {ramz_id}:")
        if scores:
            for year, score in sorted(scores.items()):
                print(f"   {year}: {score}")
        else:
            print("   No scores available")
    
    # Compare with current finale.json data
    print(f"\n🔍 COMPARISON WITH CURRENT FINALE.JSON:")
    try:
        with open('data/finale.json', 'r', encoding='utf-8') as f:
            finale_data = json.load(f)
        
        for ramz_id in test_ramz_codes:
            current_record = None
            for record in finale_data:
                if record.get('ramz_id') == ramz_id:
                    current_record = record
                    break
            
            if current_record and 'historical_scores' in current_record:
                current_scores = current_record['historical_scores']
                new_scores = results.get(ramz_id, {})
                
                current_valid = sum(1 for score in current_scores.values() if 0 <= float(score) <= 220)
                new_valid = sum(1 for score in new_scores.values() if 0 <= float(score) <= 220)
                
                print(f"\n📊 {ramz_id}:")
                print(f"   Current valid scores: {current_valid}/{len(current_scores)}")
                print(f"   New valid scores: {new_valid}/{len(new_scores)}")
                
                if new_valid > current_valid:
                    print(f"   ✅ Improvement: +{new_valid - current_valid} valid scores")
                elif new_valid == current_valid and len(new_scores) < len(current_scores):
                    print(f"   ✅ Cleaner data: Removed {len(current_scores) - len(new_scores)} invalid scores")
                
    except Exception as e:
        print(f"❌ Error reading finale.json: {e}")
    
    return results

if __name__ == "__main__":
    asyncio.run(test_multiple_ramz_scores())
