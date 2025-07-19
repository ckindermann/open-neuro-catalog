import sys
import pandas as pd

def replace_umls_with_mesh(mapping_file, cui_to_mesh_file, output_file):
    # Read input files
    df_mapping = pd.read_csv(mapping_file, sep='\t')
    df_cui_to_mesh = pd.read_csv(cui_to_mesh_file, sep='\t')

    # Merge and keep only matched rows
    merged_df = pd.merge(df_mapping, df_cui_to_mesh, on='umls_cui', how='inner')

    # Final output: replace 'umls_cui' with 'mesh_id'
    output_df = merged_df[['vocabulary_term', 'vocabulary_id', 'mesh_term', 'mesh_id']]

    # Write output to TSV
    output_df.to_csv(output_file, sep='\t', index=False)
    print(f"Output written to {output_file} ({len(output_df)} rows retained)")

if __name__ == "__main__":
    if len(sys.argv) != 4:
        print("Usage: python replace_cuis_with_mesh.py mapping.tsv cui_to_mesh.tsv output.tsv")
        sys.exit(1)

    mapping_file = sys.argv[1]
    cui_to_mesh_file = sys.argv[2]
    output_file = sys.argv[3]

    replace_umls_with_mesh(mapping_file, cui_to_mesh_file, output_file)
