#!/usr/bin/env python3
"""
Synchronize an original controlled vocabulary (using .txt files) with its ID-enhanced copy
(using .tsv files). Ensures that:
  1. Any new categories (folders) in the original are added to the copy (Categories.tsv,
     category folder, and Subcategories.tsv).
  2. Any new subcategories (.txt files) under a category are added to the copy
     (Subcategories.tsv and an empty <subcat>.tsv in the category folder).
  3. Any terms in the original .txt files missing from the corresponding .tsv files in the
     copy are added with a new, unique vocabulary_id.
     
Usage:
    python3 sync_cv_full_structure.py \
        --original /path/to/original_controlled_vocabulary \
        --copy /path/to/copy_with_ids \
        --prefix CV

Assumptions:
  - Original structure:
        original_root/
        ├── Category_A/
        │   ├── Subcat_One.txt
        │   └── Subcat_Two.txt
        └── Category_B/
            └── Subcat_X.txt

    Each “.txt” contains one term per line.

  - Copy structure (already has IDs):
        copy_root/
        ├── Categories.tsv
        ├── Category_A/
        │   ├── Subcategories.tsv
        │   ├── Subcat_One.tsv
        │   └── Subcat_Two.tsv
        └── Category_B/
            ├── Subcategories.tsv
            └── Subcat_X.tsv

    Each leaf “.tsv” has columns: term, vocabulary_id, comment
    Categories.tsv has columns: term, vocabulary_id, comment
    Subcategories.tsv has columns: term, vocabulary_id, comment

  - Terms in .tsv are in column “term” and IDs in “vocabulary_id”.
  - IDs follow the format PREFIX:XXXXXXX (7-digit zero-padded). New IDs are allocated
    incrementally beyond the highest existing numeric part in copy_root.
"""

import os
import csv
import argparse
import re
import sys

def ensure_dir(path: str):
    """Create directory if it doesn’t exist."""
    os.makedirs(path, exist_ok=True)

def append_rows_to_tsv(tsv_path: str, new_rows: list[list[str]], header: list[str]):
    """
    Append new_rows (list of [term, vocabulary_id, comment]) to the TSV at tsv_path.
    If the file doesn’t exist, create it with header first.
    """
    ensure_dir(os.path.dirname(tsv_path))
    file_exists = os.path.isfile(tsv_path)
    mode = "a" if file_exists else "w"
    with open(tsv_path, mode, newline="", encoding="utf-8") as fp:
        writer = csv.writer(fp, delimiter="\t")
        if not file_exists:
            writer.writerow(header)
        for row in new_rows:
            writer.writerow(row)

def load_term_id_map(tsv_path: str) -> dict[str, str]:
    """
    Read a TSV file with header row containing “term” and “vocabulary_id”.
    Return a dict mapping term → vocabulary_id.
    If the file does not exist or is malformed, return empty dict.
    """
    if not os.path.isfile(tsv_path):
        return {}
    term_to_id: dict[str, str] = {}
    with open(tsv_path, encoding="utf-8") as fp:
        reader = csv.reader(fp, delimiter="\t")
        header = next(reader, None)
        if not header:
            return term_to_id
        try:
            term_idx = header.index("term")
            id_idx = header.index("vocabulary_id")
        except ValueError:
            # Fallback: assume term at 0, id at 1
            term_idx, id_idx = 0, 1
        for row in reader:
            if len(row) <= max(term_idx, id_idx):
                continue
            term = row[term_idx].strip()
            vid = row[id_idx].strip()
            if term and vid:
                term_to_id[term] = vid
    return term_to_id

