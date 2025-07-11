"""
Playwright-based scraper that simulates the full user workflow:
1. Load index.php
2. Select dropdown values (bac type, university, institution, specialization)
3. Click search button
4. Extract table data with ramz links
5. Visit ramz detail pages to extract comprehensive data
"""

import asyncio
import json
import csv
import pandas as pd
from playwright.async_api import async_playwright
import time
import re
from urllib.parse import urljoin
import logging

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class PlaywrightFullWorkflowScraper:
    def __init__(self):
        self.base_url = "https://guide-orientation.rnu.tn/"
        self.index_url = "https://guide-orientation.rnu.tn/index.php"
        self.results = []
        
    async def analyze_page_structure(self, page):
        """Analyze the page structure and JavaScript events"""
        logger.info("Analyzing page structure...")
        
        # Check for form elements
        form_elements = await page.query_selector_all('select, input, button')
        logger.info(f"Found {len(form_elements)} form elements")
        
        for element in form_elements:
            tag_name = await element.evaluate('el => el.tagName')
            name = await element.get_attribute('name') or 'no-name'
            id_attr = await element.get_attribute('id') or 'no-id'
            logger.info(f"Element: {tag_name}, name: {name}, id: {id_attr}")
        
        # Check for JavaScript files
        scripts = await page.query_selector_all('script[src]')
        for script in scripts:
            src = await script.get_attribute('src')
            logger.info(f"Script: {src}")
    
    async def wait_for_dropdown_options(self, page, selector, timeout=10000):
        """Wait for dropdown options to be populated"""
        try:
            await page.wait_for_function(
                f'document.querySelector("{selector}").options.length > 1',
                timeout=timeout
            )
            return True
        except:
            logger.warning(f"Timeout waiting for {selector} options")
            return False
    
    async def get_dropdown_options(self, page, selector):
        """Get all options from a dropdown"""
        try:
            options = await page.evaluate('''
                (selector) => {
                    const select = document.querySelector(selector);
                    if (!select) return [];
                    return Array.from(select.options)
                        .map(option => ({
                            value: option.value,
                            text: option.text.trim()
                        }))
                        .filter(option => option.value && option.value !== "");
                }
            ''', selector)
            return options
        except Exception as e:
            logger.error(f"Error getting options for {selector}: {e}")
            return []
    
    async def select_dropdown_value(self, page, selector, value):
        """Select a value in dropdown and trigger change event"""
        try:
            await page.select_option(selector, value)
            # Trigger multiple events to ensure chained selects work
            await page.evaluate('''
                (selector) => {
                    const select = document.querySelector(selector);
                    select.dispatchEvent(new Event('change', { bubbles: true }));
                    select.dispatchEvent(new Event('input', { bubbles: true }));
                    // Also trigger jQuery events if jQuery is available
                    if (window.jQuery) {
                        window.jQuery(select).trigger('change');
                    }
                }
            ''', selector)
            await page.wait_for_timeout(3000)  # Wait longer for AJAX
            return True
        except Exception as e:
            logger.error(f"Error selecting {value} in {selector}: {e}")
            return False
    
    async def click_search_button(self, page):
        """Click the search button and wait for results"""
        try:
            # Try different possible search button selectors
            search_selectors = [
                'input[name="submit"]',
                'input[value="إبحث"]',
                'input[type="submit"]',
                'button[type="submit"]'
            ]
            
            clicked = False
            for selector in search_selectors:
                if await page.query_selector(selector):
                    logger.info(f"Clicking search button: {selector}")
                    await page.click(selector)
                    clicked = True
                    break
            
            if not clicked:
                logger.error("Could not find search button")
                return False
            
            # Wait for results table to load
            await page.wait_for_timeout(3000)
            return True
            
        except Exception as e:
            logger.error(f"Error clicking search button: {e}")
            return False
    
    async def extract_table_data(self, page):
        """Extract data from the results table"""
        try:
            # Look for table with results
            tables = await page.query_selector_all('table')
            logger.info(f"Found {len(tables)} tables")
            
            ramz_data = []
            
            for i, table in enumerate(tables):
                rows = await table.query_selector_all('tr')
                if len(rows) > 1:  # Has header and data rows
                    logger.info(f"Table {i} has {len(rows)} rows")
                    
                    # Extract table data
                    table_data = await page.evaluate('''
                        (table) => {
                            const rows = Array.from(table.querySelectorAll('tr'));
                            return rows.map(row => {
                                const cells = Array.from(row.querySelectorAll('td, th'));
                                return cells.map(cell => cell.textContent.trim());
                            });
                        }
                    ''', table)
                    
                    logger.info(f"Table {i} sample data: {table_data[:3]}")
                    
                    # Check if this is the results table (contains ramz codes)
                    if len(table_data) > 1 and len(table_data[1]) > 0:
                        first_data_row = table_data[1] if len(table_data) > 1 else []
                        
                        # Look for ramz pattern (5-digit codes)
                        if first_data_row and len(first_data_row) > 0:
                            potential_ramz = first_data_row[0]
                            if potential_ramz.isdigit() and len(potential_ramz) == 5:
                                logger.info(f"Found results table {i} with ramz codes")
                                
                                # Extract ramz data from this table
                                for row_data in table_data[1:]:  # Skip header
                                    if len(row_data) >= 9 and row_data[0].isdigit():
                                        ramz_code = row_data[0]
                                        specialization = row_data[1]
                                        university = row_data[2]
                                        institution = row_data[3]
                                        location = row_data[4]
                                        criteria = row_data[5]
                                        capacity = row_data[6]
                                        duration = row_data[7]
                                        last_score = row_data[8]
                                        
                                        # Construct ramz URL
                                        ramz_url = f"https://guide-orientation.rnu.tn/ramz.php?code={ramz_code}"
                                        
                                        ramz_data.append({
                                            'ramz_code': ramz_code,
                                            'ramz_url': ramz_url,
                                            'specialization': specialization,
                                            'university': university,
                                            'institution': institution,
                                            'location': location,
                                            'criteria': criteria,
                                            'capacity': capacity,
                                            'duration': duration,
                                            'last_score': last_score
                                        })
                                
                                logger.info(f"Extracted {len(ramz_data)} ramz entries from table {i}")
                                return ramz_data
                    
                    # Also look for ramz links (backup method)
                    ramz_links = await table.evaluate('''
                        (table) => {
                            const links = Array.from(table.querySelectorAll('a[href*="ramz"]'));
                            return links.map(link => ({
                                href: link.href,
                                text: link.textContent.trim()
                            }));
                        }
                    ''')
                    
                    if ramz_links:
                        logger.info(f"Found {len(ramz_links)} ramz links in table {i}")
                        return ramz_links
            
            return ramz_data
            
        except Exception as e:
            logger.error(f"Error extracting table data: {e}")
            return []
    
    async def test_workflow_sample(self, page):
        """Test the workflow with a few sample cases"""
        try:
            logger.info("Starting workflow test...")
            
            # Load the main page
            await page.goto(self.index_url, wait_until='networkidle')
            await page.wait_for_timeout(2000)
            
            # Save initial page state
            await page.screenshot(path='debug_initial_page.png')
            
            # Analyze page structure
            await self.analyze_page_structure(page)
            
            # Look for dropdown selectors (using actual form names found)
            dropdowns = {
                'bac_type': ['select[name="fBac"]', 'select#fBac'],
                'university': ['select[name="fUniv"]', 'select#fUniv'],
                'institution': ['select[name="fEtab"]', 'select#fEtab'],
                'specialization': ['select[name="fFiliere"]', 'select#fFiliere']
            }
            
            found_dropdowns = {}
            for dropdown_name, selectors in dropdowns.items():
                for selector in selectors:
                    if await page.query_selector(selector):
                        found_dropdowns[dropdown_name] = selector
                        logger.info(f"Found {dropdown_name}: {selector}")
                        break
            
            if not found_dropdowns:
                logger.error("No dropdowns found - analyzing page HTML")
                html = await page.content()
                with open('debug_full_page.html', 'w', encoding='utf-8') as f:
                    f.write(html)
                
                # Look for any select elements
                selects = await page.query_selector_all('select')
                logger.info(f"Found {len(selects)} select elements")
                for i, select in enumerate(selects):
                    name = await select.get_attribute('name')
                    id_attr = await select.get_attribute('id')
                    logger.info(f"Select {i}: name={name}, id={id_attr}")
                
                return False
            
            # Test with first available bac type
            if 'bac_type' in found_dropdowns:
                selector = found_dropdowns['bac_type']
                await self.wait_for_dropdown_options(page, selector)
                bac_options = await self.get_dropdown_options(page, selector)
                logger.info(f"Bac type options: {bac_options[:5]}")
                
                if bac_options:
                    # Select first non-empty option
                    first_option = bac_options[0]['value']
                    await self.select_dropdown_value(page, selector, first_option)
                    logger.info(f"Selected bac type: {first_option}")
                    
                    # Wait and check if other dropdowns are populated
                    await page.wait_for_timeout(2000)
                    
                    # Try to get university options
                    if 'university' in found_dropdowns:
                        univ_selector = found_dropdowns['university']
                        await self.wait_for_dropdown_options(page, univ_selector)
                        univ_options = await self.get_dropdown_options(page, univ_selector)
                        logger.info(f"University options: {len(univ_options)}")
                        
                        if univ_options:
                            # Select first university
                            first_univ = univ_options[0]['value']
                            await self.select_dropdown_value(page, univ_selector, first_univ)
                            logger.info(f"Selected university: {first_univ}")
                            await page.wait_for_timeout(2000)
            
            # Try to click search
            search_success = await self.click_search_button(page)
            if search_success:
                logger.info("Search button clicked successfully")
                await page.screenshot(path='debug_after_search.png')
                
                # Extract table data
                ramz_links = await self.extract_table_data(page)
                if ramz_links:
                    logger.info(f"Found {len(ramz_links)} ramz links")
                    return ramz_links[:5]  # Return first 5 for testing
            
            return []
            
        except Exception as e:
            logger.error(f"Error in workflow test: {e}")
            await page.screenshot(path='debug_error.png')
            return []
    
    async def extract_ramz_detail(self, page, ramz_url):
        """Extract detailed information from a ramz page"""
        try:
            await page.goto(ramz_url, wait_until='networkidle')
            await page.wait_for_timeout(2000)
            
            # Extract all available information
            detail_data = await page.evaluate('''
                () => {
                    const data = {};
                    
                    // Get page title
                    data.title = document.title;
                    
                    // Look for specific data patterns
                    const text = document.body.textContent;
                    
                    // Extract university name (pattern matching)
                    const univMatch = text.match(/الجامعة[:\\s]*([^\\n\\r]+)/);
                    if (univMatch) data.university = univMatch[1].trim();
                    
                    // Extract institution name
                    const instMatch = text.match(/المؤسسة[:\\s]*([^\\n\\r]+)/);
                    if (instMatch) data.institution = instMatch[1].trim();
                    
                    // Extract specialization
                    const specMatch = text.match(/الشعبة[:\\s]*([^\\n\\r]+)/);
                    if (specMatch) data.specialization = specMatch[1].trim();
                    
                    // Extract scores (look for numeric patterns)
                    const scoreMatches = text.match(/\\d+\\.\\d+/g);
                    if (scoreMatches) data.scores = scoreMatches;
                    
                    // Get all table data
                    const tables = Array.from(document.querySelectorAll('table'));
                    data.tables = tables.map(table => {
                        const rows = Array.from(table.querySelectorAll('tr'));
                        return rows.map(row => {
                            const cells = Array.from(row.querySelectorAll('td, th'));
                            return cells.map(cell => cell.textContent.trim());
                        });
                    });
                    
                    return data;
                }
            ''')
            
            return detail_data
            
        except Exception as e:
            logger.error(f"Error extracting ramz detail from {ramz_url}: {e}")
            return {}
    
    async def run_test(self):
        """Run the test workflow"""
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=False, slow_mo=1000)
            context = await browser.new_context(
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36'
            )
            page = await context.new_page()
            
            try:
                # Test the workflow
                ramz_links = await self.test_workflow_sample(page)
                
                if ramz_links:
                    logger.info(f"Testing detail extraction on {len(ramz_links)} ramz links")
                    
                    test_results = []
                    for ramz_item in ramz_links[:3]:  # Test first 3
                        # Handle different data structures
                        if isinstance(ramz_item, dict):
                            if 'ramz_url' in ramz_item:
                                # This is ramz_data from table extraction
                                ramz_url = ramz_item['ramz_url']
                                ramz_code = ramz_item['ramz_code']
                            elif 'href' in ramz_item:
                                # This is ramz_links from link extraction
                                ramz_url = ramz_item['href']
                                ramz_code = ramz_item['text']
                            else:
                                continue
                        else:
                            continue
                        
                        logger.info(f"Extracting detail from: {ramz_url}")
                        
                        detail_data = await self.extract_ramz_detail(page, ramz_url)
                        detail_data['ramz_url'] = ramz_url
                        detail_data['ramz_code'] = ramz_code
                        
                        # Add table data if available
                        if 'specialization' in ramz_item:
                            detail_data['table_specialization'] = ramz_item['specialization']
                            detail_data['table_university'] = ramz_item['university']
                            detail_data['table_institution'] = ramz_item['institution']
                            detail_data['table_location'] = ramz_item['location']
                            detail_data['table_criteria'] = ramz_item['criteria']
                            detail_data['table_capacity'] = ramz_item['capacity']
                            detail_data['table_duration'] = ramz_item['duration']
                            detail_data['table_last_score'] = ramz_item['last_score']
                        
                        test_results.append(detail_data)
                    
                    # Save test results
                    timestamp = time.strftime("%Y%m%d_%H%M%S")
                    output_file = f"playwright_test_results_{timestamp}.json"
                    
                    with open(output_file, 'w', encoding='utf-8') as f:
                        json.dump(test_results, f, ensure_ascii=False, indent=2)
                    
                    logger.info(f"Test results saved to {output_file}")
                    
                    # Print summary
                    for i, result in enumerate(test_results):
                        logger.info(f"Result {i+1}:")
                        logger.info(f"  URL: {result.get('ramz_url', 'N/A')}")
                        logger.info(f"  University: {result.get('university', 'N/A')}")
                        logger.info(f"  Institution: {result.get('institution', 'N/A')}")
                        logger.info(f"  Specialization: {result.get('specialization', 'N/A')}")
                        logger.info(f"  Scores found: {len(result.get('scores', []))}")
                
                else:
                    logger.error("No ramz links found - workflow failed")
                
            finally:
                await browser.close()

if __name__ == "__main__":
    scraper = PlaywrightFullWorkflowScraper()
    asyncio.run(scraper.run_test())
