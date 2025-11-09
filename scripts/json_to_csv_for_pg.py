#!/usr/bin/env python3
"""
Convert ./output/tag_data.json into CSVs suitable for PostgreSQL insertion.

Outputs:
  - ./output/academic_products.csv with columns: orcid, profiles (JSON), introduction
  - ./output/tags.csv with columns: orcid, tag_id, sub_id (int)

Notes:
  - Skips profiles without a non-empty ORCID (required by schema).
  - "profiles" JSON excludes 'orcid', 'introduction', and 'tags'.
  - Adds 'organization' field to profiles JSON with the university name from tag_data.json key.
  - Subcategory IDs like "8.2" are converted to integer 2; use with tag_id for uniqueness.
"""

import json
import csv
from pathlib import Path
from typing import Dict, Any, List


INPUT_FILE = "./output/tag_data.json"
OUTPUT_DIR = "./output"
ACADEMIC_PRODUCTS_CSV = f"{OUTPUT_DIR}/academic_products.csv"
TAGS_CSV = f"{OUTPUT_DIR}/tags.csv"


def load_json(path: str) -> Dict[str, Any]:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def extract_orcid(profile: Dict[str, Any]) -> str:
    value = profile.get("orcid")
    if value is None:
        return ""
    return str(value).strip()


def build_profiles_json(profile: Dict[str, Any], organization: str = "") -> Dict[str, Any]:
    profiles_obj = {}
    for key, value in profile.items():
        if key in {"orcid", "introduction", "tags"}:
            continue
        profiles_obj[key] = value
    # Add organization field
    if organization:
        profiles_obj["organization"] = organization
    return profiles_obj


def parse_sub_id_to_int(sub_id_value: Any) -> int:
    # Accept values like "8.2" or "2"; extract the part after the dot if present
    s = str(sub_id_value).strip()
    if "." in s:
        try:
            return int(s.split(".", 1)[1])
        except ValueError:
            pass
    try:
        return int(s)
    except ValueError:
        # Fallback: attempt to remove non-digits
        digits = "".join(ch for ch in s if ch.isdigit())
        return int(digits) if digits else 0


def process(input_path: str, products_csv: str, tags_csv: str) -> None:
    data = load_json(input_path)

    Path(OUTPUT_DIR).mkdir(parents=True, exist_ok=True)

    with open(products_csv, "w", encoding="utf-8", newline="") as prod_f, \
         open(tags_csv, "w", encoding="utf-8", newline="") as tags_f:
        products_writer = csv.writer(prod_f)
        tags_writer = csv.writer(tags_f)

        # Headers
        products_writer.writerow(["orcid", "profiles", "introduction"])
        tags_writer.writerow(["orcid", "tag_id", "sub_id"])

        for source_name, source_data in data.items():
            profiles: List[Dict[str, Any]] = source_data.get("profiles", [])
            for profile in profiles:
                orcid = extract_orcid(profile)
                if not orcid:
                    # Skip missing ORCID; cannot insert into schema
                    continue

                introduction = profile.get("introduction", "")
                profiles_json = build_profiles_json(profile, organization=source_name)
                profiles_str = json.dumps(profiles_json, ensure_ascii=False, separators=(",", ":"))

                # Write academic_products row
                products_writer.writerow([orcid, profiles_str, introduction])

                # Write tags rows
                tags_list = profile.get("tags", []) or []
                for tag_entry in tags_list:
                    tag_id = tag_entry.get("tag_id")
                    sub_ids = tag_entry.get("sub_id", []) or []
                    if tag_id is None:
                        continue
                    try:
                        tag_id_int = int(tag_id)
                    except (TypeError, ValueError):
                        continue
                    for sub in sub_ids:
                        sub_int = sub
                        tags_writer.writerow([orcid, tag_id_int, sub_int])


def main() -> None:
    if not Path(INPUT_FILE).exists():
        print(f"❌ Input file '{INPUT_FILE}' not found! Please run tag_to_id_converter.py first.")
        return
    print("📄 Converting tag_data.json to CSVs for PostgreSQL...")
    process(INPUT_FILE, ACADEMIC_PRODUCTS_CSV, TAGS_CSV)
    print("✅ Done.")
    print(f"   - Academic products: {ACADEMIC_PRODUCTS_CSV}")
    print(f"   - Tags: {TAGS_CSV}")


if __name__ == "__main__":
    main()


