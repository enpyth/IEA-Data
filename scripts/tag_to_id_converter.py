#!/usr/bin/env python3
"""
Tag Information to Tag ID Converter

This script converts tag information from researcher data to tag IDs
based on the index mapping files (index_en.json and index_cn.json).

Usage:
    python3 tag_to_id_converter.py input_file.json output_file.json [--index-file index_en.json]
"""

import json
import argparse
import sys
from typing import Dict, List, Tuple, Any


class TagToIdConverter:
    def __init__(self, index_file: str = "index/index_en.json"):
        """
        Initialize the converter with an index file.
        
        Args:
            index_file: Path to the index file containing category and subcategory mappings
        """
        self.index_file = index_file
        self.category_map = {}  # Maps category names to IDs
        self.subcategory_map = {}  # Maps subcategory names to IDs
        self.load_index()
    
    def load_index(self):
        """Load the index file and build mapping dictionaries."""
        try:
            with open(self.index_file, 'r', encoding='utf-8') as f:
                index_data = json.load(f)
            
            # Build category mapping
            for category in index_data:
                category_name = category['name']
                category_id = category['id']
                self.category_map[category_name] = category_id
                
                # Build subcategory mapping
                for subcategory in category['subcategories']:
                    subcategory_name = subcategory['name']
                    subcategory_id = subcategory['id']
                    self.subcategory_map[subcategory_name] = subcategory_id
            
            print(f"Loaded {len(self.category_map)} categories and {len(self.subcategory_map)} subcategories from {self.index_file}")
            
        except FileNotFoundError:
            print(f"Error: Index file '{self.index_file}' not found.")
            sys.exit(1)
        except json.JSONDecodeError as e:
            print(f"Error: Invalid JSON in index file '{self.index_file}': {e}")
            sys.exit(1)
    
    def parse_subcategories(self, subcategory_string: str) -> List[str]:
        """
        Parse a comma-separated string of subcategories.
        
        Args:
            subcategory_string: String containing comma-separated subcategory names
            
        Returns:
            List of cleaned subcategory names
        """
        if not subcategory_string:
            return []
        
        # Split by comma and clean whitespace
        subcategories = [s.strip() for s in subcategory_string.split(',')]
        # Remove empty strings
        subcategories = [s for s in subcategories if s]
        return subcategories
    
    def convert_tag_to_ids(self, tag_entry: List[List[str]]) -> List[Dict[str, Any]]:
        """
        Convert a tag entry to ID format.
        
        Args:
            tag_entry: List containing [category_name, subcategory_string] pairs
            
        Returns:
            List of dictionaries with category_id and subcategory_ids
        """
        converted_tags = []
        
        for category_subcategory_pair in tag_entry:
            if len(category_subcategory_pair) != 2:
                print(f"Warning: Invalid tag format: {category_subcategory_pair}")
                continue
            
            category_name = category_subcategory_pair[0].strip()
            subcategory_string = category_subcategory_pair[1].strip()
            
            # Get category ID
            if category_name not in self.category_map:
                print(f"Warning: Category '{category_name}' not found in index")
                continue
            
            category_id = self.category_map[category_name]
            
            # Parse and convert subcategories
            subcategory_names = self.parse_subcategories(subcategory_string)
            subcategory_ids = []
            
            for subcategory_name in subcategory_names:
                if subcategory_name in self.subcategory_map:
                    subcategory_ids.append(self.subcategory_map[subcategory_name])
                else:
                    print(f"Warning: Subcategory '{subcategory_name}' not found in index")
            
            # Create the converted tag entry
            converted_tag = {
                "tag_id": category_id,
                "sub_id": subcategory_ids,
            }
            
            converted_tags.append(converted_tag)
        
        return converted_tags
    
    def process_researcher_data(self, input_file: str, output_file: str):
        """
        Process the entire researcher data file and convert tags to IDs.
        
        Args:
            input_file: Path to input JSON file
            output_file: Path to output JSON file
        """
        try:
            with open(input_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            processed_data = {}
            total_processed = 0
            total_with_tags = 0
            
            for source_name, source_data in data.items():
                print(f"Processing {source_name}...")
                
                processed_source = source_data.copy()
                processed_profiles = []
                
                for profile in source_data.get('cleaned_profiles', []):
                    processed_profile = profile.copy()
                    
                    if 'tag' in profile and profile['tag']:
                        total_with_tags += 1
                        # Convert tags to IDs
                        processed_profile['tag_ids'] = self.convert_tag_to_ids(profile['tag'])
                        # Remove original tag field
                        if 'tag' in processed_profile:
                            del processed_profile['tag']
                    else:
                        processed_profile['tag_ids'] = []
                    
                    processed_profiles.append(processed_profile)
                    total_processed += 1
                
                processed_source['cleaned_profiles'] = processed_profiles
                processed_data[source_name] = processed_source
            
            # Save processed data
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(processed_data, f, ensure_ascii=False, indent=2)
            
            print(f"\nProcessing complete!")
            print(f"Total profiles processed: {total_processed}")
            print(f"Profiles with tags: {total_with_tags}")
            print(f"Output saved to: {output_file}")
            
        except FileNotFoundError:
            print(f"Error: Input file '{input_file}' not found.")
            sys.exit(1)
        except json.JSONDecodeError as e:
            print(f"Error: Invalid JSON in input file '{input_file}': {e}")
            sys.exit(1)


def main():
    parser = argparse.ArgumentParser(description='Convert tag information to tag IDs')
    parser.add_argument('input_file', help='Input JSON file with researcher data')
    parser.add_argument('output_file', help='Output JSON file with tag IDs')
    parser.add_argument('--index-file', default='../index/index_en.json',
                       help='Index file with category/subcategory mappings (default: ../index/index_en.json)')
    
    args = parser.parse_args()
    
    # Initialize converter
    converter = TagToIdConverter(args.index_file)
    
    # Process the data
    converter.process_researcher_data(args.input_file, args.output_file)


if __name__ == "__main__":
    # python3 tag_to_id_converter.py ../data/cleaned_researcher_data.json ../data/out.json --index-file ../index/index_en.json
    main()
