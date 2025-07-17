#!/usr/bin/env python3
"""
Map controlled‐vocabulary terms to an external ontology via text2term,
using the Mapped Term CURIE directly.

Usage:
    python3 map_with_text2term_curie.py \
        --vocab /path/to/vocab_root \
        --ontology UBERON \
        --threshold 0.7 \
        --output mappings_curie.tsv

Requires:
    pandas, text2term
"""

import os
import argparse
import text2term
import pandas as pd

def read_lines_from_file(file_path: str) -> list[str]:
    with open(file_path, "r", encoding="utf-8") as f:
        return [line.strip() for line in f if line.strip()]

def map_entities_to_terms(entities: list[str], ontology : str, threshold : float) -> pd.DataFrame:
    df = text2term.map_terms(source_terms=entities,
                             min_score=threshold,
                             target_ontology=ontology)
    return df

def load_vocabulary_terms(vocab_root: str) -> pd.DataFrame:
    """
    Traverse vocab_root and collect (vocabulary_term, vocabulary_id) from each *.tsv
    under each category (skipping Categories.tsv and Subcategories.tsv).
    Returns a DataFrame with columns ["vocabulary_term","vocabulary_id"].
    """
    records = []
    for category in os.listdir(vocab_root):
        cat_dir = os.path.join(vocab_root, category)
        if not os.path.isdir(cat_dir):
            continue
        for fname in os.listdir(cat_dir):
            if not fname.lower().endswith(".tsv") or fname in ("Categories.tsv", "Subcategories.tsv"):
                continue
            path = os.path.join(cat_dir, fname)
            df = pd.read_csv(path, sep="\t", dtype=str)
            # expect columns "term" and "vocabulary_id"
            df = df[["term", "vocabulary_id"]].dropna(subset=["term","vocabulary_id"])
            records.append(df.rename(columns={"term": "vocabulary_term"}))
    if not records:
        return pd.DataFrame(columns=["vocabulary_term","vocabulary_id"])
    return pd.concat(records, ignore_index=True)

def main():
    parser = argparse.ArgumentParser(
        description="Map vocabulary terms to an ontology via text2term, using the CURIE."
    )
    parser.add_argument(
        "--vocab", required=True,
        help="Root folder of the controlled vocabulary (with TSV files)."
    )
    parser.add_argument(
        "--ontology", required=True,
        help="Target ontology name for text2term.map_terms (e.g. 'MeSH', 'UBERON')."
    )
    parser.add_argument(
        "--threshold", type=float, default=0.7,
        help="Score threshold for text2term (default: 0.7)."
    )
    parser.add_argument(
        "--output", default="mappings_curie.tsv",
        help="Output TSV file (default: mappings_curie.tsv)."
    )
    args = parser.parse_args()

    vocab_root = os.path.abspath(args.vocab)
    if not os.path.isdir(vocab_root):
        raise NotADirectoryError(f"{vocab_root} is not a directory.")

    # 1) load vocabulary terms
    vocab_df = load_vocabulary_terms(vocab_root)
    if vocab_df.empty:
        print("No vocabulary terms found.", file=sys.stderr)
        return

    # 2) map via t2t
    #    map_entities_to_terms(...) must return a DataFrame with at least these cols:
    #      "Source Term ID","Source Term","Mapped Term Label","Mapped Term CURIE"
    mapping_df = map_entities_to_terms(
        vocab_df["vocabulary_term"].tolist(),
        ontology=args.ontology,
        threshold=args.threshold
    )

    # 3) join on vocabulary_id == Source Term ID
    merged = pd.merge(
        vocab_df,
        mapping_df,
        left_on="vocabulary_term",
        right_on="Source Term",
        how="left"
    )

    # fill unmapped with empty strings
    merged["Mapped Term Label"].fillna("", inplace=True)
    merged["Mapped Term CURIE"].fillna("", inplace=True)

    # 4) write out
    out = merged[[
        "vocabulary_term",
        "vocabulary_id",
        "Mapped Term Label",
        "Mapped Term CURIE"
    ]].rename(columns={
        "Mapped Term Label": "mapped_term_label",
        "Mapped Term CURIE": "mapped_term_curie"
    })
    out.to_csv(args.output, sep="\t", index=False)

    print(f"Mappings (with CURIE) written to {args.output}")

if __name__ == "__main__":
    main()
