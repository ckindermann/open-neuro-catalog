#!/usr/bin/env python3
"""
Extract and annotate terms from files against a controlled vocabulary.

Given:
  --folders: one or more directories containing files whose content is lists of terms (one per line).
  --vocabulary: a directory containing TSV files defining the controlled vocabulary,
                with columns "term" and "vocabulary_id".

For every file under each folder:
  - Read each non-empty line as a term.
  - If the term exactly matches a vocabulary term, look up its vocabulary_id.
  - Otherwise, leave the vocabulary_id blank.
  - Write out a new TSV alongside the input file, with the same base name but extension ".tsv",
    containing two columns: term, vocabulary_id.

Usage:
    python3 annotate_terms.py \
        --folders /path/to/folder1 /path/to/folder2 \
        --vocabulary /path/to/vocabulary_dir
"""

import os
import argparse
import csv
import sys

def load_vocabulary(vocab_root):
    """
    Traverse vocab_root recursively, load all .tsv files.
    Build and return a dict mapping term -> vocabulary_id.
    """
    mapping = {}
    for dirpath, _, filenames in os.walk(vocab_root):
        for fname in filenames:
            if not fname.lower().endswith(".tsv"):
                continue
            path = os.path.join(dirpath, fname)
            with open(path, encoding="utf-8") as fp:
                reader = csv.reader(fp, delimiter="\t")
                header = next(reader, None)
                if not header:
                    continue
                # find indices
                try:
                    term_idx = header.index("term")
                    id_idx = header.index("vocabulary_id")
                except ValueError:
                    term_idx, id_idx = 0, 1
                for row in reader:
                    if len(row) <= max(term_idx, id_idx):
                        continue
                    term = row[term_idx].strip()
                    vid  = row[id_idx].strip()
                    if term:
                        # if duplicate term with different ID, warn
                        if term in mapping and mapping[term] != vid:
                            print(f"WARNING: term '{term}' has conflicting IDs "
                                  f"'{mapping[term]}' vs '{vid}' in {path}", file=sys.stderr)
                        mapping[term] = vid
    return mapping

def annotate_file(file_path, mapping):
    """
    Read file_path line by line as terms.
    Write out file_path with .tsv extension:
      term<TAB>vocabulary_id
    """
    base, _ = os.path.splitext(file_path)
    out_path = f"{base}.tsv"
    rows = []
    with open(file_path, encoding="utf-8") as fp:
        for line in fp:
            term = line.strip()
            if not term:
                continue
            vid = mapping.get(term, "")
            rows.append((term, vid))

    # write TSV
    with open(out_path, "w", newline="", encoding="utf-8") as fp:
        writer = csv.writer(fp, delimiter="\t")
        writer.writerow(["term", "vocabulary_id"])
        for term, vid in rows:
            writer.writerow([term, vid])
    print(f"Annotated {file_path} → {out_path}")

def main():
    parser = argparse.ArgumentParser(
        description="Annotate files of terms against a controlled vocabulary.")
    parser.add_argument(
        "--folders",
        nargs="+",
        required=True,
        help="Directories containing files of terms to annotate."
    )
    parser.add_argument(
        "--vocabulary",
        required=True,
        help="Root directory of the controlled vocabulary (.tsv files with term and vocabulary_id)."
    )
    args = parser.parse_args()

    # load vocabulary mapping
    vocab_root = os.path.abspath(args.vocabulary)
    if not os.path.isdir(vocab_root):
        print(f"ERROR: vocabulary path '{vocab_root}' is not a directory.", file=sys.stderr)
        sys.exit(1)
    mapping = load_vocabulary(vocab_root)
    if not mapping:
        print("WARNING: no vocabulary terms loaded; all IDs will be blank.", file=sys.stderr)

    # process each folder
    for folder in args.folders:
        folder = os.path.abspath(folder)
        if not os.path.isdir(folder):
            print(f"ERROR: folder path '{folder}' is not a directory, skipping.", file=sys.stderr)
            continue
        for dirpath, _, filenames in os.walk(folder):
            for fname in filenames:
                # skip already-annotated TSVs
                if fname.lower().endswith(".tsv") or not fname.endswith(".txt"):
                    continue
                file_path = os.path.join(dirpath, fname)
                annotate_file(file_path, mapping)

if __name__ == "__main__":
    main()
