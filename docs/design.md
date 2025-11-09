# IEA Data Processing Pipeline

This project processes academic researcher profile data from JSON files and converts them into CSV format for PostgreSQL database import. The pipeline extracts, cleans, standardizes, and transforms researcher data from multiple Australian universities.

## Overview

The data processing pipeline consists of four main steps:
1. **Extract**: Combines researcher profiles from multiple university JSON files
2. **Clean**: Standardizes data structure, validates fields, and removes invalid records
3. **Convert Tags**: Maps tag categories to numeric IDs using index files
4. **Export CSV**: Generates PostgreSQL-ready CSV files for database import

## Project Structure

```
IEA-Data/
├── tag_data/              # Input JSON files (one per university)
│   ├── University Name tag.json
│   └── ...
├── index/                 # Tag mapping index files
│   ├── index_en.json      # English tag index
│   └── index_cn.json      # Chinese tag index
├── scripts/              # Processing scripts
│   ├── extract_demo.py           # Extracts data from JSON files
│   ├── clean_data.py              # Cleans and standardizes data
│   ├── tag_to_id_converter.py    # Converts tags to IDs
│   ├── json_to_csv_for_pg.py      # Exports CSV files
│   ├── run.sh                     # Main execution script
│   └── output/                    # Generated output files
│       ├── extracted_data.json    # Combined extracted data
│       ├── cleaned_data.json      # Cleaned and standardized data
│       ├── tag_data.json          # Data with tag IDs
│       ├── academic_products.csv  # PostgreSQL-ready CSV
│       └── tags.csv               # PostgreSQL-ready CSV
└── README.md
```

## Prerequisites

- Python 3.11.6 (or compatible version)
- pyenv (optional, for Python version management)

## Setup

1. **Set Python version** (if using pyenv):
   ```bash
   pyenv local 3.11.6
   ```

2. **Prepare input data**:
   - Download university JSON files to `./tag_data/` directory
   - Each file should be named: `[University Name] tag.json`

## Usage

### Quick Start

Execute the complete pipeline:

```bash
cd scripts
bash run.sh
```

This will:
1. Remove existing output files
2. Extract data from all JSON files in `tag_data/`
3. Clean and standardize the extracted data
4. Convert tags to numeric IDs
5. Generate CSV files for PostgreSQL import

### Pipeline Steps

#### 1. Extract (`extract_demo.py`)

- Reads all JSON files from `./tag_data/*.json`
- Extracts researcher profiles from each file
- Combines all profiles into `./output/extracted_data.json`
- Normalizes university names (removes trailing " tag" suffix)

**Input**: `./tag_data/*.json`  
**Output**: `./output/extracted_data.json`

#### 2. Clean (`clean_data.py`)

Performs data cleaning and standardization:

- **Field standardization**: Normalizes all fields to a consistent structure:
  - `website`, `full_name`, `title`, `org_unit`, `telephone`, `email`
  - `introduction` (renamed from `brief_introduction`)
  - `orcid`, `tag`
  
- **Data cleaning**:
  - Removes newlines (`\n`) from introduction text
  - Validates email addresses
  - Extracts ORCID IDs from URLs
  - Falls back to email if ORCID is missing or invalid
  - **Removes records with empty ORCID** (no valid ORCID and no valid email)
  - Standardizes telephone numbers
  - Cleans tag structures

- **University key normalization**: Removes " tag" suffix from university names

**Input**: `./output/extracted_data.json`  
**Output**: `./output/cleaned_data.json`  
**Note**: Records without ORCID/email are skipped and reported in statistics

#### 3. Convert Tags (`tag_to_id_converter.py`)

- Maps tag categories and subcategories to numeric IDs using `index/index_en.json`
- Converts tag text to `tag_id` and `sub_id` format
- Filters out profiles with empty email addresses
- Removes original tag field, adds `tag_ids` field

**Input**: `./output/cleaned_data.json`  
**Output**: `./output/tag_data.json`  
**Dependencies**: `../index/index_en.json`

#### 4. Export CSV (`json_to_csv_for_pg.py`)

Generates two CSV files for PostgreSQL import:

**`academic_products.csv`**:
- Columns: `orcid`, `profiles` (JSONB), `introduction`
- Contains all profile data except `orcid`, `introduction`, and `tags`
- Profiles without ORCID are skipped

**`tags.csv`**:
- Columns: `orcid`, `tag_id`, `sub_id`
- One row per tag/subcategory combination
- Links to `academic_products` via `orcid`

**Input**: `./output/tag_data.json`  
**Output**: 
- `./output/academic_products.csv`
- `./output/tags.csv`

## Output Files

### JSON Files

- **`extracted_data.json`**: Raw combined data from all university files
- **`cleaned_data.json`**: Standardized and cleaned data
- **`tag_data.json`**: Data with tag IDs converted

### CSV Files (PostgreSQL Ready)

- **`academic_products.csv`**: Main researcher profiles
- **`tags.csv`**: Tag associations

## PostgreSQL Schema

The CSV files are designed for these tables:

```sql
CREATE TABLE public.academic_products (
    orcid VARCHAR(50) PRIMARY KEY,
    profiles JSONB DEFAULT '{}',
    introduction TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE public.tags (
    id SERIAL PRIMARY KEY,
    orcid VARCHAR(50) NOT NULL REFERENCES public.academic_products(orcid) ON DELETE CASCADE,
    tag_id INTEGER NOT NULL,
    sub_id INTEGER NOT NULL
);
```

### Importing to PostgreSQL

```sql
COPY public.academic_products (orcid, profiles, introduction)
FROM '/path/to/scripts/output/academic_products.csv'
WITH (FORMAT csv, HEADER true);

COPY public.tags (orcid, tag_id, sub_id)
FROM '/path/to/scripts/output/tags.csv'
WITH (FORMAT csv, HEADER true);
```

## Data Cleaning Features

- **ORCID handling**: 
  - Extracts ORCID from URLs if present
  - Validates ORCID format
  - Uses email as fallback if ORCID is missing
  - **Removes records with no ORCID and no email**

- **Text cleaning**:
  - Removes newlines from introduction text
  - Trims whitespace from all fields
  - Validates email format

- **Tag processing**:
  - Standardizes tag structure
  - Maps to numeric IDs using index files
  - Handles missing or invalid tags gracefully

## Statistics

The pipeline reports:
- Number of universities processed
- Total profiles processed
- Profiles successfully cleaned
- Profiles skipped (no ORCID/email)
- Sample output preview

## Troubleshooting

1. **No input files found**: Ensure JSON files are in `./tag_data/` with correct naming
2. **Index file not found**: Check that `index/index_en.json` exists
3. **Empty output**: Verify input JSON files contain valid researcher data
4. **CSV import errors**: Ensure CSV files are UTF-8 encoded and paths are correct

## Notes

- All scripts use UTF-8 encoding to handle international characters
- The pipeline skips invalid records rather than failing
- University names are normalized (trailing " tag" removed)
- Profiles without ORCID or email are automatically filtered out
