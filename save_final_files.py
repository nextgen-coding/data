#!/usr/bin/env python3
"""
Save the final corrected files properly
"""

import json
import csv
from datetime import datetime

def save_final_corrected_files():
    print("💾 SAVING FINAL CORRECTED FILES")
    print("=" * 40)
    
    # Load the completed data
    try:
        with open('finale_corrected_temp_20250711_233151.json', 'r', encoding='utf-8') as f:
            corrected_data = json.load(f)
        print(f"📄 Loaded {len(corrected_data)} corrected records")
    except Exception as e:
        print(f"❌ Error loading data: {e}")
        return
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Save JSON
    json_filename = f"data/finale_corrected_final_{timestamp}.json"
    with open(json_filename, 'w', encoding='utf-8') as f:
        json.dump(corrected_data, f, ensure_ascii=False, indent=2)
    print(f"✅ JSON saved: {json_filename}")
    
    # Save CSV with proper field handling
    csv_filename = f"data/finale_corrected_final_{timestamp}.csv"
    
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
        
        print(f"✅ CSV saved: {csv_filename}")
    
    # Validation summary
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
    print(f"   Records with valid scores: {records_with_scores}")
    print(f"   Total score entries: {total_scores}")
    print(f"   Valid score entries (0-220): {valid_scores} ({valid_scores/total_scores*100:.1f}%)")
    
    # Sample some records for verification
    print(f"\n🔍 SAMPLE RECORDS:")
    for i, record in enumerate(corrected_data[:3], 1):
        print(f"   {i}. {record['ramz_id']}: {record.get('specialization_name', 'N/A')}")
        if 'historical_scores' in record:
            non_zero_scores = sum(1 for score in record['historical_scores'].values() if float(score) > 0)
            print(f"      Historical scores: {non_zero_scores}/14 non-zero")
    
    print(f"\n✨ FINAL CORRECTED DATASET COMPLETED! ✨")
    print(f"📄 Files saved in /data directory")

if __name__ == "__main__":
    save_final_corrected_files()
