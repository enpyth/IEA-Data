mv output output_$(date +%Y%m%d%H%M%S)
mkdir output

# extract ./tag_data/*.json, save to ./output/extracted_data.json
python3 extract_demo.py

# clean ./output/extracted_data.json, save to ./output/cleaned_data.json
python3 clean_data.py

# convert tag to id in ./output/cleaned_data.json, save to ./output/tag_data.json
python3 tag_to_id_converter.py

# export CSVs for PostgreSQL insertion
python3 json_to_csv_for_pg.py