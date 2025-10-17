# OpenNeuro Vocabulary (ONVOC)

ONVOC is a controlled vocabulary for annotating neuroimaging datasets hosted on [OpenNeuro](https://openneuro.org/).

## Purpose

The primary goal of ONVOC is to improve **findability** of OpenNeuro datasets.
It does so by supplying meaningful, machine-actionable tags that can capture context such as a study's focus, design, and population characteristics.

## How ONVOC Is Used

ONVOC provides the **terms** for annotation; it does **not** prescribe a metadata model or schema.
Any metadata model can define how and where ONVOC terms are applied.

### Example:

Under a metadata model that distinguishes *Study Focus*, *Inclusion Criteria*, and *Exclusion Criteria*, the term *Schizophrenia* can denote very different things. For example, *Study Focus: Schizophrenia* identifies the condition under investigation, whereas *Exclusion Criteria: Schizophrenia* flags datasets that exclude participants with that diagnosis.
To enable precise search and ranking, annotations must pair each *term* with its *context*: the term comes from ONVOC, and the context comes from the metadata model.

## Design Goals

- **Broad coverage:** Datasets are part of larger research packages (papers, presentations, code, blogs, etc). ONVOC aims to cover enough concepts that useful dataset annotations can be derived from these sources.
- **Findability first:** While broadly useful across neuroscience and psychology resources, ONVOC's core *purpose* is to make OpenNeuro datasets easier to find.
- **Simple and pragmatic:** The vocabulary is a collection of *terms* for annotating resources. It is *not* an authorative source of truth for the meaning of those terms.

## Technical Overview

### Vocabulary Structure

The controlled vocabulary is organized using a two-folder architecture:

- **`terms/`** - Contains the vocabulary terms organized in plain text files
- **`vocabulary/`** - Contains the published vocabulary with unique identifiers in TSV format

#### Terms Folder Structure
```
terms/
├── Brain_Regions/
│   ├── Cortical_Regions.txt
│   └── Subcortical_Regions.txt
├── Disorders/
│   ├── Neurological_Disorders.txt
│   └── Psychiatric_Disorders.txt
└── ...
```

In the **`terms`** directory, each folder represents a **category** (e.g., `Disorders`). Inside a category, each `.txt` file defines a **subcategory** (e.g., `Neurological_Disorders.txt`).
Each `.txt` file contains a plain, newline-delimited list of terms.

#### Vocabulary Folder Structure
```
vocabulary/
├── Brain_Regions/
│   ├── Cortical_Regions.tsv
│   └── Subcortical_Regions.tsv
├── Disorders/
│   ├── Neurological_Disorders.tsv
│   └── Psychiatric_Disorders.tsv
└── ...
```

Each `.tsv` file contains three columns:
- `term` - The vocabulary term
- `vocabulary_id` - Unique identifier (format: `ONVOC:XXXXXXX`)
- `comment` - Optional description or notes

#### Synchronization Process

The vocabulary folder is automatically generated and synchronized from the terms folder. When terms are added, moved, or removed from the terms folder, the corresponding TSV files in the vocabulary folder are updated while preserving existing vocabulary IDs for unchanged terms.

## Modifying the Vocabulary

The vocabulary can be modified using the `src/edit/edit_terms.py` script, which provides three intention-revealing operations:

### Available Operations

#### 1. Add a New Term
```bash
python3 src/edit/edit_terms.py --terms ./terms --vocabulary ./vocabulary \
    add "New Term Name" "Category/Subcategory"
```

Adds a new term to the specified category and subcategory. The term will automatically receive a new unique vocabulary ID.

#### 2. Remove a Term
```bash
python3 src/edit/edit_terms.py --terms ./terms --vocabulary ./vocabulary \
    remove "Category/Subcategory/Term Name"
```

Removes a term from the vocabulary. The term and its vocabulary ID will be permanently deleted.

#### 3. Move/Rename a Term
```bash
python3 src/edit/edit_terms.py --terms ./terms --vocabulary ./vocabulary \
    move "Old Category/Subcategory/Old Name" "New Category/Subcategory/New Name"
```

Moves a term to a different location and/or renames it while **preserving its original vocabulary ID**. This ensures that existing references to the term remain valid.

### Batch Operations

For bulk changes, you can use batch files:

```bash
python3 src/edit/edit_terms.py --terms ./terms --vocabulary ./vocabulary \
    batch changes.txt
```

Batch file format (one operation per line):
```
add "New Term 1" "Category/Subcategory"
remove "Category/Subcategory/Old Term"
move "Category/Subcategory/Term" "Category/Subcategory/Renamed Term"
# Lines starting with # are comments ```
