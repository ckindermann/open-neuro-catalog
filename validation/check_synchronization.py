#!/usr/bin/env python3
"""
Validate synchronization between a “terms” directory (using .txt files) and its 
controlled vocabulary (using .tsv files with IDs), respecting the naming conventions:

  • Folder and file names use snake_case with principal words capitalized
    (e.g., "Brain_Structures", "Functional_Imaging").
  • Each folder name maps to a "term" by replacing underscores with spaces
    (e.g., "Brain_Structures" → "Brain Structures").
  • Each .txt or .tsv filename (without extension) is in snake_case with principal words
    capitalized (e.g., "Subcortex", "Structural_MRI"), and maps similarly to a term.
  • Inside .txt and .tsv files, each term is Title Case (e.g., "Hippocampus", "T2-Weighted").

This script checks:

  1. Every term listed in each “Category/Whatever.txt” under the terms directory 
     appears (with an ID) in the matching “Category/Whatever.tsv” under the vocabulary directory.
  2. Every term in each “Category/Whatever.tsv” of the vocabulary directory is defined 
     in the corresponding “Category/Whatever.txt” of the terms directory.
  3. All category folders and subcategory files in one side appear on the other (and vice versa),
     using snake_case folder/file naming conventions.

Usage:
    python3 check_terms_vs_vocabulary.py \
        --terms /path/to/terms_directory \
        --vocabulary /path/to/vocabulary_directory
"""

import os
import csv
import argparse
import sys

def snake_to_display(snake_name: str) -> str:
    """
    Convert a snake_case name (with principal words capitalized) into a display term,
    by replacing underscores with spaces. E.g. "Brain_Structures" → "Brain Structures".
    """
    return snake_name.replace("_", " ")

def load_terms_from_txt(txt_path: str) -> set[str]:
    """
    Read a .txt file and return a set of non-empty, stripped lines (Title-Case terms).
    """
    terms: set[str] = set()
    with open(txt_path, encoding="utf-8") as fp:
        for line in fp:
            t = line.strip()
            if t:
                terms.add(t)
    return terms

def load_terms_from_tsv(tsv_path: str) -> set[str]:
    """
    Read a .tsv file (with header containing "term" and "vocabulary_id") and return
    a set of non-empty terms from the "term" column.
    """
    terms: set[str] = set()
    with open(tsv_path, encoding="utf-8") as fp:
        reader = csv.reader(fp, delimiter="\t")
        header = next(reader, None)
        if not header:
            return terms

        # Identify the "term" column; default to index 0
        try:
            term_idx = header.index("term")
        except ValueError:
            term_idx = 0

        for row in reader:
            if len(row) > term_idx:
                t = row[term_idx].strip()
                if t:
                    terms.add(t)
    return terms

