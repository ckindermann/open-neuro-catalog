#!/usr/bin/env python3
"""
Extract MeSH terms from arbitrary text using SciSpacy, then filter to those present
in a user‐provided mapping file.

Given:
  --mapping /path/to/mappings.tsv   (columns: vocabulary_term, vocabulary_id, mesh_term, mesh_id)
  --text "Some input text..."       OR  --text-file /path/to/text.txt

This script will:
  1. Load the mapping file and build a set of allowed MeSH CUIs.
  2. Run SciSpacy’s UMLS EntityLinker on the input text.
  3. For each detected entity, choose the highest‐scoring candidate whose CUI
     appears in the mapping file.
  4. Output a TSV (to stdout or --output) with columns:
       entity_text    mesh_term    mesh_id

Usage:
    python3 extract_and_filter_mesh.py \
        --mapping mappings.tsv \
        --text "Spinal and bulbar muscular atrophy is ..." \
        [--output extracted.tsv]

    python3 extract_and_filter_mesh.py \
        --mapping mappings.tsv \
        --text-file document.txt \
        --output extracted.tsv

Requirements:
    pip install scispacy spacy
    pip install \
      https://s3-us-west-2.amazonaws.com/ai2-s2-scispacy/releases/v0.5.1/en_core_sci_sm-0.5.1.tar.gz
    pip install \
      https://s3-us-west-2.amazonaws.com/ai2-s2-scispacy/releases/v0.5.1/scispacy-0.5.1.tar.gz
"""

import os
import csv
import sys
import argparse

import spacy
import scispacy
from scispacy.linking import EntityLinker

def load_allowed_mesh(mapping_tsv):
    """
    Load mapping TSV and return dict mesh_id -> mesh_term for all rows.
    """
    allowed = {}
    with open(mapping_tsv, encoding="utf-8") as fp:
        reader = csv.DictReader(fp, delimiter="\t")
        for row in reader:
            mesh_id = row.get("mesh_id", "").strip()
            mesh_term = row.get("mesh_term", "").strip()
            if mesh_id:
                allowed[mesh_id] = mesh_term
    return allowed

def extract_and_filter(text, nlp, allowed_mesh):
    """
    Run SciSpacy on text, return list of (entity_text, mesh_term, mesh_id)
    for the best scoring candidate per entity that is in allowed_mesh.
    """
    doc = nlp(text)
    linker = nlp.get_pipe("scispacy_linker")
    results = []
    seen = set()  # avoid duplicates
    
    for ent in doc.ents:
        # collect candidates sorted by score descending
        cands = sorted(ent._.kb_ents, key=lambda x: x[1], reverse=True)
        for cui, score in cands:
            if cui in allowed_mesh:
                mesh_term = allowed_mesh[cui]
                key = (ent.text, cui)
                if key not in seen:
                    results.append((ent.text, mesh_term, cui))
                    seen.add(key)
                break
    return results

def main():
    parser = argparse.ArgumentParser(
        description="Extract MeSH entities from text and filter against a mapping TSV."
    )
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--text", help="Input text string.")
    group.add_argument("--text-file", help="Path to a text file to process.")
    parser.add_argument("--mapping", required=True,
                        help="TSV file with columns including mesh_id and mesh_term.")
    parser.add_argument("--output",
                        help="Output TSV file. Defaults to stdout.")
    args = parser.parse_args()

    # Read mapping
    mapping_path = os.path.abspath(args.mapping)
    if not os.path.isfile(mapping_path):
        sys.exit(f"ERROR: mapping file '{mapping_path}' not found.")
    allowed_mesh = load_allowed_mesh(mapping_path)
    if not allowed_mesh:
        sys.exit("ERROR: No mesh_id entries found in mapping file.")

    # Read input text
    if args.text:
        text = args.text
    else:
        txt_path = os.path.abspath(args.text_file)
        if not os.path.isfile(txt_path):
            sys.exit(f"ERROR: text file '{txt_path}' not found.")
        with open(txt_path, encoding="utf-8") as f:
            text = f.read()

    # Load model and linker
    print("Loading SciSpacy model and UMLS EntityLinker...", file=sys.stderr)
    nlp = spacy.load("en_core_sci_sm")
    nlp.add_pipe("scispacy_linker",
                 config={"resolve_abbreviations": True, "linker_name": "mesh"})

    # Extract and filter
    extracted = extract_and_filter(text, nlp, allowed_mesh)

    # Write output
    out_fp = open(args.output, "w", newline="", encoding="utf-8") if args.output else sys.stdout
    writer = csv.writer(out_fp, delimiter="\t")
    writer.writerow(["entity_text", "mesh_term", "mesh_id"])
    for ent_text, mesh_term, mesh_id in extracted:
        writer.writerow([ent_text, mesh_term, mesh_id])

    if args.output:
        out_fp.close()
        print(f"Extraction complete. Results written to {args.output}", file=sys.stderr)

if __name__ == "__main__":
    main()
