#!/usr/bin/env python3
"""
Map controlled vocabulary terms to MeSH using SciSpacy’s EntityLinker.

This version picks the highest-scoring candidate and uses `canonical_name`.

Usage:
    python3 map_to_mesh.py --vocab /path/to/vocab_root --output mappings.tsv
"""

import os
import csv
import argparse

import spacy
import scispacy
from scispacy.linking import EntityLinker

def load_vocabulary_terms(vocab_root):
    pairs = []
    for category in os.listdir(vocab_root):
        cat_dir = os.path.join(vocab_root, category)
        if not os.path.isdir(cat_dir):
            continue
        for fname in os.listdir(cat_dir):
            if not fname.lower().endswith(".tsv") or fname in ("Categories.tsv", "Subcategories.tsv"):
                continue
            path = os.path.join(cat_dir, fname)
            with open(path, encoding="utf-8") as fp:
                reader = csv.DictReader(fp, delimiter="\t")
                for row in reader:
                    term = row.get("term", "").strip()
                    vid  = row.get("vocabulary_id", "").strip()
                    if term and vid:
                        pairs.append((term, vid))
    return pairs

def map_term_to_mesh(nlp, term):
    """
    Run the SciSpacy pipeline on `term`, returning the best mapping as
    (mesh_term, mesh_id) or ("", "") if no candidate.
    """
    doc = nlp(term)
    candidates = [(cui, score) for ent in doc.ents for cui, score in ent._.kb_ents]
    if not candidates:
        return "", ""

    best_cui = max(candidates, key=lambda x: x[1])[0]
    linker = nlp.get_pipe("scispacy_linker")
    entity = linker.kb.cui_to_entity[best_cui]
    # canonical_name holds the preferred label
    return entity.canonical_name, best_cui

def main():
    parser = argparse.ArgumentParser(
        description="Map vocabulary terms to MeSH via SciSpacy EntityLinker."
    )
    parser.add_argument("--vocab",    required=True,
                        help="Root of controlled vocabulary (with TSV files).")
    parser.add_argument("--output", default="mappings.tsv",
                        help="Output TSV (default: mappings.tsv).")
    args = parser.parse_args()

    vocab_root = os.path.abspath(args.vocab)
    if not os.path.isdir(vocab_root):
        raise NotADirectoryError(f"{vocab_root} is not a directory.")

    print("Loading SciSpacy model and UMLS EntityLinker...")
    #nlp = spacy.load("en_core_sci_sm")
    nlp = spacy.load("en_core_sci_lg")
    nlp.add_pipe(
        "scispacy_linker",
        config={"resolve_abbreviations": True, "linker_name": "mesh"}
    )

    vocab_pairs = load_vocabulary_terms(vocab_root)

    with open(args.output, "w", newline="", encoding="utf-8") as out_fp:
        writer = csv.writer(out_fp, delimiter="\t")
        writer.writerow(["vocabulary_term", "vocabulary_id", "mesh_term", "mesh_id"])
        for term, vid in vocab_pairs:
            mesh_term, mesh_id = map_term_to_mesh(nlp, term)
            writer.writerow([term, vid, mesh_term, mesh_id])

    print(f"Mapping complete. Results written to {args.output}")

if __name__ == "__main__":
    main()
