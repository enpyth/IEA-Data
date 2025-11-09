#!/usr/bin/env python3
"""
Data cleaning script to standardize the structure of researcher profiles
from the combined_first_five.json file.
"""

import json
import re
from pathlib import Path
from typing import Dict, List, Any, Union

def clean_and_standardize_data(input_file: str, output_file: str, if_ignore_no_orcid: bool = True):
    """
    Clean and standardize the data structure from the combined JSON file.
    
    Args:
        input_file: Path to the input JSON file
        output_file: Path to the output cleaned JSON file
        if_ignore_no_orcid: If True, skip records without ORCID. If False, use email as ORCID fallback.
    """
    
    # Define the standard structure for each researcher profile
    standard_fields = {
        "website": "",
        "full_name": "",
        "title": "",
        "org_unit": "",
        "telephone": "",
        "email": "",
        "introduction": "",
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
    
    def clean_orcid_field(value: Union[str, None], email_value: Union[str, None] = None, use_email_fallback: bool = False) -> tuple[str, bool]:
        """
        Clean and standardize ORCID field.
        
        Returns:
            Tuple of (orcid_value, is_real_orcid) where is_real_orcid is True if it's a valid ORCID,
            False if it's an email fallback or empty.
        """
        if value is None:
            value = ""
        orcid = str(value).strip()
        # Extract ORCID ID from URL if present
        if "orcid.org" in orcid:
            match = re.search(r'(\d{4}-\d{4}-\d{4}-\d{3}[\dX])', orcid)
            if match:
                return (match.group(1), True)
        elif re.match(r'^\d{4}-\d{4}-\d{4}-\d{3}[\dX]$', orcid):
            return (orcid, True)
        # Not valid orcid: use cleaned email instead if fallback is enabled
        if use_email_fallback and email_value:
            return (str(email_value).strip(), False)
        return ("", False)
    
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

    def normalize_university_key(name: str) -> str:
        """Normalize university key by removing trailing ' tag'."""
        if not isinstance(name, str):
            return str(name)
        # Remove a single trailing ' tag' (with optional preceding whitespace)
        return re.sub(r"\s+tag$", "", name).strip()
    
    def standardize_researcher_profile(profile: Dict[str, Any], use_email_fallback: bool = False) -> tuple[Dict[str, Any], bool]:
        """
        Standardize a single researcher profile.
        
        Returns:
            Tuple of (standardized_profile, is_real_orcid) where is_real_orcid indicates
            if the profile has a valid ORCID (not email fallback).
        """
        standardized = standard_fields.copy()
        
        # Map and clean each field (except orcid)
        field_mappings = {
            "website": clean_string_field,
            "full_name": clean_string_field,
            "title": clean_string_field,
            "org_unit": clean_string_field,
            "telephone": clean_telephone_field,
            "email": clean_email_field,
            "brief_introduction": clean_string_field,  # source key -> output 'introduction'
            "tag": clean_tag_field
        }
        
        for field, cleaner_func in field_mappings.items():
            if field in profile:
                output_field = "introduction" if field == "brief_introduction" else field
                cleaned_val = cleaner_func(profile[field])
                if output_field == "introduction" or output_field == "org_unit":
                    cleaned_val = cleaned_val.replace("\n", " ")
                standardized[output_field] = cleaned_val
        
        # Handle ORCID
        email_val = standardized.get("email", "")
        orcid_val = profile.get("orcid", None)
        cleaned_orcid, is_real_orcid = clean_orcid_field(orcid_val, email_val, use_email_fallback)
        standardized["orcid"] = cleaned_orcid

        return (standardized, is_real_orcid)
    
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
    skipped_profiles = 0
    
    for university_key, university_data in data.items():
        if "extracted_items" not in university_data:
            continue
        
        university_cleaned = {
            "total_items": university_data.get("total_items", 0),
            "profiles": []
        }
        
        for profile in university_data["extracted_items"]:
            total_profiles += 1
            use_email_fallback = not if_ignore_no_orcid
            cleaned_profile, is_real_orcid = standardize_researcher_profile(profile, use_email_fallback)
            
            # Skip profiles based on flag:
            # - If if_ignore_no_orcid is True: skip records without real ORCID
            # - If if_ignore_no_orcid is False: only skip if no ORCID and no email fallback
            if if_ignore_no_orcid:
                # Skip if no real ORCID
                if not is_real_orcid:
                    skipped_profiles += 1
                    continue
            else:
                # Skip if no ORCID at all (even email fallback)
                if not cleaned_profile.get("orcid"):
                    skipped_profiles += 1
                    continue
            
            university_cleaned["profiles"].append(cleaned_profile)
            cleaned_profiles += 1
        
        # Only include university if it has profiles after filtering
        if len(university_cleaned["profiles"]) > 0:
            cleaned_data[normalize_university_key(university_key)] = university_cleaned
    
    # Write the cleaned data
    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(cleaned_data, f, indent=2, ensure_ascii=False)
        
        print(f"✅ Successfully cleaned and standardized data!")
        print(f"📊 Statistics:")
        print(f"   - Universities processed: {len(cleaned_data)}")
        print(f"   - Total profiles: {total_profiles}")
        print(f"   - Profiles cleaned: {cleaned_profiles}")
        if if_ignore_no_orcid:
            print(f"   - Profiles skipped (no real ORCID): {skipped_profiles}")
        else:
            print(f"   - Profiles skipped (no ORCID/email): {skipped_profiles}")
        print(f"   - Output file: {output_file}")
        
        # Show sample of cleaned data
        if cleaned_data:
            first_university = list(cleaned_data.keys())[0]
            first_profile = cleaned_data[first_university]["profiles"][0]
            print(f"\n📋 Sample cleaned profile from {first_university}:")
            for field, value in first_profile.items():
                if field == "introduction":
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
    input_file = "./output/extracted_data.json"
    output_file = "./output/cleaned_data.json"
    if_ignore_no_orcid = True
    # Check if input file exists
    if not Path(input_file).exists():
        print(f"❌ Input file '{input_file}' not found!")
        print("Please run extract_demo.py first to generate the combined data.")
        return
    
    print("🧹 Starting data cleaning and standardization process...")
    if if_ignore_no_orcid:
        print("   Mode: Ignoring records without real ORCID")
    else:
        print("   Mode: Using email as ORCID fallback")
    clean_and_standardize_data(input_file, output_file, if_ignore_no_orcid)

if __name__ == "__main__":
    main()
