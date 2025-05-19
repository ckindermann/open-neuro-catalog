#!/usr/bin/env python3
import os
import csv
import argparse

def process_main_categories(input_folder):
    """
    Read the top‐level Categories.tsv and return a list of (term, vocab_id).
    """
    path = os.path.join(input_folder, "Categories.tsv")
    with open(path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f, delimiter="\t")
        return [(row["term"], row["vocabulary_id"]) for row in reader]

def process_subcategories(input_folder, term, parent_vocab, writer):
    """
    If a subfolder named `term` exists and contains Categories.tsv,
    read its vocabulary_ids and write narrower/broader triples.
    """
    subfolder = os.path.join(input_folder, term)
    subcat_tsv = os.path.join(subfolder, "Categories.tsv")
    if os.path.isdir(subfolder) and os.path.isfile(subcat_tsv):
        with open(subcat_tsv, "r", encoding="utf-8") as sf:
            sub_reader = csv.DictReader(sf, delimiter="\t")
            for sub in sub_reader:
                child_vocab = sub["vocabulary_id"]
                # parent → narrower → child
                writer.writerow([parent_vocab, "skos:narrower", child_vocab, "_IRI"])
                # child → broader → parent (no datatype column per spec)
                writer.writerow([child_vocab, "skos:broader", parent_vocab, "_IRI"])

def main():
    parser = argparse.ArgumentParser(
        description="Generate a SKOS CSV from Categories.tsv and its subfolders."
    )
    parser.add_argument("input_folder",
                        help="Folder containing top‐level Categories.tsv and subfolders")
    parser.add_argument("output_folder",
                        help="Where to write output.csv")
    args = parser.parse_args()

    # Ensure output folder exists
    os.makedirs(args.output_folder, exist_ok=True)
    out_path = os.path.join(args.output_folder, "top_level.csv")

    # Read top‐level categories
    main_terms = process_main_categories(args.input_folder)

    # Open CSV writer
    with open(out_path, "w", newline="", encoding="utf-8") as out_csv:
        writer = csv.writer(out_csv)

        for term, vocab in main_terms:
            # 1) rdf:type owl:NamedIndividual
            writer.writerow([vocab, "rdf:type", "owl:NamedIndividual", "_IRI"])
            # 2) rdf:type skos:Concept
            writer.writerow([vocab, "rdf:type", "skos:Concept", "_IRI"])
            # 3) skos:inScheme ONVOC:test
            writer.writerow([vocab, "skos:inScheme", "ONVOC:test", "_IRI"])
            # 4) skos:prefLabel "term"^^xsd:string (underscores → spaces)
            label = term.replace("_", " ")
            writer.writerow([vocab, "skos:prefLabel", label, "xsd:string"])
            # 5) skos:topConceptOf ONVOC:test
            writer.writerow([vocab, "skos:topConceptOf", "ONVOC:test", "_IRI"])
            # 6) ONVOC:test skos:hasTopConcept vocab
            writer.writerow(["ONVOC:test", "skos:hasTopConcept", vocab, "_IRI"])

            # Now handle subcategories
            process_subcategories(args.input_folder, term, vocab, writer)

    print(f"Done! Wrote all triples to {out_path}")

if __name__ == "__main__":
    main()
