#!/usr/bin/env python3
"""
Script to investigate PHP endpoints and data loading mechanisms
"""

import requests
import json
import time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
import re

def check_php_endpoints(ramz_id):
    """Check various PHP endpoints that might provide data"""
    
    base_url = "https://guide-orientation.rnu.tn/ar/dynamique/"
    endpoints_to_check = [
        f"values.php?id={ramz_id}",
        f"values.php?ramz={ramz_id}",
        f"filiere.php?id={ramz_id}",
        f"data.php?id={ramz_id}",
        f"get_data.php?id={ramz_id}",
        f"specialization.php?id={ramz_id}",
        "values.php",
        "data.php",
        "get_specialization.php"
    ]
    
    session = requests.Session()
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Accept': 'application/json, text/plain, */*',
        'Accept-Language': 'ar,en;q=0.9',
        'Referer': f'https://guide-orientation.rnu.tn/ar/dynamique/filiere.php?id={ramz_id}',
        'X-Requested-With': 'XMLHttpRequest'
    })
    
    print(f"🔍 Checking PHP endpoints for ramz_id: {ramz_id}")
    
    results = {}
    for endpoint in endpoints_to_check:
        try:
            url = base_url + endpoint
            print(f"  Testing: {url}")
            
            response = session.get(url, timeout=10)
            
            results[endpoint] = {
                'status_code': response.status_code,
                'content_type': response.headers.get('content-type', ''),
                'content_length': len(response.content),
                'content_preview': response.text[:200] if response.text else '',
                'has_json': False,
                'has_scores': False
            }
            
            # Check if response contains JSON
            try:
                json_data = response.json()
                results[endpoint]['has_json'] = True
                results[endpoint]['json_data'] = json_data
                print(f"    ✅ JSON response: {json_data}")
            except:
                pass
            
            # Check if response contains score data
            if re.search(r'20\d{2}.*\d+\.\d+', response.text):
                results[endpoint]['has_scores'] = True
                print(f"    📊 Contains score data")
            
            # Check for specific patterns
            if 'الجامعة' in response.text:
                print(f"    🏛️ Contains university data")
            if 'الشعبة' in response.text:
                print(f"    📚 Contains specialization data")
                
            print(f"    Status: {response.status_code}, Length: {len(response.content)}")
            
        except Exception as e:
            results[endpoint] = {'error': str(e)}
            print(f"    ❌ Error: {e}")
    
    return results

def analyze_javascript_requests(ramz_id):
    """Use Selenium to monitor network requests and JavaScript execution"""
    
    print(f"\n🕸️ Analyzing JavaScript requests for ramz_id: {ramz_id}")
    
    chrome_options = Options()
    chrome_options.add_argument('--enable-logging')
    chrome_options.add_argument('--log-level=0')
    chrome_options.add_argument('--disable-blink-features=AutomationControlled')
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option('useAutomationExtension', False)
    
    # Enable performance logging to capture network requests
    chrome_options.add_experimental_option('perfLoggingPrefs', {
        'enableNetwork': True,
        'enablePage': False,
    })
    chrome_options.set_capability('goog:loggingPrefs', {
        'performance': 'ALL',
        'browser': 'ALL'
    })
    
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)
    
    try:
        url = f"https://guide-orientation.rnu.tn/ar/dynamique/filiere.php?id={ramz_id}"
        print(f"  Loading: {url}")
        
        driver.get(url)
        
        # Wait for page to load
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.TAG_NAME, "table"))
        )
        
        # Wait for potential AJAX calls
        time.sleep(5)
        
        # Get performance logs to see network requests
        logs = driver.get_log('performance')
        network_requests = []
        
        for log in logs:
            message = json.loads(log['message'])
            if message['message']['method'] == 'Network.requestWillBeSent':
                request_url = message['message']['params']['request']['url']
                if 'php' in request_url or 'values' in request_url or 'data' in request_url:
                    network_requests.append(request_url)
                    print(f"    📡 Network request: {request_url}")
        
        # Check for JavaScript variables with data
        js_data = driver.execute_script("""
            var data = {};
            
            // Check for common variable names that might contain data
            var varsToCheck = ['chartData', 'scores', 'historicalData', 'specialization', 'university'];
            for (var i = 0; i < varsToCheck.length; i++) {
                var varName = varsToCheck[i];
                if (typeof window[varName] !== 'undefined') {
                    data[varName] = window[varName];
                }
            }
            
            // Check if Highcharts has data
            if (typeof Highcharts !== 'undefined' && Highcharts.charts && Highcharts.charts.length > 0) {
                var chart = Highcharts.charts[0];
                if (chart && chart.series && chart.series.length > 0) {
                    data.highchartsData = chart.series[0].data.map(function(point) {
                        return {year: point.category || point.name, score: point.y};
                    });
                }
            }
            
            return data;
        """)
        
        print(f"    📊 JavaScript data found: {list(js_data.keys())}")
        for key, value in js_data.items():
            print(f"      {key}: {str(value)[:100]}{'...' if len(str(value)) > 100 else ''}")
        
        # Save page source for analysis
        with open(f'selenium_page_source_{ramz_id}.html', 'w', encoding='utf-8') as f:
            f.write(driver.page_source)
        
        # Check if table cells are populated
        table_cells = driver.find_elements(By.CSS_SELECTOR, "table b")
        empty_cells = 0
        filled_cells = 0
        
        for cell in table_cells:
            if cell.text.strip():
                filled_cells += 1
            else:
                empty_cells += 1
        
        print(f"    📋 Table analysis: {filled_cells} filled cells, {empty_cells} empty cells")
        
        return {
            'network_requests': network_requests,
            'js_data': js_data,
            'filled_cells': filled_cells,
            'empty_cells': empty_cells
        }
        
    finally:
        driver.quit()

def compare_requests_vs_selenium(ramz_id):
    """Compare what requests gets vs what Selenium gets"""
    
    print(f"\n🔄 Comparing requests vs Selenium for ramz_id: {ramz_id}")
    
    url = f"https://guide-orientation.rnu.tn/ar/dynamique/filiere.php?id={ramz_id}"
    
    # Method 1: Regular requests
    print("  📥 Method 1: Regular requests")
    session = requests.Session()
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
    })
    
    requests_response = session.get(url)
    requests_soup = BeautifulSoup(requests_response.content, 'html.parser')
    
    # Count empty <b> tags
    requests_empty_b = len([b for b in requests_soup.find_all('b') if not b.get_text().strip()])
    requests_filled_b = len([b for b in requests_soup.find_all('b') if b.get_text().strip()])
    
    print(f"    Empty <b> tags: {requests_empty_b}")
    print(f"    Filled <b> tags: {requests_filled_b}")
    
    # Save requests HTML
    with open(f'requests_page_source_{ramz_id}.html', 'w', encoding='utf-8') as f:
        f.write(requests_soup.prettify())
    
    # Method 2: Selenium
    print("  🤖 Method 2: Selenium")
    selenium_results = analyze_javascript_requests(ramz_id)
    
    print(f"\n📊 Comparison Results:")
    print(f"  Requests method: {requests_filled_b} filled, {requests_empty_b} empty")
    print(f"  Selenium method: {selenium_results['filled_cells']} filled, {selenium_results['empty_cells']} empty")
    
    if selenium_results['filled_cells'] > requests_filled_b:
        print("  ✅ Selenium extracts MORE data than requests")
    elif selenium_results['filled_cells'] == requests_filled_b:
        print("  ⚠️ Both methods extract the SAME amount of data")
    else:
        print("  ❌ Requests extracts MORE data than Selenium (unexpected)")
    
    return {
        'requests': {'filled': requests_filled_b, 'empty': requests_empty_b},
        'selenium': selenium_results
    }

def main():
    """Main function to run all investigations"""
    
    print("🔍 INVESTIGATING PHP ENDPOINTS AND DATA LOADING")
    print("=" * 60)
    
    # Test with different ramz IDs
    test_ramz_ids = ["110101", "220518", "310101"]
    
    for ramz_id in test_ramz_ids:
        print(f"\n{'='*20} TESTING RAMZ ID: {ramz_id} {'='*20}")
        
        # 1. Check PHP endpoints
        php_results = check_php_endpoints(ramz_id)
        
        # 2. Compare requests vs Selenium
        comparison_results = compare_requests_vs_selenium(ramz_id)
        
        # 3. Save results
        results = {
            'ramz_id': ramz_id,
            'php_endpoints': php_results,
            'comparison': comparison_results,
            'timestamp': time.time()
        }
        
        with open(f'investigation_results_{ramz_id}.json', 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        
        print(f"  💾 Investigation results saved to: investigation_results_{ramz_id}.json")
    
    print(f"\n🎉 INVESTIGATION COMPLETE!")
    print(f"  Check the generated files:")
    print(f"  - investigation_results_*.json (detailed results)")
    print(f"  - requests_page_source_*.html (requests method HTML)")
    print(f"  - selenium_page_source_*.html (Selenium method HTML)")

if __name__ == "__main__":
    main()
