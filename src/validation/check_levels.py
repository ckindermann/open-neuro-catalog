#!/usr/bin/env python3
"""
Check that category and subcategory names do not appear as terms in any
of the vocabulary files (either .txt or .tsv).

Usage:
    python3 check_no_cat_sub_as_terms.py --vocab /path/to/vocab_root
"""

import os
import csv
import argparse
import sys

def snake_to_display(name: str) -> str:
    """
    Convert snake_case name to display form by replacing underscores with spaces.
    """
    return name.replace("_", " ")

def collect_forbidden_terms(vocab_root: str):
    """
    Scan the vocabulary directory structure to collect all category and
    subcategory display names. Returns a dict mapping display_name -> type.
    """
    forbidden = {}  # display_name -> ("Category" or "Subcategory")
    for category in sorted(os.listdir(vocab_root)):
        cat_dir = os.path.join(vocab_root, category)
        if not os.path.isdir(cat_dir):
            continue
        # Category
        disp_cat = snake_to_display(category)
        forbidden[disp_cat] = "Category"
        # Subcategories: look for .txt or .tsv files (excluding Subcategories.tsv)
        for fname in sorted(os.listdir(cat_dir)):
            base, ext = os.path.splitext(fname)
            if ext.lower() == ".txt" or (ext.lower() == ".tsv" and fname != "Subcategories.tsv"):
                disp_sub = snake_to_display(base)
                forbidden[disp_sub] = "Subcategory"
    return forbidden

def scan_terms(vocab_root: str, forbidden: dict):
    """
    Walk through all term files (.txt and .tsv) under vocab_root and check
    whether any term matches a forbidden display name.
    Returns a list of violation messages.
    """
    violations = []
    for dirpath, _, files in os.walk(vocab_root):
        for fname in files:
            path = os.path.join(dirpath, fname)
            base, ext = os.path.splitext(fname)
            # Determine file type
            if ext.lower() == ".txt":
                # skip metadata files if any
                if base.lower() in ("categories", "subcategories"):
                    continue
                with open(path, encoding="utf-8") as fp:
                    for lineno, line in enumerate(fp, start=1):
                        term = line.strip()
                        if term in forbidden:
                            vtype = forbidden[term]
                            violations.append(
                                f"{vtype} “{term}” occurs in {path} (line {lineno})"
                            )
            elif ext.lower() == ".tsv":
                # skip metadata TSVs
                if base in ("Categories", "Subcategories"):
                    continue
                with open(path, encoding="utf-8") as fp:
                    reader = csv.reader(fp, delimiter="\t")
                    header = next(reader, None)
                    if not header:
                        continue
                    # find term column
                    try:
                        term_idx = header.index("term")
                    except ValueError:
                        term_idx = 0
                    for rowno, row in enumerate(reader, start=2):
                        if len(row) > term_idx:
                            term = row[term_idx].strip()
                            if term in forbidden:
                                vtype = forbidden[term]
                                violations.append(
                                    f"{vtype} “{term}” occurs in {path} (row {rowno})"
                                )
    return violations

def main():
    parser = argparse.ArgumentParser(
        description="Ensure category and subcategory names do not appear as terms in the vocabulary files."
    )
    parser.add_argument(
        "--vocab",
        required=True,
        help="Path to the root of the vocabulary structure (folders with .txt or .tsv files)."
    )
    args = parser.parse_args()
    vocab_root = os.path.abspath(args.vocab)
    if not os.path.isdir(vocab_root):
        print(f"ERROR: “{vocab_root}” is not a directory.", file=sys.stderr)
        sys.exit(1)

    forbidden = collect_forbidden_terms(vocab_root)
    violations = scan_terms(vocab_root, forbidden)

    if violations:
        print("Found category/subcategory names used as terms:")
        for msg in violations:
            print("  -", msg)
        sys.exit(1)
    else:
        print("Success: No category or subcategory names occur as terms.")
        sys.exit(0)

if __name__ == "__main__":
    main()
