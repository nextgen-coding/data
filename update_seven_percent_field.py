import json
import csv
import pandas as pd
from datetime import datetime

def load_codes_from_csv(csv_file):
    """Load the 3-digit codes from codes.csv file"""
    codes = set()
    
    try:
        with open(csv_file, 'r', encoding='utf-8') as file:
            reader = csv.reader(file)
            for row in reader:
                if len(row) >= 2:  # Make sure we have at least 2 columns
                    code = row[1].strip()  # Second column contains the code
                    if code.isdigit() and len(code) == 3:  # Ensure it's a 3-digit code
                        codes.add(code)
    except Exception as e:
        print(f"Error reading codes.csv: {e}")
        return set()
    
    return codes

def update_seven_percent_field(input_file, codes_set):
    """Update the seven_percent field based on last 3 digits of ramz_code"""
    
    # Load the JSON data
    with open(input_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    updated_count = 0
    total_count = len(data)
    
    print(f"Processing {total_count} records...")
    print(f"Loaded {len(codes_set)} codes from codes.csv: {sorted(list(codes_set))[:10]}...")
    
    for record in data:
        ramz_code = record.get('ramz_code', '')
        
        if len(ramz_code) >= 3:
            # Get last 3 digits of ramz_code
            last_3_digits = ramz_code[-3:]
            
            # Update seven_percent field based on whether last 3 digits are in codes_set
            if last_3_digits in codes_set:
                new_value = "no"
            else:
                new_value = "yes"
            
            # Only count as updated if the value actually changed
            if record.get('seven_percent') != new_value:
                updated_count += 1
                
            record['seven_percent'] = new_value
    
    print(f"Updated {updated_count} records out of {total_count}")
    
    return data

def save_updated_data(data, base_filename):
    """Save the updated data to both JSON and CSV formats"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Save JSON
    json_filename = f"{base_filename}_seven_percent_corrected_{timestamp}.json"
    with open(json_filename, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    # Save CSV
    csv_filename = f"{base_filename}_seven_percent_corrected_{timestamp}.csv"
    df = pd.DataFrame(data)
    df.to_csv(csv_filename, index=False, encoding='utf-8')
    
    return json_filename, csv_filename

def validate_update(data, codes_set, sample_size=10):
    """Validate the seven_percent field updates with examples"""
    print("\n=== VALIDATION EXAMPLES ===")
    
    # Show some examples of records with seven_percent="no" (should match codes)
    no_examples = [r for r in data if r.get('seven_percent') == 'no'][:sample_size//2]
    print(f"\nRecords with seven_percent='no' (last 3 digits should be in codes.csv):")
    for record in no_examples:
        ramz_code = record.get('ramz_code', '')
        last_3 = ramz_code[-3:] if len(ramz_code) >= 3 else ''
        in_codes = last_3 in codes_set
        print(f"  ramz_code: {ramz_code} → last 3 digits: {last_3} → in codes.csv: {in_codes}")
    
    # Show some examples of records with seven_percent="yes" (should NOT match codes)
    yes_examples = [r for r in data if r.get('seven_percent') == 'yes'][:sample_size//2]
    print(f"\nRecords with seven_percent='yes' (last 3 digits should NOT be in codes.csv):")
    for record in yes_examples:
        ramz_code = record.get('ramz_code', '')
        last_3 = ramz_code[-3:] if len(ramz_code) >= 3 else ''
        in_codes = last_3 in codes_set
        print(f"  ramz_code: {ramz_code} → last 3 digits: {last_3} → in codes.csv: {in_codes}")

def main():
    # File paths
    codes_file = "codes.csv"
    input_file = "restoration/finale_corrected_COMPLETE_20250711_235029.json"
    base_filename = "finale_corrected_COMPLETE"
    
    print("=== UPDATING SEVEN_PERCENT FIELD ===")
    
    # Load codes from CSV
    print(f"Loading codes from {codes_file}...")
    codes_set = load_codes_from_csv(codes_file)
    
    if not codes_set:
        print("No codes loaded from CSV file. Exiting.")
        return
    
    print(f"Loaded {len(codes_set)} codes from codes.csv")
    
    # Update the seven_percent field
    print(f"Loading data from {input_file}...")
    updated_data = update_seven_percent_field(input_file, codes_set)
    
    # Save updated data
    print("Saving updated data...")
    json_file, csv_file = save_updated_data(updated_data, base_filename)
    
    print(f"✅ Updated data saved to:")
    print(f"   JSON: {json_file}")
    print(f"   CSV: {csv_file}")
    
    # Validate the updates
    validate_update(updated_data, codes_set)
    
    # Summary statistics
    total_records = len(updated_data)
    seven_percent_no = len([r for r in updated_data if r.get('seven_percent') == 'no'])
    seven_percent_yes = len([r for r in updated_data if r.get('seven_percent') == 'yes'])
    
    print(f"\n=== SUMMARY STATISTICS ===")
    print(f"Total records: {total_records}")
    print(f"Records with seven_percent='no': {seven_percent_no}")
    print(f"Records with seven_percent='yes': {seven_percent_yes}")
    print(f"Percentage with seven_percent='no': {seven_percent_no/total_records*100:.1f}%")

if __name__ == "__main__":
    main()
