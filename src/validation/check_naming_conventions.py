#!/usr/bin/env python3
"""
Validate folder and file naming conventions under a given root directory.

Conventions:
  - Names must not contain whitespace.
  - Names use “snake_case” with underscores separating words.
  - Each segment (split by underscores) must be one of:
      • A “connective” word in all lowercase (and, or, of, the, in, on, for)
      • An acronym in all uppercase (e.g. MRI, BMX)
      • A “principal” word starting with an uppercase letter followed by lowercase letters or digits
  - File extensions (e.g. .txt, .tsv) are allowed but everything before the first dot must follow the above rules.

Usage:
    python3 check_naming_conventions.py --root /path/to/Controlled_Vocabulary
"""

import os
import re
import argparse
import sys

# Connective words (allowed in purely lowercase form)
CONNECTIVES = {"and", "or", "of", "the", "in", "on", "for"}

# Regex patterns for different segment types
PRINCIPAL_WORD_RE = re.compile(r"^[A-Z][a-z0-9]+$")   # “Brain” or “Structures1”
ACRONYM_RE = re.compile(r"^[A-Z]{2,}$")               # “MRI”, “BMX”, etc.
# File extension pattern (one dot followed by lowercase letters, e.g. “.txt”, “.tsv”)
EXTENSION_RE = re.compile(r"\.[a-z]+$")

def check_segment(segment: str) -> bool:
    """
    Return True if `segment` is valid:
      - a lowercase connective word (and, or, of, the, in, on, for), or
      - an acronym (all uppercase, length >= 2), or
      - a principal word (starts with uppercase, then lowercase letters or digits).
    """
    if segment in CONNECTIVES:
        return True
    if ACRONYM_RE.match(segment):
        return True
    if PRINCIPAL_WORD_RE.match(segment):
        return True
    return False

def validate_name(name: str, is_file: bool=False) -> list[str]:
    """
    Validate a single folder or file name. Returns a list of error messages (empty if valid).
    If `is_file` is True, splits off the extension before validating the base name.
    """
    errors: list[str] = []

    if re.search(r"\s", name):
        errors.append("contains whitespace")

    base = name
    ext = ""
    if is_file:
        # Split base and extension (only the LAST dot)
        if "." not in name:
            errors.append("missing file extension")
            base = name
        else:
            base, ext = name.rsplit(".", 1)
            ext = "." + ext
            if not EXTENSION_RE.match(ext):
                errors.append(f"invalid extension '{ext}' (must be a dot followed by lowercase letters)")

    if base == "":
        errors.append("empty base name")
    else:
        segments = base.split("_")
        if "" in segments:
            errors.append("empty segment due to consecutive or leading/trailing underscores")
        else:
            for seg in segments:
                if not check_segment(seg):
                    errors.append(f"invalid segment '{seg}'")
    return errors

def main(root: str):
    """
    Walk through `root` recursively and validate every folder and file name.
    Print any violations with their path and explanation.
    """
    violations_found = False

    # os.walk yields (dirpath, dirnames, filenames). We’ll check dirnames and filenames.
    for dirpath, dirnames, filenames in os.walk(root):
        # Check each subfolder name in dirnames
        for d in list(dirnames):  # list() to avoid modifying during iteration
            rel_path = os.path.join(dirpath, d)
            errs = validate_name(d, is_file=False)
            if errs:
                violations_found = True
                print(f"[Folder] {rel_path}:")
                for e in errs:
                    print(f"  ‣ {e}")
        # Check each file name
        for f in filenames:
            rel_path = os.path.join(dirpath, f)
            errs = validate_name(f, is_file=True)
            if errs:
                violations_found = True
                print(f"[File]   {rel_path}:")
                for e in errs:
                    print(f"  ‣ {e}")

    if not violations_found:
        print("All folder and file names conform to the naming conventions.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Check that folder and file names follow the specified naming conventions."
    )
    parser.add_argument(
        "--root",
        required=True,
        help="Root directory to validate."
    )
    args = parser.parse_args()

    if not os.path.isdir(args.root):
        print(f"ERROR: “{args.root}” is not a directory or does not exist.", file=sys.stderr)
        sys.exit(1)

    main(args.root)
