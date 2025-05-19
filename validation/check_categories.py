#!/usr/bin/env python3
"""
Script to verify that each term listed in Categories.tsv has a corresponding .tsv file or
folder in the target directory, and vice versa. Ensures Categories.tsv exists but does not
require 'Categories' to be a term.
"""
import argparse
import csv
import sys
from pathlib import Path


def parse_categories(categories_path: Path) -> set[str]:
    """
    Parse the Categories.tsv file and return a set of terms.

    Args:
        categories_path: Path to the Categories.tsv file.

    Returns:
        A set of term strings.
    """
    terms = set()
    with categories_path.open(newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f, delimiter='\t')
        required_fields = {'term', 'vocabulary_id', 'mapping_id', 'comment'}
        if not required_fields.issubset(reader.fieldnames or []):
            missing = required_fields - set(reader.fieldnames or [])
            sys.exit(f"Error: Categories.tsv is missing columns: {', '.join(missing)}")
        for row in reader:
            term = row['term'].strip()
            if term and term != 'Categories':
                terms.add(term)
    return terms


def find_entities(target_dir: Path) -> tuple[set[str], set[str], set[str]]:
    """
    Find .tsv files (excluding Categories.tsv) and folders in the target directory.

    Args:
        target_dir: Path to the target directory.

    Returns:
        A tuple of three sets:
          - tsv_names: stems of .tsv files (excluding Categories.tsv)
          - dir_names: names of subdirectories
          - all_entities: union of tsv_names and dir_names
    """
    tsv_names = {p.stem for p in target_dir.glob('*.tsv') if p.name != 'Categories.tsv'}
    dir_names = {p.name for p in target_dir.iterdir() if p.is_dir()}
    all_entities = tsv_names.union(dir_names)
    return tsv_names, dir_names, all_entities


def report_discrepancies(target: Path, terms: set[str], tsv_names: set[str], dir_names: set[str], entities: set[str]) -> None:
    """
    Compare terms to existing entities and print missing and extra items.

    Args:
        target: Path to the target directory.
        terms: Set of expected term names.
        tsv_names: Set of .tsv file stems.
        dir_names: Set of directory names.
        entities: Union of tsv_names and dir_names.
    """
    missing = terms - entities
    extra = entities - terms

    if missing:
        print("Missing .tsv file or folder for these terms:")
        for term in sorted(missing):
            print(f"  - {term}.tsv or folder named '{term}'")
    else:
        print("✔ All terms have corresponding .tsv files or folders.")

    if extra:
        print("\nExtra .tsv files or folders without matching terms:")
        for name in sorted(extra):
            if name in tsv_names:
                print(f"  - {name}.tsv")
            elif name in dir_names:
                print(f"  - folder '{name}/'")
    else:
        print("✔ No extra .tsv files or folders found.")


def main():
    parser = argparse.ArgumentParser(
        description="Verify .tsv files or folders correspond to terms in Categories.tsv"
    )
    parser.add_argument(
        'target_folder',
        type=Path,
        help='Path to the folder containing Categories.tsv and .tsv files or term-named folders'
    )
    args = parser.parse_args()
    target = args.target_folder

    # Ensure Categories.tsv exists
    categories_file = target / 'Categories.tsv'
    if not categories_file.exists():
        sys.exit(f"Error: 'Categories.tsv' not found in {target}")

    # Parse terms
    terms = parse_categories(categories_file)

    # Find existing .tsv files and folders
    tsv_names, dir_names, entities = find_entities(target)

    # Report any mismatches
    report_discrepancies(target, terms, tsv_names, dir_names, entities)

if __name__ == '__main__':  # pragma: no cover
    main()
