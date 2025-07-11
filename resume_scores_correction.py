#!/usr/bin/env python3
"""
Resume historical scores correction from where it left off
"""

import asyncio
import json
from playwright.async_api import async_playwright
from datetime import datetime
import re

async def parse_values_response(content, ramz_id):
    """Parse values.php response content and extract historical scores"""
    scores = {}
    
    if not content or not content.strip():
        return scores
    
    try:
        # Parse as delimited text (like "2020/109.82251/2021/93.4883/")
        if '/' in content:
            parts = content.strip().split('/')
            
            # Parse pairs of year/score
            for i in range(0, len(parts) - 1, 2):
                try:
                    year = parts[i].strip()
                    score = parts[i + 1].strip()
                    
                    year_int = int(year)
                    score_float = float(score)
                    
                    if 2011 <= year_int <= 2024 and 0 <= score_float <= 220 and score_float != 0:
                        scores[str(year_int)] = score_float
                        
                except (ValueError, IndexError):
                    continue
    
    except Exception as e:
        pass
    
    return scores

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
            # Navigate to ramz page
            await page.goto(ramz_url, wait_until='networkidle', timeout=10000)
            await page.wait_for_timeout(500)
            
            # Use fetch API to get values.php data
            fetch_result = await page.evaluate(f"""
                async () => {{
                    try {{
                        const response = await fetch('/ar/dynamique/values.php?id={ramz_id}');
                        const text = await response.text();
                        return {{
                            status: response.status,
                            content: text
                        }};
                    }} catch (error) {{
                        return {{ error: error.message }};
                    }}
                }}
            """)
            
            if 'content' in fetch_result:
                scores = await parse_values_response(fetch_result['content'], ramz_id)
                # Return all years 2011-2024 with 0 for missing years
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

async def resume_correction():
    """Resume correction from the intermediate temp file"""
    
    print("🔄 RESUMING HISTORICAL SCORES CORRECTION")
    print("=" * 50)
    
    # Load the intermediate progress
    temp_file = "finale_corrected_temp_20250711_230735.json"
    try:
        with open(temp_file, 'r', encoding='utf-8') as f:
            corrected_data = json.load(f)
        print(f"✅ Loaded {len(corrected_data)} corrected records from {temp_file}")
    except Exception as e:
        print(f"❌ Error loading temp file: {e}")
        return
    
    # Load original data
    try:
        with open('data/finale.json', 'r', encoding='utf-8') as f:
            original_data = json.load(f)
        print(f"✅ Loaded {len(original_data)} original records")
    except Exception as e:
        print(f"❌ Error loading original data: {e}")
        return
    
    # Find where we left off (records that haven't been corrected yet)
    corrected_ramz_ids = {record['ramz_id'] for record in corrected_data}
    remaining_records = [record for record in original_data if record['ramz_id'] not in corrected_ramz_ids]
    
    print(f"📊 Progress: {len(corrected_data)}/{len(original_data)} records corrected")
    print(f"📊 Remaining: {len(remaining_records)} records to process")
    
    if not remaining_records:
        print("🎉 All records already corrected!")
        return
    
    # Process remaining records in batches
    batch_size = 20
    total_batches = (len(remaining_records) + batch_size - 1) // batch_size
    
    success_count = 0
    fail_count = 0
    
    for batch_num in range(total_batches):
        start_idx = batch_num * batch_size
        end_idx = min(start_idx + batch_size, len(remaining_records))
        batch = remaining_records[start_idx:end_idx]
        
        batch_start = len(corrected_data) // batch_size + batch_num + 1
        total_display = (len(original_data) + batch_size - 1) // batch_size
        print(f"\n🎯 Processing batch {batch_start}/{total_display} ({len(batch)} records)")
        
        # Process batch
        for i, record in enumerate(batch, 1):
            ramz_id = record['ramz_id']
            print(f"   📊 {i}/{len(batch)}: {ramz_id}", end=" ")
            
            try:
                # Extract correct scores
                correct_scores = await extract_correct_scores(ramz_id)
                
                if correct_scores and any(score > 0 for score in correct_scores.values()):
                    # Update the record with correct scores
                    record['historical_scores'] = correct_scores
                    record['scores_corrected_at'] = datetime.now().isoformat()
                    
                    # Count non-zero scores
                    non_zero_scores = sum(1 for score in correct_scores.values() if score > 0)
                    print(f"✅ ({non_zero_scores} scores)")
                    success_count += 1
                else:
                    print("❌ (no scores)")
                    fail_count += 1
                
                # Add to corrected data
                corrected_data.append(record)
                
            except Exception as e:
                print(f"❌ (error: {str(e)[:30]})")
                fail_count += 1
                # Add original record even if correction failed
                corrected_data.append(record)
        
        print(f"✅ Batch {batch_start} complete")
        
        # Save intermediate progress every 5 batches
        if batch_num % 5 == 4:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            temp_filename = f"finale_corrected_temp_{timestamp}.json"
            with open(temp_filename, 'w', encoding='utf-8') as f:
                json.dump(corrected_data, f, ensure_ascii=False, indent=2)
            print(f"💾 Saved intermediate progress: {temp_filename}")
        
        # Small delay between batches
        await asyncio.sleep(1)
    
    # Save final corrected data
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # JSON
    final_json = f"finale_corrected_complete_{timestamp}.json"
    with open(final_json, 'w', encoding='utf-8') as f:
        json.dump(corrected_data, f, ensure_ascii=False, indent=2)
    
    # CSV
    final_csv = f"finale_corrected_complete_{timestamp}.csv"
    if corrected_data:
        import csv
        fieldnames = list(corrected_data[0].keys())
        with open(final_csv, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(corrected_data)
    
    print(f"\n🎉 CORRECTION COMPLETE!")
    print(f"📊 Total records: {len(corrected_data)}")
    print(f"📊 Successfully corrected: {success_count}")
    print(f"📊 Failed to correct: {fail_count}")
    print(f"📄 Final JSON: {final_json}")
    print(f"📄 Final CSV: {final_csv}")
    
    # Validation check
    print(f"\n🔍 VALIDATION CHECK:")
    valid_scores = 0
    total_score_records = 0
    
    for record in corrected_data:
        if 'historical_scores' in record:
            total_score_records += 1
            scores = record['historical_scores']
            if all(0 <= float(score) <= 220 for score in scores.values()):
                valid_scores += 1
    
    print(f"   Records with valid scores (0-220): {valid_scores}/{total_score_records}")
    print(f"   Validation rate: {valid_scores/total_score_records*100:.1f}%")

if __name__ == "__main__":
    asyncio.run(resume_correction())
