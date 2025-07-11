#!/usr/bin/env python3
"""
Final completion script - finish the last 98 records with correct batch numbering
"""

import asyncio
import json
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

async def complete_final_correction():
    """Complete the final correction of remaining records"""
    
    print("🏁 FINAL HISTORICAL SCORES COMPLETION")
    print("=" * 50)
    
    # Load progress
    try:
        with open('data/finale.json', 'r', encoding='utf-8') as f:
            original_data = json.load(f)
        
        with open('finale_corrected_temp_20250711_232151.json', 'r', encoding='utf-8') as f:
            corrected_data = json.load(f)
        
        print(f"📄 Original: {len(original_data)} records")
        print(f"📄 Corrected: {len(corrected_data)} records")
        
    except Exception as e:
        print(f"❌ Error loading data: {e}")
        return
    
    # Find remaining records
    corrected_ramz_ids = {record['ramz_id'] for record in corrected_data}
    remaining_records = [record for record in original_data if record['ramz_id'] not in corrected_ramz_ids]
    
    print(f"📊 Remaining: {len(remaining_records)} records")
    
    if not remaining_records:
        print("🎉 All records already completed!")
        return await save_final_files(corrected_data)
    
    # Process remaining records
    batch_size = 20
    total_original_batches = (len(original_data) + batch_size - 1) // batch_size
    completed_batches = len(corrected_data) // batch_size
    
    success_count = 0
    fail_count = 0
    
    for i, record in enumerate(remaining_records, 1):
        current_batch = completed_batches + ((i - 1) // batch_size) + 1
        batch_position = ((i - 1) % batch_size) + 1
        
        print(f"📊 {i}/{len(remaining_records)} (Batch {current_batch}/{total_original_batches}, Record {batch_position}/20): {record['ramz_id']}", end=" ")
        
        try:
            correct_scores = await extract_correct_scores(record['ramz_id'])
            
            if correct_scores:
                record['historical_scores'] = correct_scores
                non_zero_scores = sum(1 for score in correct_scores.values() if score > 0)
                print(f"✅ ({non_zero_scores} scores)")
                success_count += 1
            else:
                print("❌ (no scores)")
                fail_count += 1
            
            corrected_data.append(record)
            
            # Save intermediate progress every 20 records
            if i % 20 == 0:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                temp_filename = f"finale_corrected_temp_{timestamp}.json"
                with open(temp_filename, 'w', encoding='utf-8') as f:
                    json.dump(corrected_data, f, ensure_ascii=False, indent=2)
                print(f"💾 Saved intermediate progress: {temp_filename}")
            
        except Exception as e:
            print(f"❌ (error: {str(e)[:30]})")
            fail_count += 1
            corrected_data.append(record)
    
    print(f"\n🎯 COMPLETION SUMMARY:")
    print(f"   ✅ Successful: {success_count}")
    print(f"   ❌ Failed: {fail_count}")
    print(f"   📊 Total processed: {len(corrected_data)}")
    
    # Save final files
    await save_final_files(corrected_data)

async def save_final_files(corrected_data):
    """Save the final corrected files"""
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Save JSON
    json_filename = f"data/finale_corrected_final_{timestamp}.json"
    with open(json_filename, 'w', encoding='utf-8') as f:
        json.dump(corrected_data, f, ensure_ascii=False, indent=2)
    
    # Save CSV
    csv_filename = f"data/finale_corrected_final_{timestamp}.csv"
    
    if corrected_data:
        fieldnames = list(corrected_data[0].keys())
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
                writer.writerow(row)
    
    print(f"\n🎉 FINAL FILES SAVED:")
    print(f"📄 JSON: {json_filename}")
    print(f"📄 CSV: {csv_filename}")
    
    # Validation summary
    valid_scores = 0
    total_scores = 0
    
    for record in corrected_data:
        if 'historical_scores' in record:
            scores = record['historical_scores']
            for year, score in scores.items():
                total_scores += 1
                if 0 <= float(score) <= 220:
                    valid_scores += 1
    
    print(f"\n📈 FINAL VALIDATION:")
    print(f"   Total records: {len(corrected_data)}")
    print(f"   Total scores: {total_scores}")
    print(f"   Valid scores (0-220): {valid_scores} ({valid_scores/total_scores*100:.1f}%)")
    
    print(f"\n✨ CORRECTION COMPLETED SUCCESSFULLY! ✨")

if __name__ == "__main__":
    asyncio.run(complete_final_correction())
