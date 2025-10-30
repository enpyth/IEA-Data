## Data processing tools

This project converts JSON files to CSV for database data imports.

## How to use it

1. prepare env

    $ pyenv local 3.11.6

2. raw data 

    download json files to ./tag_data

3. exec

    $ cd scripts; sh run.sh

## Core steps

1. extract

    extract n item from each ./tag_data/*.json
    
2. clean 
    
    - standardize all the json to one structure
    - remove `\n` 
    - use eamil as orcid if orcid is null

3. convert tag to id 

    read index to map, then convert the text to id

4. export CSV for PostgreSQL insertion

    refer to table strcture of academic_products and tags, convert the taged json to csv.
