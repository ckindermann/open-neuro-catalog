#!/usr/bin/env python3
"""
Convert a hierarchical controlled vocabulary (folders → text files → terms)
into a parallel TSV folder structure with additional metadata columns. The original
text files remain untouched; all TSV files are written under a separate output root.

This version assigns incremental IDs (PREFIX:XXXXXXX) but ensures that the same
string always receives the same ID. The “mapping_id” column is removed; each TSV
now has three columns: term, vocabulary_id, and comment.

Usage:
    python3 generate_cv_tsv_unique_ids.py \
        --input /path/to/Controlled_Vocabulary \
        --output /path/to/Output_TSVs \
        --prefix CV
"""

import os
import argparse
import csv
import itertools

def write_tsv(path: str, rows: list, header: list):
    """
    Write a list of rows (each row is a list of strings) to a TSV file at `path`.
    Creates parent directories if needed.
    """
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8") as fp:
        writer = csv.writer(fp, delimiter="\t")
        writer.writerow(header)
        for row in rows:
            writer.writerow(row)


def process_controlled_vocabulary(input_root: str, output_root: str, prefix: str):
    """
    Traverse each category folder under input_root, and under output_root produce:
      - output_root/Categories.tsv
      - For each category:
          • output_root/<category>/Subcategories.tsv
          • output_root/<category>/<subcategory>.tsv
    Ensures the same string always maps to the same incremental ID.
    Removes the mapping_id column; TSVs have columns: term, vocabulary_id, comment.
    """
    # Counter for incremental IDs
    id_counter = itertools.count(1)
    # Mapping from string → assigned ID
    string_to_id = {}

    def get_or_create_id(s: str) -> str:
        """
        Return the existing ID for string s, or create a new one if not seen yet.
        IDs have format PREFIX:XXXXXXX (7-digit zero-padded from counter).
        """
        if s not in string_to_id:
            next_id = next(id_counter)
            string_to_id[s] = f"{prefix}:{next_id:07d}"
        return string_to_id[s]

    # 1) Identify category subdirectories in input_root
    category_names = [
        name for name in os.listdir(input_root)
        if os.path.isdir(os.path.join(input_root, name))
    ]

    # 2) Build Categories.tsv rows
    categories_rows = []
    for category in sorted(category_names):
        term_display = category.replace("_", " ")
        vocab_id = get_or_create_id(term_display)
        categories_rows.append([term_display, vocab_id, ""])

    # Write Categories.tsv in output_root
    os.makedirs(output_root, exist_ok=True)
    categories_tsv_path = os.path.join(output_root, "Categories.tsv")
    write_tsv(
        categories_tsv_path,
        categories_rows,
        header=["term", "vocabulary_id", "comment"]
    )
    print(f"Written Categories.tsv → {categories_tsv_path}")

    # 3) Process each category folder
    for category in sorted(category_names):
        input_category_dir = os.path.join(input_root, category)
        output_category_dir = os.path.join(output_root, category)
        os.makedirs(output_category_dir, exist_ok=True)

        # 3a) Collect subcategory filenames
        subcategory_files = [
            fname for fname in os.listdir(input_category_dir)
            if fname.lower().endswith(".txt") and os.path.isfile(os.path.join(input_category_dir, fname))
        ]
        subcategory_names = [os.path.splitext(fname)[0] for fname in subcategory_files]

        # 3b) Build Subcategories.tsv rows
        subcategories_rows = []
        for subcat in sorted(subcategory_names):
            term_display = subcat.replace("_", " ")
            vocab_id = get_or_create_id(term_display)
            subcategories_rows.append([term_display, vocab_id, ""])

        subcategories_tsv_path = os.path.join(output_category_dir, "Subcategories.tsv")
        write_tsv(
            subcategories_tsv_path,
            subcategories_rows,
            header=["term", "vocabulary_id", "comment"]
        )
        print(f"Written Subcategories.tsv → {subcategories_tsv_path}")

        # 3c) Convert each .txt file into .tsv under output_category_dir
        for txt_fname in sorted(subcategory_files):
            subcat_name, _ = os.path.splitext(txt_fname)
            input_txt_path = os.path.join(input_category_dir, txt_fname)
            output_tsv_path = os.path.join(output_category_dir, f"{subcat_name}.tsv")

            # Read all non-empty lines (terms) from the .txt file
            terms = []
            with open(input_txt_path, "r", encoding="utf-8") as fp:
                for line in fp:
                    term = line.strip()
                    if term:
                        terms.append(term)

            # Build rows: [term, vocabulary_id, comment], reusing IDs if seen
            tsv_rows = []
            for term in terms:
                vocab_id = get_or_create_id(term)
                tsv_rows.append([term, vocab_id, ""])

            write_tsv(
                output_tsv_path,
                tsv_rows,
                header=["term", "vocabulary_id", "comment"]
            )
            print(f"  Converted {os.path.join(category, txt_fname)} → {output_tsv_path} ({len(tsv_rows)} terms)")

    print("Done processing controlled vocabulary.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Convert a controlled-vocabulary directory structure into a parallel TSV folder structure "
                    "while ensuring each unique string maps to exactly one ID, and removing mapping_id."
    )
    parser.add_argument(
        "--input",
        required=True,
        help="Path to the root folder of the controlled vocabulary (input)."
    )
    parser.add_argument(
        "--output",
        required=True,
        help="Path to the root folder where TSV files will be written."
    )
    parser.add_argument(
        "--prefix",
        default="ONVOC",
        help="Prefix to use for generating vocabulary_id (default: ONVOC)."
    )
    args = parser.parse_args()

    input_root = os.path.abspath(args.input)
    output_root = os.path.abspath(args.output)

    if not os.path.isdir(input_root):
        print(f"ERROR: The specified input path does not exist or is not a directory:\n  {input_root}")
        exit(1)

    process_controlled_vocabulary(input_root, output_root, args.prefix)
