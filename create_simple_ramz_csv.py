#!/usr/bin/env python3
"""
Simple script to create a CSV with just ramz codes and links
"""

import re
import csv

def extract_ramz_links():
    """Extract ramz codes and links from existing CSV file"""
    
    ramz_data = []
    
    try:
        with open('ramz_links.csv', 'r', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                ramz_data.append({
                    'ramz_code': row['ramz_code'],
                    'ramz_link': row['ramz_link']
                })
        
        return ramz_data
        
    except Exception as e:
        print(f"Error reading CSV file: {e}")
        return []

def create_csv(ramz_data):
    """Create a simple CSV file with ramz codes and links"""
    
    if not ramz_data:
        print("No data to save")
        return
    
    filename = 'ramz_links.csv'
    
    with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
        fieldnames = ['ramz_code', 'ramz_link']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        
        writer.writeheader()
        for row in ramz_data:
            writer.writerow(row)
    
    print(f"✅ Created {filename} with {len(ramz_data)} ramz links")
    return filename

def main():
    print("Creating simple ramz CSV...")
    
    # Extract data
    ramz_data = extract_ramz_links()
    
    if ramz_data:
        # Create CSV
        filename = create_csv(ramz_data)
        print(f"📁 File created: {filename}")
        
        # Show sample
        print(f"\n📋 Sample data (first 5 rows):")
        for i, row in enumerate(ramz_data[:5]):
            print(f"  {row['ramz_code']} -> {row['ramz_link']}")
        
        print(f"\nTotal: {len(ramz_data)} unique ramz links")
    else:
        print("❌ No data found")

if __name__ == "__main__":
    main()
