#!/usr/bin/env python3
"""
This script reads a TSV file with columns: term, vocabulary_id, mapping_id, comment,
and generates a CSV file containing RDF triples for each term/vocabulary_id.

Usage:
    python generate_rdf_csv.py input_file.tsv output_folder
"""
import argparse
import csv
import os
import sys

def main():
    parser = argparse.ArgumentParser(
        description="Generate RDF CSV from TSV input."
    )
    parser.add_argument(
        "input_file",
        help="Path to input TSV file"
    )
    parser.add_argument(
        "output_folder",
        help="Path to output folder"
    )
    args = parser.parse_args()

    input_file = args.input_file
    output_folder = args.output_folder

    # Validate input file
    if not os.path.isfile(input_file):
        sys.exit(f"Error: Input file '{input_file}' does not exist.")

    # Ensure output folder exists
    os.makedirs(output_folder, exist_ok=True)

    # Determine output file path
    base_name = os.path.splitext(os.path.basename(input_file))[0]
    output_file = os.path.join(output_folder, f"{base_name}.csv")

    # Process TSV and write RDF CSV
    with open(input_file, newline="", encoding="utf-8") as tsvfile, \
         open(output_file, "w", newline="", encoding="utf-8") as csvfile:
        reader = csv.DictReader(tsvfile, delimiter="\t")
        writer = csv.writer(csvfile)

        for row in reader:
            term = row.get("term", "").replace("_", " ")
            vid = row.get("vocabulary_id", "")

            # Write the required RDF triples
            writer.writerow([vid, "rdf:type", "owl:NamedIndividual", "_IRI"])
            writer.writerow([vid, "rdf:type", "skos:Concept", "_IRI"])
            writer.writerow([vid, "skos:inScheme", "ONVOC:test", "_IRI"])
            writer.writerow([vid, "skos:prefLabel", term, "xsd:string"])

    print(f"RDF CSV file written to '{output_file}'")

if __name__ == "__main__":
    main()
