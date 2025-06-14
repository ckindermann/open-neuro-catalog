#!/usr/bin/env python3
"""
Serialize a controlled vocabulary folder (with TSV files & IDs) as SKOS, including
both skos:topConceptOf on each top concept and the inverse skos:hasTopConcept on the
ConceptScheme.

Usage:
    python3 export_to_skos.py --vocab /path/to/vocab_folder --output skos.ttl

Requirements:
    pip install rdflib
"""

import os
import csv
import argparse
from rdflib import Graph, Namespace, URIRef, Literal
from rdflib.namespace import SKOS, RDF, OWL

def load_tsv_map(tsv_path):
    """
    Load a TSV with header [term, vocabulary_id, ...] and return list of (term, id).
    """
    items = []
    with open(tsv_path, encoding="utf-8") as fp:
        reader = csv.reader(fp, delimiter="\t")
        header = next(reader, None)
        if not header:
            return items
        try:
            term_idx = header.index("term")
            id_idx   = header.index("vocabulary_id")
        except ValueError:
            term_idx, id_idx = 0, 1
        for row in reader:
            if len(row) > max(term_idx, id_idx):
                term = row[term_idx].strip()
                vid  = row[id_idx].strip()
                if term and vid:
                    items.append((term, vid))
    return items

def main(vocab_root, output_path):
    # Namespaces
    CAT = Namespace("http://www.onvoc/test/alpha#")
    SCHEME_URI = CAT.scheme

    g = Graph()
    g.bind("skos", SKOS)
    g.bind("owl", OWL)
    g.bind("rdf", RDF)
    g.bind("alpha", CAT)

    # Declare the scheme itself
    g.add((SCHEME_URI, RDF.type, SKOS.ConceptScheme))
    g.add((SCHEME_URI, SKOS.prefLabel, Literal("Alpha Controlled Vocabulary")))

    # 1) Load categories
    cats_tsv = os.path.join(vocab_root, "Categories.tsv")
    categories = load_tsv_map(cats_tsv)

    # Map vocab_id -> URIRef, and store term for convenience
    uri_map = {}
    for term, vid in categories:
        uri = URIRef(f"{CAT}{vid.replace(':','_')}")
        uri_map[vid] = uri
        # Types
        g.add((uri, RDF.type, SKOS.Concept))
        g.add((uri, RDF.type, OWL.NamedIndividual))
        # Labels
        g.add((uri, SKOS.prefLabel, Literal(term)))
        # In scheme
        g.add((uri, SKOS.inScheme, SCHEME_URI))
        # Top concepts and inverse
        g.add((uri, SKOS.topConceptOf, SCHEME_URI))
        g.add((SCHEME_URI, SKOS.hasTopConcept, uri))

    # 2) Load subcategories and link to categories
    for term, vid in categories:
        cat_uri = uri_map[vid]
        folder = term.replace(" ", "_")
        sub_tsv = os.path.join(vocab_root, folder, "Subcategories.tsv")
        if not os.path.isfile(sub_tsv):
            continue
        subcats = load_tsv_map(sub_tsv)
        for sub_term, sub_vid in subcats:
            sub_uri = URIRef(f"{CAT}{sub_vid.replace(':','_')}")
            uri_map[sub_vid] = sub_uri
            # Types & labels & inScheme
            g.add((sub_uri, RDF.type, SKOS.Concept))
            g.add((sub_uri, RDF.type, OWL.NamedIndividual))
            g.add((sub_uri, SKOS.prefLabel, Literal(sub_term)))
            g.add((sub_uri, SKOS.inScheme, SCHEME_URI))
            # Hierarchy
            g.add((cat_uri, SKOS.narrower, sub_uri))
            g.add((sub_uri, SKOS.broader, cat_uri))

        # 3) Load leaf terms for each subcategory
        for sub_term, sub_vid in subcats:
            sub_uri = uri_map[sub_vid]
            sub_folder = sub_term.replace(" ", "_")
            leaf_tsv = os.path.join(vocab_root, folder, f"{sub_folder}.tsv")
            if not os.path.isfile(leaf_tsv):
                continue
            leaves = load_tsv_map(leaf_tsv)
            for leaf_term, leaf_vid in leaves:
                leaf_uri = URIRef(f"{CAT}{leaf_vid.replace(':','_')}")
                uri_map[leaf_vid] = leaf_uri
                g.add((leaf_uri, RDF.type, SKOS.Concept))
                g.add((leaf_uri, RDF.type, OWL.NamedIndividual))
                g.add((leaf_uri, SKOS.prefLabel, Literal(leaf_term)))
                g.add((leaf_uri, SKOS.inScheme, SCHEME_URI))
                # Hierarchy
                g.add((sub_uri, SKOS.narrower, leaf_uri))
                g.add((leaf_uri, SKOS.broader, sub_uri))

    # Serialize to Turtle
    g.serialize(destination=output_path, format="turtle")
    print(f"SKOS vocabulary written to {output_path}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Export a controlled vocabulary folder as SKOS RDF with topConceptOf and hasTopConcept."
    )
    parser.add_argument(
        "--vocab",
        required=True,
        help="Path to the controlled vocabulary root (with Categories.tsv, subfolders, etc.)"
    )
    parser.add_argument(
        "--output",
        default="vocabulary.ttl",
        help="Output Turtle file (default: vocabulary.ttl)"
    )
    args = parser.parse_args()
    main(args.vocab, args.output)
