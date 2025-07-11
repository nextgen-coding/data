#!/usr/bin/env python3
"""
Corrected Historical Scores Extractor
Fix all historical scores in finale.json using the working values.php method
"""

import asyncio
import json
from playwright.async_api import async_playwright
import re
from datetime import datetime

async def extract_correct_historical_scores(ramz_id):
    """Extract correct historical scores using the working Method 3B approach"""
    
    ramz_url = f"https://guide-orientation.rnu.tn/ar/dynamique/filiere.php?id={ramz_id}"
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)  # Fast extraction
        context = await browser.new_context(
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36'
        )
        
        page = await context.new_page()
        
        try:
            # Navigate to ramz page
            await page.goto(ramz_url, wait_until='networkidle', timeout=30000)
            await page.wait_for_timeout(2000)
            
            # Use Method 3B: Fetch from page context (the working method!)
            fetch_result = await page.evaluate(f"""
                async () => {{
                    try {{
                        const response = await fetch('/ar/dynamique/values.php?id={ramz_id}');
                        const text = await response.text();
                        return {{
                            status: response.status,
                            content: text,
                            success: true
                        }};
                    }} catch (error) {{
                        return {{
                            error: error.message,
                            success: false
                        }};
                    }}
                }}
            """)
            
            if fetch_result.get('success') and 'content' in fetch_result:
                content = fetch_result['content']
                scores = parse_values_content(content)
                await browser.close()
                return scores
            else:
                await browser.close()
                return {}
                
        except Exception as e:
            await browser.close()
            return {}

def parse_values_content(content):
    """Parse the values.php content to extract historical scores"""
    scores = {}
    
    if not content or not content.strip():
        return scores
    
    try:
        # The content format is: "2011/0/2012/0/2013/0/2014/0/2015/0/2016/0/2017/0/2018/0/2019/0/2020/109.8251/2021/93.4883/2022/0/2023/0/2024/0/"
        parts = content.strip().split('/')
        
        # Parse pairs of year/score
        for i in range(0, len(parts) - 1, 2):
            try:
                if i + 1 < len(parts):
                    year = parts[i].strip()
                    score = parts[i + 1].strip()
                    
                    year_int = int(year)
                    score_float = float(score)
                    
                    # Only include years 2010-2024 and valid scores (0-220)
                    if 2010 <= year_int <= 2024 and 0 <= score_float <= 220:
                        scores[str(year_int)] = score_float
                        
            except (ValueError, IndexError):
                continue
    
    except Exception as e:
        print(f"❌ Error parsing content: {e}")
    
    return scores

async def update_all_historical_scores():
    """Update historical scores for all records in finale.json"""
    
    print("🇹🇳 CORRECTED HISTORICAL SCORES UPDATER")
    print("=" * 60)
    print("Using the working Method 3B (Fetch from page context)")
    print()
    
    # Load current finale.json
    try:
        with open('data/finale.json', 'r', encoding='utf-8') as f:
            finale_data = json.load(f)
        print(f"📄 Loaded {len(finale_data)} records from finale.json")
    except Exception as e:
        print(f"❌ Error loading finale.json: {e}")
        return
    
    # Process records in batches
    batch_size = 10
    updated_records = []
    successful_updates = 0
    failed_updates = 0
    
    for i in range(0, len(finale_data), batch_size):
        batch = finale_data[i:i + batch_size]
        batch_num = i // batch_size + 1
        total_batches = (len(finale_data) + batch_size - 1) // batch_size
        
        print(f"\n🎯 Processing batch {batch_num}/{total_batches} ({len(batch)} records)")
        
        # Process batch concurrently
        tasks = []
        for record in batch:
            ramz_id = record.get('ramz_id')
            if ramz_id:
                task = extract_correct_historical_scores(ramz_id)
                tasks.append((ramz_id, task))
        
        # Execute batch
        for ramz_id, task in tasks:
            try:
                new_scores = await task
                
                # Find the record and update it
                for record in batch:
                    if record.get('ramz_id') == ramz_id:
                        old_scores = record.get('historical_scores', {})
                        
                        if new_scores:
                            record['historical_scores'] = new_scores
                            record['scores_updated_at'] = datetime.now().isoformat()
                            record['scores_extraction_method'] = 'values_php_fetch'
                            
                            # Count valid scores
                            old_valid = sum(1 for score in old_scores.values() if 0 <= float(score) <= 220)
                            new_valid = sum(1 for score in new_scores.values() if 0 <= float(score) <= 220)
                            
                            print(f"  ✅ {ramz_id}: {old_valid}→{new_valid} valid scores")
                            successful_updates += 1
                        else:
                            print(f"  ❌ {ramz_id}: No scores extracted")
                            failed_updates += 1
                        
                        updated_records.append(record)
                        break
            
            except Exception as e:
                print(f"  ❌ {ramz_id}: Error - {e}")
                failed_updates += 1
                
                # Add original record
                for record in batch:
                    if record.get('ramz_id') == ramz_id:
                        updated_records.append(record)
                        break
        
        # Small delay between batches
        await asyncio.sleep(1)
    
    # Save updated data
    if updated_records:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Save corrected JSON
        corrected_json_file = f'data/finale_corrected_scores_{timestamp}.json'
        with open(corrected_json_file, 'w', encoding='utf-8') as f:
            json.dump(updated_records, f, ensure_ascii=False, indent=2)
        
        # Save corrected CSV
        corrected_csv_file = f'data/finale_corrected_scores_{timestamp}.csv'
        if updated_records:
            import csv
            fieldnames = list(updated_records[0].keys())
            with open(corrected_csv_file, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(updated_records)
        
        print(f"\n🎉 UPDATE COMPLETE!")
        print(f"📊 Total records: {len(updated_records)}")
        print(f"✅ Successful updates: {successful_updates}")
        print(f"❌ Failed updates: {failed_updates}")
        print(f"📁 Files saved:")
        print(f"   📄 JSON: {corrected_json_file}")
        print(f"   📄 CSV: {corrected_csv_file}")
        
        # Show validation statistics
        total_valid_scores = 0
        total_scores = 0
        
        for record in updated_records:
            if 'historical_scores' in record:
                scores = record['historical_scores']
                total_scores += len(scores)
                total_valid_scores += sum(1 for score in scores.values() if 0 <= float(score) <= 220)
        
        print(f"\n📈 VALIDATION STATISTICS:")
        print(f"   Total historical scores: {total_scores}")
        print(f"   Valid scores (0-220): {total_valid_scores}")
        print(f"   Validity rate: {(total_valid_scores/total_scores)*100:.1f}%" if total_scores > 0 else "   No scores found")

async def main():
    """Main execution function"""
    await update_all_historical_scores()

if __name__ == "__main__":
    asyncio.run(main())
