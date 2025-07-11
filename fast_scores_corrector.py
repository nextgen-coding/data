#!/usr/bin/env python3
"""
Fast Historical Scores Corrector - Fix all historical scores in finale.json
"""

import asyncio
import json
from playwright.async_api import async_playwright
from datetime import datetime
import re

async def extract_correct_scores(ramz_id):
    """Extract correct historical scores for a single ramz_id using Method 3B"""
    
    ramz_url = f"https://guide-orientation.rnu.tn/ar/dynamique/filiere.php?id={ramz_id}"
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36'
        )
        page = await context.new_page()
        
        try:
            # Navigate to ramz page
            await page.goto(ramz_url, wait_until='networkidle', timeout=15000)
            await page.wait_for_timeout(1000)
            
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
                        return {{
                            error: error.message
                        }};
                    }}
                }}
            """)
            
            if 'content' in fetch_result:
                content = fetch_result['content']
                scores = {}
                
                # Parse the format: "2011/0/2012/0/.../2020/109.8251/2021/93.4883/..."
                if '/' in content:
                    parts = content.strip().split('/')
                    
                    # Parse pairs of year/score
                    for i in range(0, len(parts) - 1, 2):
                        try:
                            year = parts[i].strip()
                            score = parts[i + 1].strip()
                            
                            year_int = int(year)
                            score_float = float(score)
                            
                            if 2010 <= year_int <= 2024 and 0 <= score_float <= 220:
                                scores[str(year_int)] = score_float
                                
                        except (ValueError, IndexError):
                            continue
                
                await browser.close()
                return scores
            
            await browser.close()
            return {}
            
        except Exception as e:
            await browser.close()
            return {}

async def process_batch(records_batch, batch_num, total_batches):
    """Process a batch of records concurrently"""
    print(f"🎯 Processing batch {batch_num}/{total_batches} ({len(records_batch)} records)")
    
    # Process records in this batch sequentially (to avoid overwhelming server)
    results = []
    
    for i, record in enumerate(records_batch, 1):
        ramz_id = record.get('ramz_id')
        if not ramz_id:
            results.append(record)
            continue
        
        print(f"   📊 {i}/{len(records_batch)}: {ramz_id}", end="", flush=True)
        
        try:
            correct_scores = await extract_correct_scores(ramz_id)
            
            if correct_scores:
                # Update the record with correct scores
                record['historical_scores'] = correct_scores
                record['scores_corrected_at'] = datetime.now().isoformat()
                print(f" ✅ ({len(correct_scores)} scores)")
            else:
                print(f" ❌ (no scores)")
            
            results.append(record)
            
        except Exception as e:
            print(f" ❌ Error: {str(e)[:50]}")
            results.append(record)
        
        # Small delay to avoid overwhelming server
        await asyncio.sleep(0.5)
    
    print(f"✅ Batch {batch_num} complete")
    return results

async def correct_all_historical_scores():
    """Correct all historical scores in finale.json"""
    
    print("🇹🇳 HISTORICAL SCORES CORRECTOR")
    print("=" * 50)
    
    # Load finale.json
    try:
        with open('data/finale.json', 'r', encoding='utf-8') as f:
            records = json.load(f)
        print(f"📄 Loaded {len(records)} records from finale.json")
    except Exception as e:
        print(f"❌ Error loading finale.json: {e}")
        return
    
    # Process in batches to be efficient
    batch_size = 20  # Process 20 records per batch
    batches = [records[i:i + batch_size] for i in range(0, len(records), batch_size)]
    total_batches = len(batches)
    
    print(f"📊 Processing {len(records)} records in {total_batches} batches")
    
    start_time = datetime.now()
    all_corrected = []
    
    # Process batches
    for batch_num, batch in enumerate(batches, 1):
        try:
            corrected_batch = await process_batch(batch, batch_num, total_batches)
            all_corrected.extend(corrected_batch)
            
            # Save intermediate progress every 5 batches
            if batch_num % 5 == 0:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                temp_file = f"finale_corrected_temp_{timestamp}.json"
                with open(temp_file, 'w', encoding='utf-8') as f:
                    json.dump(all_corrected, f, ensure_ascii=False, indent=2)
                print(f"💾 Saved intermediate progress: {temp_file}")
        
        except Exception as e:
            print(f"❌ Error processing batch {batch_num}: {e}")
            # Continue with next batch
            all_corrected.extend(batch)
    
    # Save final corrected data
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Save JSON
    corrected_json = f"finale_corrected_{timestamp}.json"
    with open(corrected_json, 'w', encoding='utf-8') as f:
        json.dump(all_corrected, f, ensure_ascii=False, indent=2)
    
    # Save CSV
    corrected_csv = f"finale_corrected_{timestamp}.csv"
    if all_corrected:
        import csv
        fieldnames = list(all_corrected[0].keys())
        with open(corrected_csv, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(all_corrected)
    
    end_time = datetime.now()
    duration = end_time - start_time
    
    print(f"\n🎉 CORRECTION COMPLETE!")
    print(f"⏱️  Total time: {duration}")
    print(f"📊 Processed records: {len(all_corrected)}")
    print(f"📄 Files saved:")
    print(f"   📄 JSON: {corrected_json}")
    print(f"   📄 CSV: {corrected_csv}")
    
    # Validation statistics
    corrected_count = 0
    valid_scores_count = 0
    total_scores = 0
    
    for record in all_corrected:
        if 'scores_corrected_at' in record:
            corrected_count += 1
        
        if 'historical_scores' in record:
            scores = record['historical_scores']
            for score in scores.values():
                total_scores += 1
                if 0 <= float(score) <= 220:
                    valid_scores_count += 1
    
    print(f"\n📈 VALIDATION STATISTICS:")
    print(f"   Records with corrected scores: {corrected_count}/{len(all_corrected)}")
    print(f"   Valid scores (0-220): {valid_scores_count}/{total_scores}")
    print(f"   Average time per record: {duration.total_seconds() / len(all_corrected):.2f}s")

if __name__ == "__main__":
    asyncio.run(correct_all_historical_scores())
