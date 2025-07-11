#!/usr/bin/env python3
"""
Test script to discover the correct data loading endpoint
"""

import requests
import json
from urllib.parse import urlparse, parse_qs

def test_values_endpoint(ramz_id):
    """Test accessing the values.php endpoint directly"""
    
    session = requests.Session()
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Accept': 'application/json, text/javascript, */*; q=0.01',
        'Accept-Language': 'ar,en;q=0.9',
        'X-Requested-With': 'XMLHttpRequest',
        'Referer': f'https://guide-orientation.rnu.tn/ar/dynamique/filiere.php?id={ramz_id}'
    })
    
    # Test different possible endpoints
    endpoints = [
        f'https://guide-orientation.rnu.tn/ar/dynamique/values.php?id={ramz_id}',
        f'https://guide-orientation.rnu.tn/ar/dynamique/values.php',
        f'https://guide-orientation.rnu.tn/dynamique/values.php?id={ramz_id}',
        f'https://guide-orientation.rnu.tn/values.php?id={ramz_id}',
        f'https://guide-orientation.rnu.tn/ar/dynamique/data.php?id={ramz_id}',
        f'https://guide-orientation.rnu.tn/ar/ajax/get_data.php?id={ramz_id}',
    ]
    
    print(f"🔍 Testing data endpoints for ramz_id: {ramz_id}")
    
    for endpoint in endpoints:
        try:
            print(f"\n📡 Testing: {endpoint}")
            response = session.get(endpoint, timeout=10)
            
            print(f"  Status: {response.status_code}")
            print(f"  Content-Type: {response.headers.get('Content-Type', 'N/A')}")
            print(f"  Content Length: {len(response.content)} bytes")
            
            if response.status_code == 200:
                content = response.text
                print(f"  Preview: {content[:200]}...")
                
                # Try to parse as JSON
                try:
                    data = response.json()
                    print(f"  ✅ Valid JSON response with {len(data)} items")
                    
                    # Save the response for analysis
                    filename = f"debug_values_response_{ramz_id}.json"
                    with open(filename, 'w', encoding='utf-8') as f:
                        json.dump(data, f, ensure_ascii=False, indent=2)
                    print(f"  📁 Saved to {filename}")
                    
                    return endpoint, data
                    
                except json.JSONDecodeError:
                    print(f"  📄 Not JSON, content type: text")
                    if len(content) < 1000:  # Save small responses
                        filename = f"debug_values_response_{ramz_id}.txt"
                        with open(filename, 'w', encoding='utf-8') as f:
                            f.write(content)
                        print(f"  📁 Saved to {filename}")
            
        except Exception as e:
            print(f"  ❌ Error: {e}")
    
    return None, None

def test_page_source_data(ramz_id):
    """Check if data is embedded in the page source"""
    
    try:
        session = requests.Session()
        session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        })
        
        url = f'https://guide-orientation.rnu.tn/ar/dynamique/filiere.php?id={ramz_id}'
        response = session.get(url, timeout=10)
        
        if response.status_code == 200:
            content = response.text
            
            # Look for embedded JSON data
            import re
            
            # Look for various data patterns
            patterns = [
                r'var\s+data\s*=\s*(\[.*?\]);',
                r'chart.*?data\s*:\s*(\[.*?\])',
                r'series\s*:\s*\[\s*{\s*data\s*:\s*(\[.*?\])',
                r'(\[\s*\{.*?score.*?\}\s*\])',
            ]
            
            print(f"\n🔍 Looking for embedded data in page source...")
            
            for i, pattern in enumerate(patterns):
                matches = re.findall(pattern, content, re.DOTALL | re.IGNORECASE)
                if matches:
                    print(f"  ✅ Pattern {i+1} found {len(matches)} matches")
                    for j, match in enumerate(matches):
                        try:
                            data = json.loads(match)
                            filename = f"debug_embedded_data_{ramz_id}_pattern_{i+1}_{j+1}.json"
                            with open(filename, 'w', encoding='utf-8') as f:
                                json.dump(data, f, ensure_ascii=False, indent=2)
                            print(f"    📁 Saved match {j+1} to {filename}")
                            return match
                        except json.JSONDecodeError:
                            print(f"    ❌ Match {j+1} not valid JSON")
                            
            # Look for historical scores in a different format
            score_pattern = r'(20\d{2})[^\d]*(\d+(?:\.\d+)?)'
            score_matches = re.findall(score_pattern, content)
            if score_matches:
                print(f"  📊 Found {len(score_matches)} potential year-score pairs")
                scores = {year: float(score) for year, score in score_matches if len(score) > 2}
                if scores:
                    filename = f"debug_scores_{ramz_id}.json"
                    with open(filename, 'w', encoding='utf-8') as f:
                        json.dump(scores, f, ensure_ascii=False, indent=2)
                    print(f"    📁 Saved scores to {filename}")
                    return scores
                    
    except Exception as e:
        print(f"❌ Error analyzing page source: {e}")
    
    return None

def main():
    # Test with a specific ramz_id
    test_ramz_id = "110101"
    
    print("🎯 TUNISIA UNIVERSITY DATA ENDPOINT DISCOVERY")
    print("=" * 60)
    
    # Test 1: Try various endpoints
    endpoint, data = test_values_endpoint(test_ramz_id)
    
    # Test 2: Look for embedded data in page source
    embedded_data = test_page_source_data(test_ramz_id)
    
    print(f"\n📋 SUMMARY:")
    if endpoint:
        print(f"  ✅ Working endpoint: {endpoint}")
    else:
        print(f"  ❌ No working API endpoint found")
    
    if embedded_data:
        print(f"  ✅ Found embedded data in page source")
    else:
        print(f"  ❌ No embedded data found")
    
    if not endpoint and not embedded_data:
        print(f"\n💡 RECOMMENDATION:")
        print(f"  The data might be loaded via JavaScript after page load.")
        print(f"  Consider using Selenium with JavaScript execution.")

if __name__ == "__main__":
    main()