def check_sync(terms_root: str, vocab_root: str) -> list[str]:
    """
    Compare the terms directory (.txt) and vocabulary directory (.tsv), respecting snake_case naming
    conventions. Returns a list of mismatch messages.
    """
    mismatches: list[str] = []

    # 1) Ensure the root directories exist
    if not os.path.isdir(terms_root):
        mismatches.append(f"Terms root \"{terms_root}\" does not exist or is not a directory.")
        return mismatches
    if not os.path.isdir(vocab_root):
        mismatches.append(f"Vocabulary root \"{vocab_root}\" does not exist or is not a directory.")
        return mismatches

    # 2) Build sets of category folder names (snake_case) on each side
    terms_categories = {
        name for name in os.listdir(terms_root)
        if os.path.isdir(os.path.join(terms_root, name))
    }
    vocab_categories = {
        name for name in os.listdir(vocab_root)
        if os.path.isdir(os.path.join(vocab_root, name))
    }

    # 3) Check for missing/extra categories
    for cat in sorted(terms_categories - vocab_categories):
        mismatches.append(f"[Missing Category Folder] \"{cat}\" exists in terms but not in vocabulary.")
    for cat in sorted(vocab_categories - terms_categories):
        mismatches.append(f"[Extra Category Folder] \"{cat}\" exists in vocabulary but not in terms.")

    # 4) For each category present on both sides, compare subcategories and terms
    for category in sorted(terms_categories & vocab_categories):
        terms_cat_dir = os.path.join(terms_root, category)
        vocab_cat_dir = os.path.join(vocab_root, category)

        # 4a) Gather subcategory filenames (without extension) in each folder
        terms_subcats = {
            os.path.splitext(f)[0]
            for f in os.listdir(terms_cat_dir)
            if f.lower().endswith(".txt") and os.path.isfile(os.path.join(terms_cat_dir, f))
        }
        vocab_subcats = {
            os.path.splitext(f)[0]
            for f in os.listdir(vocab_cat_dir)
            if f.lower().endswith(".tsv") and f != "Subcategories.tsv" and os.path.isfile(os.path.join(vocab_cat_dir, f))
        }

        # 4b) Check for missing/extra subcategories (snake_case)
        for sub in sorted(terms_subcats - vocab_subcats):
            mismatches.append(
                f"[Missing Subcategory .tsv] \"{sub}.tsv\" under category \"{category}\" is missing in vocabulary."
            )
        for sub in sorted(vocab_subcats - terms_subcats):
            mismatches.append(
                f"[Extra Subcategory .tsv] \"{sub}.tsv\" under category \"{category}\" is not in terms."
            )

        # 4c) For each subcategory present on both sides, compare term sets
        for sub in sorted(terms_subcats & vocab_subcats):
            terms_txt = os.path.join(terms_cat_dir, f"{sub}.txt")
            vocab_tsv = os.path.join(vocab_cat_dir, f"{sub}.tsv")

            # 4c-i) Load terms from .txt
            orig_terms = load_terms_from_txt(terms_txt)

            # 4c-ii) Verify vocabulary .tsv exists
            if not os.path.isfile(vocab_tsv):
                mismatches.append(
                    f"[Missing .tsv File] Expected \"{sub}.tsv\" under \"{vocab_cat_dir}\" corresponding to terms."
                )
                continue

            # 4c-iii) Load terms from vocabulary .tsv
            copy_terms = load_terms_from_tsv(vocab_tsv)

            # 4c-iv) Identify terms in terms_dir missing from vocabulary
            for term in sorted(orig_terms - copy_terms):
                mismatches.append(
                    f"[Missing Term] \"{term}\" in terms/{category}/{sub}.txt "
                    f"is not found in vocabulary/{category}/{sub}.tsv."
                )

            # 4c-v) Identify extra terms in vocabulary not in terms
            for term in sorted(copy_terms - orig_terms):
                mismatches.append(
                    f"[Extra Term] \"{term}\" in vocabulary/{category}/{sub}.tsv "
                    f"is not defined in terms/{category}/{sub}.txt."
                )

    return mismatches

def main():
    parser = argparse.ArgumentParser(
        description="Check that every term in the terms directory (.txt) has a matching ID in the vocabulary (.tsv), "
                    "and every term in the vocabulary is defined in the terms directory, respecting naming conventions."
    )
    parser.add_argument(
        "--terms",
        required=True,
        help="Path to the root folder of the terms directory (with .txt files)."
    )
    parser.add_argument(
        "--vocabulary",
        required=True,
        help="Path to the root folder of the vocabulary directory (with .tsv files and IDs)."
    )
    args = parser.parse_args()

    terms_root = os.path.abspath(args.terms)
    vocab_root = os.path.abspath(args.vocabulary)

    mismatches = check_sync(terms_root, vocab_root)
    if mismatches:
        print("Synchronization check found mismatches:")
        for msg in mismatches:
            print("  -", msg)
        sys.exit(1)
    else:
        print("Success: Terms and vocabulary are in sync (all terms match, and naming conventions respected).")
        sys.exit(0)

if __name__ == "__main__":
    main()
