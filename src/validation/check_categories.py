#!/usr/bin/env python3
"""
Validate that each term listed in Categories.tsv and Subcategories.tsv has a corresponding
folder or .tsv file in the target directory, and vice versa. Ensures all required TSV files
exist in the correct locations.

Usage:
    python3 check_cv_structure.py --vocabulary /path/to/tsv_vocabulary
"""

import os
import csv
import argparse
import sys

def load_terms_from_tsv(tsv_path, term_column_name="term"):
    """
    Read a TSV file and return a list of term strings from the specified column.
    If the header does not contain term_column_name, assume the first column is "term".
    """
    terms = []
    with open(tsv_path, encoding="utf-8") as fp:
        reader = csv.reader(fp, delimiter="\t")
        header = next(reader, None)
        if not header:
            return terms
        try:
            term_idx = header.index(term_column_name)
        except ValueError:
            term_idx = 0
        for row in reader:
            if len(row) > term_idx:
                term = row[term_idx].strip()
                if term:
                    terms.append(term)
    return terms

def validate_structure(vocabulary):
    errors = []

    # 1) Check that Categories.tsv exists at vocabulary
    categories_tsv = os.path.join(vocabulary, "Categories.tsv")
    if not os.path.isfile(categories_tsv):
        errors.append(f"Missing Categories.tsv in vocabulary: {vocabulary}")
        return errors  # cannot proceed further without Categories.tsv

    # 2) Load category terms from Categories.tsv
    category_terms = load_terms_from_tsv(categories_tsv)

    # 3) Build expected folder names from category terms (spaces → underscores)
    expected_folders = {term.replace(" ", "_") for term in category_terms}

    # 4) List actual folders at vocabulary (ignore files)
    actual_items = os.listdir(vocabulary)
    actual_folders = {name for name in actual_items if os.path.isdir(os.path.join(vocabulary, name))}

    # 5) Check that every expected folder exists
    for folder in sorted(expected_folders):
        if folder not in actual_folders:
            errors.append(f"Category listed in Categories.tsv not found as folder: '{folder}'")

    # 6) Check that every folder under vocabulary is listed in Categories.tsv
    for folder in sorted(actual_folders):
        if folder not in expected_folders:
            errors.append(f"Extra folder under vocabulary not in Categories.tsv: '{folder}'")

    # 7) For each category folder, validate Subcategories.tsv and .tsv files
    for category in sorted(expected_folders.intersection(actual_folders)):
        cat_dir = os.path.join(vocabulary, category)

        # a) Check Subcategories.tsv exists
        subcats_tsv = os.path.join(cat_dir, "Subcategories.tsv")
        if not os.path.isfile(subcats_tsv):
            errors.append(f"Missing Subcategories.tsv in category folder: '{cat_dir}'")
            continue

        # b) Load subcategory terms
        subcat_terms = load_terms_from_tsv(subcats_tsv)

        # c) Expected subcategory TSV filenames (spaces → underscores + ".tsv")
        expected_subcat_files = {term.replace(" ", "_") + ".tsv" for term in subcat_terms}

        # d) List actual .tsv files in category folder (excluding Subcategories.tsv)
        all_files = os.listdir(cat_dir)
        actual_tsv_files = {
            fname for fname in all_files
            if fname.lower().endswith(".tsv") and fname != "Subcategories.tsv"
        }

        # e) Verify each expected .tsv file exists
        for fname in sorted(expected_subcat_files):
            if fname not in actual_tsv_files:
                errors.append(f"Subcategory '{fname}' listed in {subcats_tsv} missing in folder '{cat_dir}'")

        # f) Verify no extra .tsv files exist
        for fname in sorted(actual_tsv_files):
            if fname not in expected_subcat_files:
                errors.append(f"Extra .tsv file in '{cat_dir}' not listed in Subcategories.tsv: '{fname}'")

    return errors

def main():
    parser = argparse.ArgumentParser(
        description="Check that Categories.tsv and Subcategories.tsv terms correspond to folders and .tsv files."
    )
    parser.add_argument(
        "--vocabulary",
        required=True,
        help="Path to the vocabulary directory containing Categories.tsv and category folders."
    )
    args = parser.parse_args()

    vocabulary = os.path.abspath(args.vocabulary)
    if not os.path.isdir(vocabulary):
        print(f"ERROR: “{vocabulary}” is not a directory or does not exist.", file=sys.stderr)
        sys.exit(1)

    errors = validate_structure(vocabulary)
    if errors:
        print("Validation errors found:")
        for e in errors:
            print(f"  - {e}")
        sys.exit(1)
    else:
        print("All categories and subcategories match the folder/.tsv structure.")
        sys.exit(0)

if __name__ == "__main__":
    main()
