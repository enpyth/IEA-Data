#!/usr/bin/env python3
"""
Data cleaning script to standardize the structure of researcher profiles
from the combined_first_five.json file.
"""

import json
import re
from pathlib import Path
from typing import Dict, List, Any, Union

def clean_and_standardize_data(input_file: str, output_file: str):
    """
    Clean and standardize the data structure from the combined JSON file.
    
    Args:
        input_file: Path to the input JSON file
        output_file: Path to the output cleaned JSON file
    """
    
    # Define the standard structure for each researcher profile
    standard_fields = {
        "website": "",
        "full_name": "",
        "title": "",
        "org_unit": "",
        "telephone": "",
        "email": "",
        "brief_introduction": "",
        "orcid": "",
        "tag": []
    }
    
    def clean_string_field(value: Union[str, List, None]) -> str:
        """Clean and standardize string fields."""
        if value is None:
            return ""
        if isinstance(value, list):
            # Join list items with semicolon separator
            return "; ".join(str(item).strip() for item in value if item)
        return str(value).strip()
    
    def clean_telephone_field(value: Union[str, List, None]) -> str:
        """Clean and standardize telephone field."""
        if value is None:
            return ""
        
        if isinstance(value, list):
            # Join multiple phone numbers
            phones = []
            for phone in value:
                if phone and isinstance(phone, str):
                    phones.append(phone.strip())
            return "; ".join(phones)
        
        return str(value).strip()
    
    def clean_email_field(value: Union[str, None]) -> str:
        """Clean and standardize email field."""
        if value is None:
            return ""
        
        email = str(value).strip()
        # Basic email validation
        if "@" in email and "." in email.split("@")[-1]:
            return email
        return ""
    
    def clean_orcid_field(value: Union[str, None]) -> str:
        """Clean and standardize ORCID field."""
        if value is None:
            return ""
        
        orcid = str(value).strip()
        # Extract ORCID ID from URL if present
        if "orcid.org" in orcid:
            match = re.search(r'(\d{4}-\d{4}-\d{4}-\d{3}[\dX])', orcid)
            if match:
                return match.group(1)
        elif re.match(r'^\d{4}-\d{4}-\d{4}-\d{3}[\dX]$', orcid):
            return orcid
        
        return ""
    
    def clean_tag_field(value: Union[List, None]) -> List[List[str]]:
        """Clean and standardize tag field."""
        if value is None:
            return []
        
        if not isinstance(value, list):
            return []
        
        cleaned_tags = []
        for tag_group in value:
            if isinstance(tag_group, list) and len(tag_group) >= 2:
                category = str(tag_group[0]).strip()
                subcategories = str(tag_group[1]).strip()
                if category and subcategories:
                    cleaned_tags.append([category, subcategories])
        
        return cleaned_tags
    
    def standardize_researcher_profile(profile: Dict[str, Any]) -> Dict[str, Any]:
        """Standardize a single researcher profile."""
        standardized = standard_fields.copy()
        
        # Map and clean each field
        field_mappings = {
            "website": clean_string_field,
            "full_name": clean_string_field,
            "title": clean_string_field,
            "org_unit": clean_string_field,
            "telephone": clean_telephone_field,
            "email": clean_email_field,
            "brief_introduction": clean_string_field,
            "orcid": clean_orcid_field,
            "tag": clean_tag_field
        }
        
        for field, cleaner_func in field_mappings.items():
            if field in profile:
                standardized[field] = cleaner_func(profile[field])
        
        return standardized
    
    # Read the input file
    try:
        with open(input_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except FileNotFoundError:
        print(f"Error: Input file '{input_file}' not found!")
        return
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON in input file: {e}")
        return
    
    # Process and clean the data
    cleaned_data = {}
    total_profiles = 0
    cleaned_profiles = 0
    
    for university_key, university_data in data.items():
        if "extracted_items" not in university_data:
            continue
        
        university_cleaned = {
            "source_file": university_data.get("source_file", ""),
            "total_items": university_data.get("total_items", 0),
            "cleaned_profiles": []
        }
        
        for profile in university_data["extracted_items"]:
            total_profiles += 1
            cleaned_profile = standardize_researcher_profile(profile)
            university_cleaned["cleaned_profiles"].append(cleaned_profile)
            cleaned_profiles += 1
        
        cleaned_data[university_key] = university_cleaned
    
    # Write the cleaned data
    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(cleaned_data, f, indent=2, ensure_ascii=False)
        
        print(f"✅ Successfully cleaned and standardized data!")
        print(f"📊 Statistics:")
        print(f"   - Universities processed: {len(cleaned_data)}")
        print(f"   - Total profiles: {total_profiles}")
        print(f"   - Profiles cleaned: {cleaned_profiles}")
        print(f"   - Output file: {output_file}")
        
        # Show sample of cleaned data
        if cleaned_data:
            first_university = list(cleaned_data.keys())[0]
            first_profile = cleaned_data[first_university]["cleaned_profiles"][0]
            print(f"\n📋 Sample cleaned profile from {first_university}:")
            for field, value in first_profile.items():
                if field == "brief_introduction":
                    preview = value[:100] + "..." if len(value) > 100 else value
                    print(f"   {field}: {preview}")
                elif field == "tag":
                    print(f"   {field}: {len(value)} tag groups")
                else:
                    print(f"   {field}: {value}")
        
    except Exception as e:
        print(f"Error writing output file: {e}")

def main():
    """Main function to run the data cleaning process."""
    input_file = "combined_first_five.json"
    output_file = "cleaned_researcher_data.json"
    
    # Check if input file exists
    if not Path(input_file).exists():
        print(f"❌ Input file '{input_file}' not found!")
        print("Please run extract_demo.py first to generate the combined data.")
        return
    
    print("🧹 Starting data cleaning and standardization process...")
    clean_and_standardize_data(input_file, output_file)

if __name__ == "__main__":
    main()
