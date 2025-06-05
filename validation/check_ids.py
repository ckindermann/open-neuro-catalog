#!/usr/bin/env python3
"""
Validate one-to-one correspondence between terms and vocabulary IDs across all TSV files
under a given root directory. Every term should map to exactly one ID, and every ID should
map to exactly one term.

Conventions:
  - All TSV files have a header row with columns: term, vocabulary_id, mapping_id, comment
  - Terms appear in the first column, IDs in the second column.
  - We scan all files ending in “.tsv” recursively under the specified root.

Usage:
    python3 check_term_id_uniqueness.py --root /path/to/tsv_root
"""

import os
import csv
import argparse
import sys

def collect_term_id_pairs(root_dir: str):
    """
    Traverse root_dir recursively and collect all (term, vocabulary_id) pairs
    from every *.tsv file found. Returns two dicts:
      - term_to_ids: { term_str: set([id1, id2, ...]) }
      - id_to_terms: { id_str: set([term1, term2, ...]) }
    """
    term_to_ids = {}
    id_to_terms = {}

    for dirpath, _, filenames in os.walk(root_dir):
        for fname in filenames:
            if not fname.lower().endswith(".tsv"):
                continue
            file_path = os.path.join(dirpath, fname)
            with open(file_path, encoding="utf-8") as fp:
                reader = csv.reader(fp, delimiter="\t")
                header = next(reader, None)
                if not header or len(header) < 2:
                    # Skip files that do not have at least two columns
                    continue

                # Identify index of 'term' and 'vocabulary_id' columns (by header name)
                # Fallback: assume term is column 0, vocab_id is column 1
                try:
                    term_idx = header.index("term")
                    id_idx = header.index("vocabulary_id")
                except ValueError:
                    term_idx = 0
                    id_idx = 1

                for row in reader:
                    if len(row) <= id_idx:
                        continue
                    term = row[term_idx].strip()
                    vid = row[id_idx].strip()
                    if not term or not vid:
                        continue

                    term_to_ids.setdefault(term, set()).add(vid)
                    id_to_terms.setdefault(vid, set()).add(term)

    return term_to_ids, id_to_terms


def main(root: str):
    term_to_ids, id_to_terms = collect_term_id_pairs(root)
    violations = False

    # Check for terms that map to multiple IDs
    for term, ids in sorted(term_to_ids.items()):
        if len(ids) > 1:
            violations = True
            print(f"[Term] '{term}' has multiple IDs: {sorted(ids)}")

    # Check for IDs that map to multiple terms
    for vid, terms in sorted(id_to_terms.items()):
        if len(terms) > 1:
            violations = True
            print(f"[ID] '{vid}' is assigned to multiple terms: {sorted(terms)}")

    if not violations:
        print("All terms and vocabulary IDs have a one-to-one correspondence.")
    else:
        sys.exit(1)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Check that every term maps to exactly one vocabulary_id and "
                    "every vocabulary_id maps to exactly one term."
    )
    parser.add_argument(
        "--root",
        required=True,
        help="Root directory containing TSV files to validate."
    )
    args = parser.parse_args()

    if not os.path.isdir(args.root):
        print(f"ERROR: “{args.root}” is not a directory or does not exist.", file=sys.stderr)
        sys.exit(1)

    main(args.root)
