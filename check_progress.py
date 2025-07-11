#!/usr/bin/env python3
"""
Simple script to check progress and fix the batch numbering issue
"""

import json
from datetime import datetime

def check_progress():
    print("🔍 CHECKING CORRECTION PROGRESS")
    print("=" * 40)
    
    try:
        # Load original data
        with open('data/finale.json', 'r', encoding='utf-8') as f:
            original_data = json.load(f)
        print(f"📄 Original records: {len(original_data)}")
        
        # Load latest corrected data
        with open('finale_corrected_temp_20250711_232151.json', 'r', encoding='utf-8') as f:
            corrected_data = json.load(f)
        print(f"📄 Corrected records: {len(corrected_data)}")
        
        # Calculate remaining
        corrected_ramz_ids = {record['ramz_id'] for record in corrected_data}
        remaining_records = [record for record in original_data if record['ramz_id'] not in corrected_ramz_ids]
        
        print(f"📊 Remaining records: {len(remaining_records)}")
        print(f"📊 Progress: {len(corrected_data)}/{len(original_data)} ({len(corrected_data)/len(original_data)*100:.1f}%)")
        
        # Check historical scores validity in corrected data
        valid_scores = 0
        total_scores = 0
        
        for record in corrected_data[:10]:  # Check first 10 records
            if 'historical_scores' in record:
                scores = record['historical_scores']
                for year, score in scores.items():
                    total_scores += 1
                    if 0 <= float(score) <= 220:
                        valid_scores += 1
        
        print(f"📈 Score validity in corrected data: {valid_scores}/{total_scores} ({valid_scores/total_scores*100:.1f}% valid)")
        
        # Calculate batch info
        batch_size = 20
        completed_batches = len(corrected_data) // batch_size
        total_batches = (len(original_data) + batch_size - 1) // batch_size
        remaining_batches = total_batches - completed_batches
        
        print(f"📊 Batch progress: {completed_batches}/{total_batches} complete")
        print(f"📊 Remaining batches: {remaining_batches}")
        
        if len(remaining_records) == 0:
            print("🎉 ALL RECORDS COMPLETED!")
            
            # Save final corrected file
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            final_filename = f"data/finale_corrected_final_{timestamp}.json"
            
            with open(final_filename, 'w', encoding='utf-8') as f:
                json.dump(corrected_data, f, ensure_ascii=False, indent=2)
            
            print(f"💾 Saved final corrected file: {final_filename}")
            
            # Also save as CSV
            import csv
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
                
                print(f"📄 Saved final CSV: {csv_filename}")
            
        else:
            print(f"🔄 Need to continue processing {len(remaining_records)} remaining records")
            print(f"🎯 Next records to process:")
            for i, record in enumerate(remaining_records[:5], 1):
                print(f"   {i}. {record['ramz_id']}")
            if len(remaining_records) > 5:
                print(f"   ... and {len(remaining_records) - 5} more")
            
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    check_progress()
