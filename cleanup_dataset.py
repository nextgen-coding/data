#!/usr/bin/env python3
"""
Clean the final dataset by removing unwanted fields
"""

import json
import csv
from datetime import datetime

def clean_dataset():
    """Clean the dataset by removing unwanted fields"""
    
    print("🧹 CLEANING FINAL DATASET")
    print("=" * 40)
    
    # Fields to remove
    fields_to_remove = [
        'extracted_at',
        'extraction_phase', 
        'university',
        'governorate',
        'institution',
        'bac_type',
        'study_duration',
        'seven_percent',
        'final_merge_timestamp',
        'scores_corrected_at'
    ]
    
    print(f"🗑️  Fields to remove: {fields_to_remove}")
    
    # Load the complete dataset
    try:
        with open('data/finale_corrected_COMPLETE_20250711_235029.json', 'r', encoding='utf-8') as f:
            data = json.load(f)
        print(f"📄 Loaded {len(data)} records")
    except Exception as e:
        print(f"❌ Error loading data: {e}")
        return
    
    # Clean each record
    cleaned_data = []
    removed_fields_count = {}
    
    for record in data:
        cleaned_record = {}
        
        for key, value in record.items():
            if key not in fields_to_remove:
                cleaned_record[key] = value
            else:
                # Count removed fields
                removed_fields_count[key] = removed_fields_count.get(key, 0) + 1
        
        cleaned_data.append(cleaned_record)
    
    print(f"🧹 Cleaned {len(cleaned_data)} records")
    print(f"📊 Removed fields count:")
    for field, count in removed_fields_count.items():
        print(f"   {field}: {count} instances")
    
    # Save cleaned JSON
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    json_filename = f"data/finale_cleaned_final_{timestamp}.json"
    with open(json_filename, 'w', encoding='utf-8') as f:
        json.dump(cleaned_data, f, ensure_ascii=False, indent=2)
    
    print(f"✅ Cleaned JSON saved: {json_filename}")
    
    # Save cleaned CSV
    csv_filename = f"data/finale_cleaned_final_{timestamp}.csv"
    
    if cleaned_data:
        # Get all possible fields including flattened historical scores
        all_fields = set()
        for record in cleaned_data:
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
            
            for record in cleaned_data:
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
        
        print(f"✅ Cleaned CSV saved: {csv_filename}")
    
    # Show sample of cleaned data
    print(f"\n🔍 SAMPLE CLEANED RECORD:")
    if cleaned_data:
        sample = cleaned_data[0]
        print(f"   Fields in cleaned record: {len(sample)}")
        for key in sorted(sample.keys())[:10]:  # Show first 10 fields
            if key != 'historical_scores':
                value = str(sample[key])[:50]  # Truncate long values
                print(f"     {key}: {value}")
        
        if 'historical_scores' in sample:
            scores = sample['historical_scores']
            non_zero_scores = sum(1 for score in scores.values() if float(score) > 0)
            print(f"     historical_scores: {non_zero_scores}/14 non-zero scores")
    
    return json_filename, csv_filename

def cleanup_old_files():
    """Clean up old JSON and CSV files from data directory"""
    
    print(f"\n🗑️  CLEANING UP OLD FILES")
    print("=" * 40)
    
    import os
    import glob
    
    data_dir = 'data'
    
    # Files to keep (the new cleaned ones will be added to this list)
    files_to_keep = {
        'finale.json',
        'finale.csv'
    }
    
    # Get all JSON and CSV files in data directory
    json_files = glob.glob(os.path.join(data_dir, '*.json'))
    csv_files = glob.glob(os.path.join(data_dir, '*.csv'))
    
    all_files = json_files + csv_files
    
    print(f"📁 Found {len(all_files)} JSON/CSV files in data directory")
    
    files_to_delete = []
    files_to_keep_list = []
    
    for file_path in all_files:
        filename = os.path.basename(file_path)
        
        # Keep the original finale files and new cleaned files
        if (filename in files_to_keep or 
            'finale_cleaned_final_' in filename or
            filename == 'finale_corrected_COMPLETE_20250711_235029.json' or
            filename == 'finale_corrected_COMPLETE_20250711_235029.csv'):
            files_to_keep_list.append(filename)
        else:
            files_to_delete.append(file_path)
    
    print(f"📋 Files to keep ({len(files_to_keep_list)}):")
    for filename in sorted(files_to_keep_list):
        print(f"   ✅ {filename}")
    
    print(f"\n🗑️  Files to delete ({len(files_to_delete)}):")
    for file_path in sorted(files_to_delete)[:10]:  # Show first 10
        filename = os.path.basename(file_path)
        print(f"   ❌ {filename}")
    
    if len(files_to_delete) > 10:
        print(f"   ... and {len(files_to_delete) - 10} more files")
    
    if files_to_delete:
        confirm = input(f"\n⚠️  Delete {len(files_to_delete)} old files? (y/N): ")
        if confirm.lower() == 'y':
            deleted_count = 0
            for file_path in files_to_delete:
                try:
                    os.remove(file_path)
                    deleted_count += 1
                except Exception as e:
                    print(f"❌ Failed to delete {os.path.basename(file_path)}: {e}")
            
            print(f"✅ Deleted {deleted_count} old files")
        else:
            print("🔄 Skipped file deletion")
    else:
        print("✅ No old files to delete")

def main():
    """Main execution function"""
    
    print("🇹🇳 TUNISIA UNIVERSITY DATASET CLEANUP")
    print("=" * 50)
    
    # Clean the dataset
    json_file, csv_file = clean_dataset()
    
    # Clean up old files
    cleanup_old_files()
    
    print(f"\n🎉 CLEANUP COMPLETED!")
    print(f"📁 Backup files saved in: /restoration")
    print(f"📄 Clean JSON: {json_file}")
    print(f"📄 Clean CSV: {csv_file}")
    print(f"🧹 Old files cleaned from /data directory")

if __name__ == "__main__":
    main()
