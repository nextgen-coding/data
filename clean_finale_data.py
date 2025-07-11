import json
import pandas as pd
from datetime import datetime

def clean_data_fields(input_json_file, input_csv_file, output_base_name):
    """Remove unwanted fields from JSON and CSV files"""
    
    # Fields to remove
    fields_to_remove = [
        "final_merge_timestamp",
        "scores_corrected_at",
        "specialization_code_detailed",
        "bac_type",
        "study_duration",
        "extracted_at",
        "extraction_phase",
        "university",
        "governorate"
    ]
    
    print(f"=== CLEANING DATA FILES ===")
    print(f"Fields to remove: {fields_to_remove}")
    
    # Process JSON file
    print(f"\nProcessing JSON file: {input_json_file}")
    with open(input_json_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    total_records = len(data)
    fields_removed_count = {field: 0 for field in fields_to_remove}
    
    # Remove unwanted fields from each record
    for record in data:
        for field in fields_to_remove:
            if field in record:
                del record[field]
                fields_removed_count[field] += 1
    
    # Save cleaned JSON
    output_json = f"data/{output_base_name}.json"
    with open(output_json, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    print(f"✅ Cleaned JSON saved to: {output_json}")
    
    # Process CSV file
    print(f"\nProcessing CSV file: {input_csv_file}")
    df = pd.read_csv(input_csv_file, encoding='utf-8')
    
    print(f"Original CSV columns: {len(df.columns)}")
    
    # Remove unwanted columns from DataFrame
    columns_to_remove = [col for col in fields_to_remove if col in df.columns]
    if columns_to_remove:
        df = df.drop(columns=columns_to_remove)
        print(f"Removed columns: {columns_to_remove}")
    
    # Save cleaned CSV
    output_csv = f"data/{output_base_name}.csv"
    df.to_csv(output_csv, index=False, encoding='utf-8')
    
    print(f"✅ Cleaned CSV saved to: {output_csv}")
    print(f"Final CSV columns: {len(df.columns)}")
    
    # Summary
    print(f"\n=== SUMMARY ===")
    print(f"Total records processed: {total_records}")
    print(f"Fields removed from JSON:")
    for field, count in fields_removed_count.items():
        if count > 0:
            print(f"  {field}: {count} records")
    
    # Show sample of remaining fields
    if data:
        sample_record = data[0]
        print(f"\nRemaining fields in cleaned data:")
        for field in sorted(sample_record.keys()):
            print(f"  - {field}")
    
    return output_json, output_csv

def main():
    input_json = "data/new_finale.json"
    input_csv = "data/new_finale.csv"
    output_base = "finale_one"
    
    try:
        output_json, output_csv = clean_data_fields(input_json, input_csv, output_base)
        print(f"\n✅ SUCCESS: Cleaned files created:")
        print(f"   JSON: {output_json}")
        print(f"   CSV: {output_csv}")
    except Exception as e:
        print(f"❌ ERROR: {e}")

if __name__ == "__main__":
    main()
