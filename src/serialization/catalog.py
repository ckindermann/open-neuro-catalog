#!/usr/bin/env python3
"""
Transform a controlled vocabulary folder (with TSV files & IDs) into a JSON tree.

Each node in the tree has:
  - id:           the vocabulary_id
  - label:        the term (from the TSV)
  - children:     list of child nodes (subcategories or leaf terms)

Usage:
    python3 vocab_to_json_tree.py --vocab /path/to/vocab_root --output tree.json
"""

import os
import csv
import json
import argparse

def load_tsv(filepath):
    """
    Load a TSV with a header row; return a list of dictionaries keyed by column names.
    """
    items = []
    with open(filepath, encoding="utf-8") as fp:
        reader = csv.DictReader(fp, delimiter="\t")
        for row in reader:
            items.append(row)
    return items

def snake_from_label(label):
    """
    Convert a display label back to the folder/file base name: replace spaces with underscores.
    """
    return label.replace(" ", "_")

def build_tree(vocab_root):
    """
    Build the JSON tree from the vocabulary directory.
    """
    tree = []

    # 1) Load categories
    cats_path = os.path.join(vocab_root, "Categories.tsv")
    if not os.path.isfile(cats_path):
        raise FileNotFoundError(f"Missing Categories.tsv at {vocab_root}")
    categories = load_tsv(cats_path)

    for cat in categories:
        cat_label = cat["term"]
        cat_id    = cat["vocabulary_id"]
        cat_node  = {
            "id": cat_id,
            "label": cat_label,
            "children": []
        }

        # 2) Load subcategories for this category
        cat_folder = os.path.join(vocab_root, snake_from_label(cat_label))
        subcats_tsv = os.path.join(cat_folder, "Subcategories.tsv")
        if os.path.isfile(subcats_tsv):
            subcats = load_tsv(subcats_tsv)
            for sub in subcats:
                sub_label = sub["term"]
                sub_id    = sub["vocabulary_id"]
                sub_node  = {
                    "id": sub_id,
                    "label": sub_label,
                    "children": []
                }

                # 3) Load leaf terms under this subcategory
                leaf_tsv = os.path.join(
                    cat_folder,
                    f"{snake_from_label(sub_label)}.tsv"
                )
                if os.path.isfile(leaf_tsv):
                    leaves = load_tsv(leaf_tsv)
                    for leaf in leaves:
                        leaf_label = leaf["term"]
                        leaf_id    = leaf["vocabulary_id"]
                        leaf_node  = {
                            "id": leaf_id,
                            "label": leaf_label,
                            "children": []
                        }
                        sub_node["children"].append(leaf_node)

                cat_node["children"].append(sub_node)

        tree.append(cat_node)

    return tree

def main():
    parser = argparse.ArgumentParser(
        description="Convert a controlled vocabulary folder into a JSON tree."
    )
    parser.add_argument(
        "--vocab",
        required=True,
        help="Path to the controlled vocabulary root (with Categories.tsv, subfolders, etc.)"
    )
    parser.add_argument(
        "--output",
        default="vocab_tree.json",
        help="Output JSON file (default: vocab_tree.json)"
    )
    args = parser.parse_args()

    vocab_root = os.path.abspath(args.vocab)
    tree = build_tree(vocab_root)

    with open(args.output, "w", encoding="utf-8") as fp:
        json.dump(tree, fp, indent=2, ensure_ascii=False)

    print(f"JSON tree written to {args.output}")

if __name__ == "__main__":
    main()
