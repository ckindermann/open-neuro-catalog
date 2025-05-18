#!/usr/bin/env python3
"""
Script to validate vocabulary TSV files against defined ID ranges.

- Parses an `id_ranges.tsv` file with columns:
  - `category` (str)
  - `lower_bound` (int)
  - `upper_bound` (int)
  - `next_id` (int, not used here)

- Recursively searches a target directory for `.tsv` files with columns:
  - `term` (str)
  - `vocabulary_id` (str of form ONVOC:XXXXXXX)
  - `mapping_id` (str)
  - `comment` (str)

- Validates that:
  1. Each `term` maps to exactly one valid `vocabulary_id`.
  2. For any TSV located under a folder named after a category in `id_ranges.tsv`,
     the numeric part of each `vocabulary_id` (prefix stripped) falls within
     the specified `lower_bound` and `upper_bound` for that category.

Exits with status code 1 if any checks fail, otherwise prints success message.
"""
import argparse
import csv
import os
import re
import sys

def parse_id_ranges(path):
    """
    Parse id_ranges.tsv into a dict mapping category to (lower, upper) bounds.
    """
    ranges = {}
    with open(path, newline='') as fh:
        reader = csv.DictReader(fh, delimiter='\t')
        for row in reader:
            category = row['category'].strip()
            try:
                lower = int(row['lower_bound'])
                upper = int(row['upper_bound'])
            except ValueError:
                print(
                    f"Invalid bounds for category '{category}': ``{row['lower_bound']}``-``{row['upper_bound']}``",
                    file=sys.stderr,
                )
                continue
            ranges[category] = (lower, upper)
    return ranges


def find_tsv_files(root_dir):
    """
    Yield paths to all .tsv files under `root_dir` recursively.
    """
    for dirpath, _, filenames in os.walk(root_dir):
        for fname in filenames:
            if fname.lower().endswith('.tsv'):
                yield os.path.join(dirpath, fname)


def main():
    parser = argparse.ArgumentParser(
        description='Validate TSV vocabularies against ID ranges',
    )
    parser.add_argument(
        'id_ranges',
        help='Path to id_ranges.tsv containing category bounds',
    )
    parser.add_argument(
        'target_dir',
        help='Target directory to recursively search for .tsv files',
    )
    args = parser.parse_args()

    # Load category bounds
    id_ranges = parse_id_ranges(args.id_ranges)

    # Regex to match ONVOC: followed by exactly 7 digits
    vocab_pattern = re.compile(r"^ONVOC:(\d{7})$")

    # Track mapping of term -> set of vocabulary_ids
    term_to_ids = {}

    # Flag to indicate any errors found
    errors_found = False

    # Process each TSV file
    for tsv_path in find_tsv_files(args.target_dir):
        # Determine which categories apply based on ancestor folder names
        ancestors = os.path.normpath(tsv_path).split(os.sep)
        applicable_cats = set(c for c in ancestors if c in id_ranges)

        with open(tsv_path, newline='') as fh:
            reader = csv.DictReader(fh, delimiter='\t')
            for lineno, row in enumerate(reader, start=2):
                term = row.get('term', '').strip()
                vid = row.get('vocabulary_id', '').strip()

                # Validate vocabulary_id format
                m = vocab_pattern.match(vid)
                if not m:
                    print(
                        f"{tsv_path}:{lineno}: Invalid vocabulary_id '{vid}' for term '{term}'",
                        file=sys.stderr,
                    )
                    errors_found = True
                    continue

                # Extract numeric part
                num_id = int(m.group(1))

                # Check bounds for each applicable category
                for cat in applicable_cats:
                    lower, upper = id_ranges[cat]
                    if not (lower <= num_id <= upper):
                        print(
                            f"{tsv_path}:{lineno}: vocabulary_id {vid} for term '{term}' "
                            f"out of range for category '{cat}' ({lower}-{upper})",
                            file=sys.stderr,
                        )
                        errors_found = True

                # Record term<->id mapping
                term_to_ids.setdefault(term, set()).add(vid)

    # Ensure each term maps to exactly one vocabulary_id
    for term, vids in sorted(term_to_ids.items()):
        if len(vids) != 1:
            print(
                f"Term '{term}' has multiple vocabulary_ids: {sorted(vids)}",
                file=sys.stderr,
            )
            errors_found = True

    if errors_found:
        sys.exit(1)
    else:
        print("All vocabulary checks passed successfully.")


if __name__ == '__main__':
    main()
