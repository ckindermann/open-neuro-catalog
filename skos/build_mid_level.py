#!/usr/bin/env python3
"""
Generate SKOS RDF triples (in CSV form) from a Categories.tsv and its per-term TSV files.

Usage:
    python make_skos.py /path/to/input_folder /path/to/output_folder
"""

import os
import csv
import argparse
import sys

def main():
    parser = argparse.ArgumentParser(
        description="Generate SKOS triples from Categories.tsv and child TSVs."
    )
    parser.add_argument("input_folder", help="Folder containing Categories.tsv and per-term TSV files")
    parser.add_argument("output_folder", help="Folder where output.csv will be written")
    args = parser.parse_args()

    in_dir = args.input_folder
    out_dir = args.output_folder
    cat_file = os.path.join(in_dir, "Categories.tsv")
    out_file = os.path.join(out_dir, "mid_level.csv")

    # ensure input exists
    if not os.path.isdir(in_dir):
        print(f"Error: input folder '{in_dir}' does not exist.", file=sys.stderr)
        sys.exit(1)
    if not os.path.isfile(cat_file):
        print(f"Error: '{cat_file}' not found.", file=sys.stderr)
        sys.exit(1)

    # create output folder if needed
    os.makedirs(out_dir, exist_ok=True)

    # open output CSV
    with open(out_file, "w", newline='', encoding="utf-8") as fout:
        writer = csv.writer(fout)
        
        # read Categories.tsv
        with open(cat_file, "r", newline='', encoding="utf-8") as fin:
            reader = csv.DictReader(fin, delimiter='\t')
            for cat in reader:
                raw_term = cat["term"]
                parent_id = cat["vocabulary_id"]
                # transform term for label (underscores -> space)
                label = raw_term.replace("_", " ")
                
                # write the four basic triples
                writer.writerow([parent_id, "rdf:type",       "owl:NamedIndividual", "_IRI"])
                writer.writerow([parent_id, "rdf:type",       "skos:Concept",        "_IRI"])
                writer.writerow([parent_id, "skos:inScheme",  "ONVOC:test",          "_IRI"])
                writer.writerow([parent_id, "skos:prefLabel", label,                  "xsd:string"])
                
                # now process its child TSV
                child_file = os.path.join(in_dir, f"{raw_term}.tsv")
                if not os.path.isfile(child_file):
                    # warn and skip if no file
                    print(f"Warning: expected child file '{child_file}' not found; skipping narrower/broader for '{raw_term}'.", 
                          file=sys.stderr)
                    continue

                with open(child_file, "r", newline='', encoding="utf-8") as cfin:
                    child_reader = csv.DictReader(cfin, delimiter='\t')
                    for row in child_reader:
                        child_id = row["vocabulary_id"]
                        # write skos:narrower and skos:broader
                        writer.writerow([parent_id,    "skos:narrower", child_id, "_IRI"])
                        writer.writerow([child_id,     "skos:broader",  parent_id, "_IRI"])

    print(f"Wrote SKOS triples to '{out_file}'.")

if __name__ == "__main__":
    main()
