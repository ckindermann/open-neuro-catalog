#!/usr/bin/env python3
"""
Validate mappings in the mappings/ folder against the vocabulary.

This script:
1. Loads all terms and IDs from the vocabulary/ folder
2. Reads all TSV files in the mappings/ folder
3. Checks if ONVOC IDs in vocabulary_id column are defined in vocabulary
4. Checks if vocabulary_term matches the term for that vocabulary_id in vocabulary
"""

import csv
from pathlib import Path
from typing import Dict, Set, List, Tuple
from collections import defaultdict


def load_vocabulary(vocab_dir: Path) -> Dict[str, str]:
    """
    Load all vocabulary terms and their IDs.

    Args:
        vocab_dir: Path to vocabulary directory

    Returns:
        Dictionary mapping ONVOC ID -> term
    """
    vocab_map = {}

    # Find all TSV files in vocabulary directory
    for tsv_file in vocab_dir.rglob('*.tsv'):
        # Skip files named 'Subcategories.tsv' as they may have different structure
        if tsv_file.name == 'Subcategories.tsv':
            continue

        try:
            with open(tsv_file, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f, delimiter='\t')

                for row in reader:
                    vocab_id = row.get('vocabulary_id', '').strip()
                    term = row.get('term', '').strip()

                    if vocab_id and term:
                        if vocab_id in vocab_map and vocab_map[vocab_id] != term:
                            print(f"    Warning: Duplicate ID {vocab_id} with different terms:")
                            print(f"    Existing: {vocab_map[vocab_id]}")
                            print(f"    New: {term} (in {tsv_file.relative_to(vocab_dir)})")
                        vocab_map[vocab_id] = term

        except Exception as e:
            print(f"  ✗ Error reading {tsv_file}: {e}")

    return vocab_map


def validate_mapping_file(mapping_file: Path, vocab_map: Dict[str, str]) -> Tuple[int, List[str], bool]:
    """
    Validate a single mapping file.

    Args:
        mapping_file: Path to mapping TSV file
        vocab_map: Dictionary of ONVOC ID -> term from vocabulary

    Returns:
        Tuple of (total_rows, list_of_errors, should_skip)
    """
    errors = []
    total_rows = 0

    try:
        with open(mapping_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f, delimiter='\t')

            # Check if file has all 4 required columns
            required_columns = {'vocabulary_term', 'vocabulary_id', 'mesh_term', 'mesh_id'}
            if not reader.fieldnames or not required_columns.issubset(set(reader.fieldnames)):
                # File doesn't have the required structure, skip it
                return 0, errors, True

            for row_num, row in enumerate(reader, start=2):  # Start at 2 (accounting for header)
                total_rows += 1

                vocab_id = row.get('vocabulary_id', '').strip()
                vocab_term = row.get('vocabulary_term', '').strip()

                if not vocab_id:
                    errors.append(f"Row {row_num}: Empty vocabulary_id")
                    continue

                if not vocab_term:
                    errors.append(f"Row {row_num}: Empty vocabulary_term")
                    continue

                # Check 1: Is the ONVOC ID defined in vocabulary?
                if vocab_id not in vocab_map:
                    errors.append(f"Row {row_num}: ONVOC ID '{vocab_id}' not found in vocabulary")
                    continue

                # Check 2: Does the vocabulary_term match the term for this ID?
                expected_term = vocab_map[vocab_id]
                if vocab_term != expected_term:
                    errors.append(
                        f"Row {row_num}: Term mismatch for {vocab_id}\n"
                        f"           Mapping has: '{vocab_term}'\n"
                        f"           Vocabulary has: '{expected_term}'"
                    )

    except Exception as e:
        errors.append(f"Error reading file: {e}")

    return total_rows, errors, False


def main():
    base_dir = Path(__file__).parent.parent.parent
    vocab_dir = base_dir / 'vocabulary'
    mappings_dir = base_dir / 'mappings'

    print("="*70)
    print("Mapping Validation")
    print("="*70)
    print(f"Vocabulary directory: {vocab_dir}")
    print(f"Mappings directory: {mappings_dir}")
    print()

    # Load vocabulary
    print("Loading vocabulary...")
    vocab_map = load_vocabulary(vocab_dir)
    print(f"Loaded {len(vocab_map)} unique ONVOC terms from vocabulary")
    print()

    # Find all TSV files in mappings directory
    mapping_files = sorted(mappings_dir.glob('*.tsv'))

    if not mapping_files:
        print("No TSV files found in mappings directory")
        return

    print(f"Found {len(mapping_files)} mapping files to validate")
    print()

    # Validate each mapping file
    total_errors = 0
    total_rows = 0
    files_with_errors = 0
    files_skipped = 0

    for mapping_file in mapping_files:
        print(f"Validating: {mapping_file.name}")

        rows, errors, should_skip = validate_mapping_file(mapping_file, vocab_map)

        if should_skip:
            files_skipped += 1
            print(f"  ⊘ Skipped (missing required columns)")
            print()
            continue

        total_rows += rows

        if errors:
            files_with_errors += 1
            total_errors += len(errors)
            print(f"  Found {len(errors)} error(s) in {rows} rows:")
            for error in errors:  
                print(f"    • {error}")
            #if len(errors) > 10:
            #    print(f"    ... and {len(errors) - 10} more errors")
        else:
            print(f"  ✓ Valid ({rows} rows)")

        print()

    print("="*70)
    print("Validation Summary")
    print("="*70)
    print(f"Total files found: {len(mapping_files)}")
    print(f"Files skipped: {files_skipped}")
    print(f"Files validated: {len(mapping_files) - files_skipped}")
    print(f"Total rows validated: {total_rows}")
    print(f"Files with errors: {files_with_errors}")
    print(f"Total errors found: {total_errors}")

    if total_errors == 0:
        print("\n✓ All validated mappings are valid!")
    else:
        print(f"\n✗ Found issues in {files_with_errors} file(s)")

    print("="*70)


if __name__ == '__main__':
    main()
