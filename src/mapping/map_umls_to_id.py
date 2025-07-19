import sys
import pandas as pd
from lxml import etree

# This script extracts a mapping from UMLS CUIs to MeSH IDs from an OWL/XML file.
def extract_umls_to_mesh_mappings(owl_file_path):
    # Parse the OWL file
    tree = etree.parse(owl_file_path)
    root = tree.getroot()

    # Define namespaces
    ns = {
        'rdf': "http://www.w3.org/1999/02/22-rdf-syntax-ns#",
        'umls': "http://bioportal.bioontology.org/ontologies/umls/",
    }

    mappings = []

    # Iterate over all Class elements
    for cls in root.findall(".//{*}Class"):
        mesh_id = cls.attrib.get('{http://www.w3.org/1999/02/22-rdf-syntax-ns#}about')
        if not mesh_id:
            continue
        for cui_elem in cls.findall('umls:cui', namespaces=ns):
            cui = cui_elem.text
            mappings.append({'mesh_id': mesh_id, 'umls_cui': cui})

    return pd.DataFrame(mappings)

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python extract_umls_mesh.py path_to_ontology.owl")
        sys.exit(1)

    input_path = sys.argv[1]
    df = extract_umls_to_mesh_mappings(input_path)
    output_path = "umls_to_mesh.tsv"
    df.to_csv(output_path, sep='\t', index=False)
    print(f"Saved UMLS-to-MeSH mapping to {output_path}")
