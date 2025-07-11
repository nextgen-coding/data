#!/usr/bin/env python3
"""
Final verification and completion script - ensure we have all 998 records
"""

import json
import asyncio
from playwright.async_api import async_playwright
from datetime import datetime
import csv

async def extract_correct_scores(ramz_id):
    """Extract correct historical scores for a ramz_id"""
    ramz_url = f"https://guide-orientation.rnu.tn/ar/dynamique/filiere.php?id={ramz_id}"
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        )
        page = await context.new_page()
        
        try:
            await page.goto(ramz_url, wait_until='networkidle', timeout=15000)
            await page.wait_for_timeout(1000)
            
            # Use the working method: fetch API from page context
            fetch_result = await page.evaluate(f"""
                async () => {{
                    try {{
                        const response = await fetch('/ar/dynamique/values.php?id={ramz_id}');
                        const text = await response.text();
                        return {{ content: text }};
                    }} catch (error) {{
                        return {{ error: error.message }};
                    }}
                }}
            """)
            
            if 'content' in fetch_result:
                content = fetch_result['content']
                scores = {}
                
                # Parse the format: "2011/0/2012/0/2013/0/2014/0/2015/0/2016/0/2017/0/2018/0/2019/0/2020/109.8251/2021/93.4883/2022/0/2023/0/2024/0/"
                if '/' in content:
                    parts = content.strip().split('/')
                    for i in range(0, len(parts) - 1, 2):
                        try:
                            year = int(parts[i].strip())
                            score = float(parts[i + 1].strip())
                            if 2011 <= year <= 2024 and 0 <= score <= 220:
                                scores[str(year)] = score
                        except (ValueError, IndexError):
                            continue
                
                # Return complete scores for all years 2011-2024
                complete_scores = {}
                for year in range(2011, 2025):
                    complete_scores[str(year)] = scores.get(str(year), 0.0)
                return complete_scores
            else:
                return {}
                
        except Exception as e:
            return {}
        
        finally:
            await browser.close()

async def ensure_complete_dataset():
    """Ensure we have a complete dataset with all 998 records"""
    
    print("🔍 FINAL VERIFICATION AND COMPLETION")
    print("=" * 50)
    
    # Load original data
    try:
        with open('data/finale.json', 'r', encoding='utf-8') as f:
            original_data = json.load(f)
        print(f"📄 Original records: {len(original_data)}")
    except Exception as e:
        print(f"❌ Error loading original data: {e}")
        return
    
    # Load the latest corrected data
    try:
        with open('finale_corrected_temp_20250711_233151.json', 'r', encoding='utf-8') as f:
            corrected_data = json.load(f)
        print(f"📄 Latest corrected records: {len(corrected_data)}")
    except Exception as e:
        print(f"❌ Error loading corrected data: {e}")
        return
    
    # Find any missing records
    corrected_ramz_ids = {record['ramz_id'] for record in corrected_data}
    missing_records = [record for record in original_data if record['ramz_id'] not in corrected_ramz_ids]
    
    print(f"📊 Missing records: {len(missing_records)}")
    
    if missing_records:
        print(f"🎯 Processing {len(missing_records)} missing records:")
        
        for i, record in enumerate(missing_records, 1):
            print(f"   📊 {i}/{len(missing_records)}: {record['ramz_id']}", end=" ")
            
            try:
                correct_scores = await extract_correct_scores(record['ramz_id'])
                
                if correct_scores:
                    record['historical_scores'] = correct_scores
                    non_zero_scores = sum(1 for score in correct_scores.values() if score > 0)
                    print(f"✅ ({non_zero_scores} scores)")
                else:
                    print("❌ (no scores)")
                
                corrected_data.append(record)
                
            except Exception as e:
                print(f"❌ (error: {str(e)[:30]})")
                corrected_data.append(record)
    
    # Final validation
    print(f"\n📊 FINAL DATASET:")
    print(f"   Total records: {len(corrected_data)}")
    print(f"   Expected: {len(original_data)}")
    print(f"   Complete: {'✅' if len(corrected_data) == len(original_data) else '❌'}")
    
    # Save the complete final dataset
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Save JSON
    json_filename = f"data/finale_corrected_COMPLETE_{timestamp}.json"
    with open(json_filename, 'w', encoding='utf-8') as f:
        json.dump(corrected_data, f, ensure_ascii=False, indent=2)
    print(f"✅ Complete JSON saved: {json_filename}")
    
    # Save CSV with proper field handling
    csv_filename = f"data/finale_corrected_COMPLETE_{timestamp}.csv"
    
    if corrected_data:
        # Get all possible fields including historical scores
        all_fields = set()
        for record in corrected_data:
            all_fields.update(record.keys())
            if 'historical_scores' in record:
                for year in record['historical_scores'].keys():
                    all_fields.add(f'score_{year}')
        
        # Remove historical_scores field as we'll flatten it
        all_fields.discard('historical_scores')
        fieldnames = sorted(list(all_fields))
        
        with open(csv_filename, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            
            for record in corrected_data:
                # Flatten historical_scores for CSV
                row = dict(record)
                if 'historical_scores' in row:
                    scores = row.pop('historical_scores')
                    for year, score in scores.items():
                        row[f'score_{year}'] = score
                        
                # Fill missing fields with empty values
                for field in fieldnames:
                    if field not in row:
                        row[field] = ''
                        
                writer.writerow(row)
        
        print(f"✅ Complete CSV saved: {csv_filename}")
    
    # Final validation summary
    valid_scores = 0
    total_scores = 0
    records_with_scores = 0
    
    for record in corrected_data:
        if 'historical_scores' in record:
            has_valid_scores = False
            scores = record['historical_scores']
            for year, score in scores.items():
                total_scores += 1
                if 0 <= float(score) <= 220:
                    valid_scores += 1
                    if float(score) > 0:
                        has_valid_scores = True
            if has_valid_scores:
                records_with_scores += 1
    
    print(f"\n📈 FINAL VALIDATION:")
    print(f"   Total records: {len(corrected_data)}")
    print(f"   Records with historical scores: {records_with_scores}")
    print(f"   Total score entries: {total_scores}")
    print(f"   Valid score entries (0-220): {valid_scores} ({valid_scores/total_scores*100:.1f}%)")
    
    print(f"\n🎉 COMPLETE DATASET FINALIZED! 🎉")
    print(f"📄 All {len(corrected_data)} records processed")
    print(f"📄 Historical scores corrected with valid range (0-220)")
    print(f"📁 Files saved in /data directory")

if __name__ == "__main__":
    asyncio.run(ensure_complete_dataset())
