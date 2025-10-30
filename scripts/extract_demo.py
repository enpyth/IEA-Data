#!/usr/bin/env python3
"""
Script to extract the data from each JSON file in the tag_data directory
and combine them into a single JSON file.
"""

import json
import os
from pathlib import Path

EXTRACT_COUNT = 3

def extract_data(output_file):
    """
    Extract first EXTRACT_COUNT items from each JSON file in tag_data directory
    and combine them into a single JSON file.
    """
    # Define paths
    tag_data_dir = Path("../tag_data")
    
    # Check if tag_data directory exists
    if not tag_data_dir.exists():
        print(f"Error: {tag_data_dir} directory not found!")
        return
    
    # Dictionary to store combined data
    combined_data = {}
    
    # Get all JSON files in tag_data directory
    json_files = list(tag_data_dir.glob("*.json"))
    
    if not json_files:
        print(f"No JSON files found in {tag_data_dir}")
        return
    
    print(f"Found {len(json_files)} JSON files to process...")
    
    # Process each JSON file
    for json_file in json_files:
        try:
            print(f"Processing: {json_file.name}")
            
            # Read the JSON file
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Extract first EXTRACT_COUNT items
            first_five = data[:EXTRACT_COUNT] if isinstance(data, list) else []
            
            # Store in combined data with filename as key
            file_key = json_file.stem  # filename without extension
            combined_data[file_key] = {
                "source_file": json_file.name,
                "total_items": len(data) if isinstance(data, list) else 0,
                "extracted_items": first_five
            }
            
            print(f"  - Extracted {len(first_five)} items from {len(data) if isinstance(data, list) else 0} total items")
            
        except json.JSONDecodeError as e:
            print(f"  - Error reading JSON from {json_file.name}: {e}")
        except Exception as e:
            print(f"  - Error processing {json_file.name}: {e}")
    
    # Write combined data to output file
    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(combined_data, f, indent=2, ensure_ascii=False)
        
        print(f"\nSuccessfully created {output_file}")
        print(f"Combined data from {len(combined_data)} files")
        
        # Print summary
        total_extracted = sum(len(data["extracted_items"]) for data in combined_data.values())
        print(f"Total extracted items: {total_extracted}")
        
    except Exception as e:
        print(f"Error writing output file: {e}")

if __name__ == "__main__":
    output_file = "./output/extracted_data.json"
    extract_data(output_file)
