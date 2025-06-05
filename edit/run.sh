#!/bin/bash

# Check for input folder argument
if [ $# -ne 2 ]; then
  echo "Usage: $0 <input_folder> <output_folder>"
  exit 1
fi

INPUT_FOLDER="$1"
OUTPUT_FOLDER="$2"
ontology="/Users/ckindman/projects/open-neuro/annotation/ontologies/open_neuro_mesh.owl"
script_path="/Users/ckindman/projects/open-neuro/annotation/pipeline/text2vocab"

# Make sure the folder exists
if [ ! -d "$INPUT_FOLDER" ]; then
  echo "Error: '$INPUT_FOLDER' is not a directory"
  exit 1
fi

if [ ! -d "$OUTPUT_FOLDER" ]; then
  echo "Error: '$OUTPUT_FOLDER' is not a directory"
  exit 1
fi

# Iterate over files in the folder
for file in "$INPUT_FOLDER"/*; do
  if [ -f "$file" ]; then
    echo "Processing $file..."
    filename=$(basename $file)
    #python3.11 __main__.py extract -i $file -o $OUTPUT_FOLDER/$filename
    python3.11 $script_path/__main__.py map -i $file -ont $ontology -t 0.9 -o $OUTPUT_FOLDER/$filename
    #python3.11 __main__.py annotate -i $file -o $OUTPUT_FOLDER/$filename
  fi
done
