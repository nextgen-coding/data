#!/usr/bin/env python3
"""
Debug script to examine the HTML and JavaScript of ramz pages
"""

import requests
from bs4 import BeautifulSoup
import re

def analyze_ramz_page(url):
    """Analyze the HTML structure and JavaScript of a ramz page"""
    
    try:
        session = requests.Session()
        session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'ar,en;q=0.9',
        })
        
        response = session.get(url, timeout=10)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Save full HTML for inspection
        with open('debug_ramz_full.html', 'w', encoding='utf-8') as f:
            f.write(soup.prettify())
        
        print("🔍 HTML saved to debug_ramz_full.html")
        
        # Look for JavaScript files and inline scripts
        print("\n📋 JAVASCRIPT ANALYSIS:")
        
        # External JS files
        scripts = soup.find_all('script', src=True)
        print(f"External JavaScript files: {len(scripts)}")
        for script in scripts:
            src = script.get('src')
            print(f"  📄 {src}")
            
            # Try to fetch and analyze key JS files
            if 'data_graph.js' in src or 'values.php' in src:
                try:
                    js_url = f"https://guide-orientation.rnu.tn/{src.lstrip('../')}"
                    js_response = session.get(js_url, timeout=5)
                    if js_response.status_code == 200:
                        with open(f"debug_{src.split('/')[-1]}", 'w', encoding='utf-8') as f:
                            f.write(js_response.text)
                        print(f"    ✅ Downloaded {src.split('/')[-1]}")
                except Exception as e:
                    print(f"    ❌ Failed to download {src}: {e}")
        
        # Inline scripts
        inline_scripts = soup.find_all('script', src=False)
        print(f"\nInline JavaScript blocks: {len(inline_scripts)}")
        
        for i, script in enumerate(inline_scripts):
            if script.string and len(script.string.strip()) > 50:
                print(f"  📝 Inline script {i+1}: {len(script.string)} characters")
                
                # Look for specific patterns
                script_content = script.string
                
                # Look for AJAX calls
                if 'ajax' in script_content.lower() or 'xhr' in script_content.lower():
                    print(f"    🔍 Contains AJAX calls")
                
                # Look for data loading patterns
                if 'values.php' in script_content:
                    print(f"    🎯 References values.php")
                
                # Look for chart/graph data
                if 'chart' in script_content.lower() or 'highcharts' in script_content.lower():
                    print(f"    📊 Contains chart/graph code")
                
                # Save inline scripts for analysis
                with open(f"debug_inline_script_{i+1}.js", 'w', encoding='utf-8') as f:
                    f.write(script_content)
        
        # Look for div elements that might be populated by JS
        print(f"\n🎯 KEY ELEMENTS:")
        
        # Chart container
        chart_div = soup.find('div', id='chart')
        if chart_div:
            print(f"  📊 Chart div found: {chart_div}")
        
        # Look for empty table cells that might be filled by JS
        empty_cells = soup.find_all('b')
        empty_count = sum(1 for cell in empty_cells if not cell.get_text().strip())
        print(f"  📋 Empty <b> tags: {empty_count} (likely filled by JavaScript)")
        
        # Look for specific patterns in URLs or forms
        text_content = soup.get_text()
        if 'values.php' in text_content:
            print(f"  🔍 Text mentions values.php")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def main():
    # Test with a specific ramz URL
    test_url = "https://guide-orientation.rnu.tn/ar/dynamique/filiere.php?id=110101"
    print(f"🔍 Analyzing ramz page: {test_url}")
    analyze_ramz_page(test_url)
    
    print(f"\n📁 Files created for analysis:")
    print(f"  - debug_ramz_full.html (full page HTML)")
    print(f"  - debug_inline_script_*.js (inline JavaScript)")
    print(f"  - debug_data_graph.js (if available)")

if __name__ == "__main__":
    main()