def load_existing_id_counter(copy_root: str, prefix: str) -> int:
    """
    Traverse all *.tsv files under copy_root and gather existing vocabulary_id values
    of the form PREFIX:XXXXXXX. Return the maximum numeric value found (or 0 if none).
    """
    max_num = 0
    id_pattern = re.compile(rf"^{re.escape(prefix)}:(\d{{7}})$")
    for dirpath, _, filenames in os.walk(copy_root):
        for fname in filenames:
            if not fname.lower().endswith(".tsv"):
                continue
            path = os.path.join(dirpath, fname)
            with open(path, encoding="utf-8") as fp:
                reader = csv.reader(fp, delimiter="\t")
                header = next(reader, None)
                if not header:
                    continue
                # Find index of vocabulary_id, or default to 1
                try:
                    id_idx = header.index("vocabulary_id")
                except ValueError:
                    id_idx = 1
                for row in reader:
                    if len(row) <= id_idx:
                        continue
                    vid = row[id_idx].strip()
                    m = id_pattern.match(vid)
                    if m:
                        num = int(m.group(1))
                        if num > max_num:
                            max_num = num
    return max_num

def sync_full_structure(original_root: str, copy_root: str, prefix: str):
    """
    Ensure that every category, subcategory, and term in original_root appears in copy_root.
    - New categories: create folder, update Categories.tsv.
    - New subcategories: create/update Subcategories.tsv in category folder.
    - New terms: append to the correct <subcat>.tsv with a new ID.
    """
    # Step 1: Determine starting ID counter
    max_existing_id = load_existing_id_counter(copy_root, prefix)
    next_id_num = max_existing_id + 1

    # Step 2: Load existing categories from copy Root/Categories.tsv
    categories_tsv_path = os.path.join(copy_root, "Categories.tsv")
    category_to_id: dict[str, str] = {}
    if os.path.isfile(categories_tsv_path):
        category_to_id = load_term_id_map(categories_tsv_path)
    else:
        # If Categories.tsv is missing, create an empty file with header
        append_rows_to_tsv(categories_tsv_path, [], ["term", "vocabulary_id", "comment"])

    # Step 3: Load existing subcategories for each category
    subcategory_to_id: dict[str, dict[str, str]] = {}  # { category_term: { subcat_term: id, ... } }
    for category_term, _ in category_to_id.items():
        category_folder = category_term.replace(" ", "_")
        subcats_tsv = os.path.join(copy_root, category_folder, "Subcategories.tsv")
        sub_map = load_term_id_map(subcats_tsv)
        subcategory_to_id[category_term] = sub_map

    # Step 4: Traverse original categories
    for category_folder in sorted(os.listdir(original_root)):
        orig_cat_dir = os.path.join(original_root, category_folder)
        if not os.path.isdir(orig_cat_dir):
            continue

        category_term = category_folder.replace("_", " ")
        # 4a: If category not in copy, add it
        if category_term not in category_to_id:
            new_id = f"{prefix}:{next_id_num:07d}"
            next_id_num += 1
            append_rows_to_tsv(categories_tsv_path, [[category_term, new_id, ""]], ["term", "vocabulary_id", "comment"])
            category_to_id[category_term] = new_id
            print(f"Added new category '{category_term}' with ID {new_id} to {categories_tsv_path}")

            # Create the category folder and an empty Subcategories.tsv
            copy_cat_dir = os.path.join(copy_root, category_folder)
            ensure_dir(copy_cat_dir)
            subcats_tsv = os.path.join(copy_cat_dir, "Subcategories.tsv")
            append_rows_to_tsv(subcats_tsv, [], ["term", "vocabulary_id", "comment"])
            subcategory_to_id[category_term] = {}
        else:
            copy_cat_dir = os.path.join(copy_root, category_folder)
            # Ensure folder exists
            ensure_dir(copy_cat_dir)
            # Ensure Subcategories.tsv exists
            subcats_tsv = os.path.join(copy_cat_dir, "Subcategories.tsv")
            if not os.path.isfile(subcats_tsv):
                append_rows_to_tsv(subcats_tsv, [], ["term", "vocabulary_id", "comment"])
                subcategory_to_id[category_term] = {}
            elif category_term not in subcategory_to_id:
                subcategory_to_id[category_term] = load_term_id_map(subcats_tsv)

        # 4b: Process subcategories within this category
        for fname in sorted(os.listdir(orig_cat_dir)):
            if not fname.lower().endswith(".txt"):
                continue
            subcat_folder_name = os.path.splitext(fname)[0]  # e.g. "Subcat_One"
            subcat_term = subcat_folder_name.replace("_", " ")
            copy_cat_dir = os.path.join(copy_root, category_folder)
            subcats_tsv = os.path.join(copy_cat_dir, "Subcategories.tsv")

            # If subcategory not in copy's Subcategories.tsv, add it
            if subcat_term not in subcategory_to_id.get(category_term, {}):
                new_id = f"{prefix}:{next_id_num:07d}"
                next_id_num += 1
                append_rows_to_tsv(subcats_tsv, [[subcat_term, new_id, ""]], ["term", "vocabulary_id", "comment"])
                subcategory_to_id[category_term][subcat_term] = new_id
                print(f"Added subcategory '{subcat_term}' with ID {new_id} to {subcats_tsv}")
                # Create empty <subcat>.tsv
                copy_subcat_tsv = os.path.join(copy_cat_dir, f"{subcat_folder_name}.tsv")
                append_rows_to_tsv(copy_subcat_tsv, [], ["term", "vocabulary_id", "comment"])
            else:
                # Ensure the subcategory .tsv file exists
                copy_subcat_tsv = os.path.join(copy_cat_dir, f"{subcat_folder_name}.tsv")
                if not os.path.isfile(copy_subcat_tsv):
                    append_rows_to_tsv(copy_subcat_tsv, [], ["term", "vocabulary_id", "comment"])

            # 4c: Sync terms inside each subcategory
            orig_txt_path = os.path.join(orig_cat_dir, fname)
            copy_subcat_tsv = os.path.join(copy_cat_dir, f"{subcat_folder_name}.tsv")

            # Load existing term→ID map from the copy subcategory .tsv
            term_to_id_map = load_term_id_map(copy_subcat_tsv)

            # Read original terms
            orig_terms: list[str] = []
            with open(orig_txt_path, encoding="utf-8") as fp:
                for line in fp:
                    t = line.strip()
                    if t:
                        orig_terms.append(t)

            # Identify missing terms
            missing_terms = [t for t in orig_terms if t not in term_to_id_map]

            if missing_terms:
                new_rows: list[list[str]] = []
                for term in missing_terms:
                    new_id = f"{prefix}:{next_id_num:07d}"
                    next_id_num += 1
                    new_rows.append([term, new_id, ""])
                    print(f"  Adding term '{term}' with ID {new_id} to {copy_subcat_tsv}")
                append_rows_to_tsv(copy_subcat_tsv, new_rows, ["term", "vocabulary_id", "comment"])

    print("Synchronization complete.")

def main():
    parser = argparse.ArgumentParser(
        description="Ensure every category, subcategory, and term in the original .txt vocabulary "
                    "is present in the copy .tsv structure; add missing items with new IDs."
    )
    parser.add_argument(
        "--original",
        required=True,
        help="Path to the root folder of the original controlled vocabulary (with .txt files)."
    )
    parser.add_argument(
        "--copy",
        required=True,
        help="Path to the root folder of the copy (with .tsv files and IDs)."
    )
    parser.add_argument(
        "--prefix",
        default="ONVOC",
        help="Prefix used in vocabulary_id (default: ONVOC)."
    )
    args = parser.parse_args()

    orig = os.path.abspath(args.original)
    copy = os.path.abspath(args.copy)

    if not os.path.isdir(orig):
        print(f"ERROR: Original path '{orig}' is not a directory or does not exist.", file=sys.stderr)
        sys.exit(1)
    if not os.path.isdir(copy):
        print(f"ERROR: Copy path '{copy}' is not a directory or does not exist.", file=sys.stderr)
        sys.exit(1)

    sync_full_structure(orig, copy, args.prefix)

if __name__ == "__main__":
    main()
