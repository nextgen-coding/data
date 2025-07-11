#!/usr/bin/env python3
"""
Diagnostic script to compare Selenium extraction vs manual browser access
"""

import csv
import json
import time
import requests
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
import webbrowser

def test_manual_vs_selenium_access():
    """Compare manual browser access vs Selenium access"""
    
    # Test URL - let's use the first ramz link
    test_url = "https://guide-orientation.rnu.tn/ar/dynamique/filiere.php?id=110101"
    
    print("🔍 COMPARING MANUAL VS SELENIUM ACCESS")
    print("=" * 50)
    print(f"Test URL: {test_url}")
    
    # Method 1: Simple requests (baseline)
    print("\n📡 Method 1: Simple HTTP Request")
    try:
        session = requests.Session()
        session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'ar,en;q=0.9',
        })
        
        response = session.get(test_url, timeout=10)
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Save requests HTML
        with open('compare_requests.html', 'w', encoding='utf-8') as f:
            f.write(soup.prettify())
        
        # Extract sample fields
        university_requests = extract_field_from_soup(soup, 'الجامعة')
        specialization_requests = extract_field_from_soup(soup, 'الشعبة / الإجازة')
        
        print(f"  University: '{university_requests}'")
        print(f"  Specialization: '{specialization_requests}'")
        print(f"  HTML saved: compare_requests.html")
        
    except Exception as e:
        print(f"  ❌ Error: {e}")
    
    # Method 2: Selenium with different configurations
    selenium_configs = [
        {"name": "Standard Selenium", "headless": True, "stealth": False},
        {"name": "Visible Selenium", "headless": False, "stealth": False},
        {"name": "Stealth Selenium", "headless": True, "stealth": True},
        {"name": "Slow Selenium", "headless": False, "stealth": True, "slow": True}
    ]
    
    for config in selenium_configs:
        print(f"\n🤖 Method: {config['name']}")
        try:
            driver = setup_selenium_driver(config)
            
            # Load page
            driver.get(test_url)
            
            # Wait for page load
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, "table"))
            )
            
            # Additional wait time
            if config.get('slow'):
                print("  ⏳ Waiting 10 seconds for full page load...")
                time.sleep(10)
            else:
                time.sleep(3)
            
            # Save Selenium HTML
            filename = f"compare_selenium_{config['name'].lower().replace(' ', '_')}.html"
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(driver.page_source)
            
            # Extract sample fields
            university_selenium = extract_field_from_selenium(driver, 'الجامعة')
            specialization_selenium = extract_field_from_selenium(driver, 'الشعبة / الإجازة')
            
            # Check for JavaScript completion
            js_ready = driver.execute_script("return document.readyState === 'complete'")
            jquery_ready = driver.execute_script("return typeof $ !== 'undefined' && $.active === 0") if check_jquery(driver) else "N/A"
            
            print(f"  University: '{university_selenium}'")
            print(f"  Specialization: '{specialization_selenium}'")
            print(f"  Page ready: {js_ready}")
            print(f"  jQuery ready: {jquery_ready}")
            print(f"  HTML saved: {filename}")
            
            driver.quit()
            
        except Exception as e:
            print(f"  ❌ Error: {e}")
    
    # Method 3: Open in manual browser for comparison
    print(f"\n🌐 Method: Manual Browser")
    print(f"  Opening {test_url} in your default browser...")
    print(f"  Please manually check the page and compare with saved HTML files")
    
    try:
        webbrowser.open(test_url)
        time.sleep(2)
    except Exception as e:
        print(f"  ❌ Error opening browser: {e}")
    
    # Analysis
    print(f"\n📊 ANALYSIS SUMMARY")
    print(f"  Generated files for comparison:")
    print(f"    - compare_requests.html (HTTP requests)")
    print(f"    - compare_selenium_*.html (Various Selenium configs)")
    print(f"  ")
    print(f"  Next steps:")
    print(f"    1. Compare the HTML files to see differences")
    print(f"    2. Check what you see manually vs what Selenium extracts")
    print(f"    3. Look for anti-bot measures or dynamic content loading")

