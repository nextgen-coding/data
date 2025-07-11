#!/usr/bin/env python3
"""
Debug script to analyze the main page structure and find dropdown elements
"""

import asyncio
from playwright.async_api import async_playwright

async def debug_main_page():
    """Debug the main page to find dropdown elements"""
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context(
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36'
        )
        
        page = await context.new_page()
        
        print("🌐 Navigating to main page...")
        await page.goto('https://guide-orientation.rnu.tn/', wait_until='networkidle')
        await page.wait_for_timeout(3000)
        
        # Take screenshot
        await page.screenshot(path='debug_main_page_structure.png')
        
        print("🔍 Looking for all form elements...")
        
        # Find all form elements
        forms = await page.query_selector_all('form')
        print(f"Found {len(forms)} forms")
        
        # Find all select elements
        selects = await page.query_selector_all('select')
        print(f"Found {len(selects)} select elements:")
        
        for i, select in enumerate(selects):
            name = await select.get_attribute('name')
            id_attr = await select.get_attribute('id')
            print(f"  Select {i+1}: name='{name}', id='{id_attr}'")
            
            # Get options
            options = await select.query_selector_all('option')
            print(f"    Has {len(options)} options:")
            for j, option in enumerate(options[:5]):  # Show first 5 options
                value = await option.get_attribute('value')
                text = await option.inner_text()
                print(f"      {j+1}: value='{value}', text='{text.strip()}'")
            if len(options) > 5:
                print(f"      ... and {len(options) - 5} more options")
        
        # Find all input elements
        inputs = await page.query_selector_all('input')
        print(f"\nFound {len(inputs)} input elements:")
        
        for i, inp in enumerate(inputs):
            type_attr = await inp.get_attribute('type')
            name = await inp.get_attribute('name')
            value = await inp.get_attribute('value')
            print(f"  Input {i+1}: type='{type_attr}', name='{name}', value='{value}'")
        
        # Get page HTML for analysis
        html_content = await page.content()
        with open('debug_main_page_html.html', 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        print(f"\n📄 Page HTML saved to debug_main_page_html.html")
        print(f"📷 Screenshot saved to debug_main_page_structure.png")
        
        await browser.close()

if __name__ == "__main__":
    asyncio.run(debug_main_page())
