import json
import pandas as pd
from datetime import datetime

def remove_fields_from_finale_one():
    """Remove table_university and institution fields from finale_one files"""
    
    # Fields to remove
    fields_to_remove = ["table_university", "institution"]
    
    print(f"=== REMOVING FIELDS FROM FINALE_ONE ===")
    print(f"Fields to remove: {fields_to_remove}")
    
    # Process JSON file
    input_json = "data/finale_one.json"
    output_json = "data/finale-data.json"
    
    print(f"\nProcessing JSON file: {input_json}")
    with open(input_json, 'r', encoding='utf-8') as f:
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
    with open(output_json, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    print(f"✅ Cleaned JSON saved to: {output_json}")
    
    # Process CSV file
    input_csv = "data/finale_one.csv"
    output_csv = "data/finale-data.csv"
    
    print(f"\nProcessing CSV file: {input_csv}")
    df = pd.read_csv(input_csv, encoding='utf-8')
    
    original_columns = len(df.columns)
    print(f"Original CSV columns: {original_columns}")
    
    # Remove unwanted columns from DataFrame
    columns_to_remove = [col for col in fields_to_remove if col in df.columns]
    if columns_to_remove:
        df = df.drop(columns=columns_to_remove)
        print(f"Removed columns: {columns_to_remove}")
    
    # Save cleaned CSV
    df.to_csv(output_csv, index=False, encoding='utf-8')
    
    final_columns = len(df.columns)
    print(f"✅ Cleaned CSV saved to: {output_csv}")
    print(f"Final CSV columns: {final_columns} (reduced from {original_columns})")
    
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
        print(f"\nRemaining fields in cleaned data ({len(sample_record)} total):")
        for field in sorted(sample_record.keys()):
            print(f"  - {field}")
    
    # File sizes
    import os
    json_size = os.path.getsize(output_json) / 1024  # KB
    csv_size = os.path.getsize(output_csv) / 1024    # KB
    
    print(f"\n=== FILE SIZES ===")
    print(f"{output_json}: {json_size:.0f} KB")
    print(f"{output_csv}: {csv_size:.0f} KB")
    
    return output_json, output_csv

def main():
    try:
        output_json, output_csv = remove_fields_from_finale_one()
        print(f"\n✅ SUCCESS: Final cleaned files created:")
        print(f"   JSON: {output_json}")
        print(f"   CSV: {output_csv}")
    except Exception as e:
        print(f"❌ ERROR: {e}")

if __name__ == "__main__":
    main()