def setup_selenium_driver(config):
    """Setup Selenium driver with specific configuration"""
    
    chrome_options = Options()
    
    if config.get('headless'):
        chrome_options.add_argument('--headless')
    
    if config.get('stealth'):
        # Stealth options to avoid detection
        chrome_options.add_argument('--disable-blink-features=AutomationControlled')
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-gpu')
    
    # Standard options
    chrome_options.add_argument('--window-size=1920,1080')
    chrome_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36')
    
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)
    
    if config.get('stealth'):
        # Execute stealth script
        driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
    
    driver.set_page_load_timeout(30)
    return driver

def extract_field_from_soup(soup, arabic_label):
    """Extract field value from BeautifulSoup"""
    try:
        rows = soup.find_all('tr')
        for row in rows:
            cells = row.find_all('td')
            if len(cells) >= 2:
                label_text = cells[0].get_text().strip()
                if arabic_label in label_text:
                    value_cell = cells[1]
                    bold_tags = value_cell.find_all('b')
                    if bold_tags:
                        values = [b.get_text().strip() for b in bold_tags if b.get_text().strip()]
                        if values:
                            return ' '.join(values)
                    return value_cell.get_text().strip()
        return ''
    except:
        return ''

def extract_field_from_selenium(driver, arabic_label):
    """Extract field value from Selenium driver"""
    try:
        rows = driver.find_elements(By.TAG_NAME, "tr")
        for row in rows:
            cells = row.find_elements(By.TAG_NAME, "td")
            if len(cells) >= 2:
                label_text = cells[0].text.strip()
                if arabic_label in label_text:
                    value_cell = cells[1]
                    bold_elements = value_cell.find_elements(By.TAG_NAME, "b")
                    if bold_elements:
                        values = [b.text.strip() for b in bold_elements if b.text.strip()]
                        if values:
                            return ' '.join(values)
                    return value_cell.text.strip()
        return ''
    except:
        return ''

def check_jquery(driver):
    """Check if jQuery is available"""
    try:
        return driver.execute_script("return typeof $ !== 'undefined'")
    except:
        return False

def create_interactive_test():
    """Create an interactive test to manually verify data"""
    
    print("\n🔧 INTERACTIVE SELENIUM TEST")
    print("=" * 40)
    print("This will open a visible Selenium browser where you can:")
    print("1. See exactly what Selenium sees")
    print("2. Manually interact with the page if needed")
    print("3. Compare with what you see in your regular browser")
    
    input("Press Enter to start the interactive test...")
    
    try:
        # Setup visible Selenium
        chrome_options = Options()
        chrome_options.add_argument('--window-size=1920,1080')
        chrome_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36')
        
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=chrome_options)
        
        test_url = "https://guide-orientation.rnu.tn/ar/dynamique/filiere.php?id=110101"
        print(f"Loading: {test_url}")
        
        driver.get(test_url)
        
        print("\n🔍 Selenium browser is now open!")
        print("Take a screenshot or note what you see, then:")
        print("1. Compare with your manual browser")
        print("2. Check if all fields are populated")
        print("3. Look for any differences")
        
        input("Press Enter when you've finished examining the page...")
        
        # Extract data for comparison
        print("\n📊 What Selenium extracted:")
        fields_to_check = [
            'الجامعة',
            'الولاية', 
            'المؤسسة',
            'الشعبة / الإجازة',
            'المقياس',
            'نوع الباكالوريا'
        ]
        
        for field in fields_to_check:
            value = extract_field_from_selenium(driver, field)
            status = "✅" if value and value.strip() else "❌"
            print(f"  {status} {field}: '{value}'")
        
        driver.quit()
        
    except Exception as e:
        print(f"❌ Error in interactive test: {e}")

def main():
    """Main diagnostic function"""
    
    print("🔍 SELENIUM VS MANUAL BROWSER DIAGNOSTIC")
    print("=" * 60)
    
    choice = input("Choose test type:\n1. Automated comparison\n2. Interactive test\n3. Both\nEnter choice (1-3): ")
    
    if choice in ['1', '3']:
        test_manual_vs_selenium_access()
    
    if choice in ['2', '3']:
        create_interactive_test()
    
    print("\n🎯 DIAGNOSTIC COMPLETE!")
    print("Check the generated HTML files and compare them with what you see manually.")

if __name__ == "__main__":
    main()
