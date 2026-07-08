---
output:
  word_document:
    fig_caption: true
    number_sections: false
    toc: false
    toc_depth: 3
    df_print: paged
  pdf_document:
    latex_engine: xelatex
    highlight: arrow
    number_sections: false
  html_document:
    df_print: kable
    toc: true
    toc_float: true
    number_sections: true
    theme: readable
    highlight: textmate
    dev: CairoPNG
---

# Chloroplast Genome Mining Module

## Overview

This module implements an automated, end-to-end bioinformatics pipeline for the retrieval, quality assessment, re-annotation, gene extraction, and deduplication of plant chloroplast genome sequences from the NCBI GenBank database. The pipeline is designed for large-scale comparative chloroplast genomics studies and consists of eight sequential stages.

------------------------------------------------------------------------

## Pipeline Architecture

``` mermaid
flowchart TD
    A["1. Accession List"] --> B["2. Batch Download\n(download_gb_file.py)"]
    B -->|"*.gb"| C["3. Pre-filtering\n(pre_filter_gb_file.py)"]
    C -->|"Retained *.gb"| D["4. Quality Control\n(quality_ctrl.py)"]
    D -->|"gb_info.csv"| E{Problematic genomes?}
    E -->|"Yes"| F["5. PGA-NG Re-annotation\n(call_pga.py)"]
    E -->|"No"| G["6. CDS Extraction\n(get_cds.py)"]
    F -->|"*.gb.old + pga_output/*.gb"| G
    G -->|"*.fasta per gene"| H["7. Length Filtering\n(filter_seq.py)"]
    H -->|"length.csv + filtered *.fasta"| I["8. Species-level Selection\n(select_seq_by_acc.py)"]
    I --> J["Final representative CDS set"]

    style A fill:#e1f5fe
    style B fill:#fff3e0
    style C fill:#fff3e0
    style D fill:#fff3e0
    style F fill:#ffebee
    style G fill:#fff3e0
    style H fill:#fff3e0
    style I fill:#e8f5e9
    style J fill:#e8f5e9
```

------------------------------------------------------------------------

## Workflow Stages

### Stage 1: Batch Download (`download_gb_file.py`)

**Function**: Download GenBank-format chloroplast genome files from NCBI based on a provided accession list.

**Implementation details**:

| Feature | Description |
|----------------|-------------------------------------------------------|
| Threading | `ThreadPoolExecutor` with configurable thread count (default: 10) |
| Rate limiting | Minimum 0.34 s interval between consecutive requests |
| Retry mechanism | Up to 3 retries per accession with exponential backoff |
| Error handling | Timeout (600 s per request), HTTP 429 rate-limit detection |
| Resume support | Detects existing `.gb` files and previously failed accessions |
| Integrity check | Validates `ORIGIN` section presence; deletes empty/invalid files |

**Inputs**:

- Accession list file (one accession per line)
- NCBI contact email

**Outputs**:

- `{accession}.gb` files in the output directory
- `error_downloaded_index.csv` for failed downloads

------------------------------------------------------------------------

### Stage 2: Pre-filtering (`pre_filter_gb_file.py`)

**Function**: Remove low-quality or non-target genomes prior to downstream analysis.

**Rejection criteria**:

| Criterion | Action |
|-------------------------------|----------------------------------------|
| `KEYWORDS` contains `UNVERIFIED` | Reject → rename to `.unusable` |
| `ORGANISM` contains `sp.` | Reject (ambiguous species-level identification) |
| `ORGANISM` contains `x` | Reject (hybrid genomes) |

**Retention strategy**:

For each taxon (species or variety level, configurable via `species_level`), retain at most `keep_latest` (default: 3) genomes, prioritized by:

1.  Publication status (published \> unpublished)
2.  Number of annotated CDS features
3.  Genome length
4.  Submission date (newest first)

**Inputs**: Directory of `.gb` files

**Outputs**:

- Retained `.gb` files copied to output directory
- `pre_filter.csv`: per-genome metadata table

------------------------------------------------------------------------

### Stage 3: Quality Control (`quality_ctrl.py`)

**Function**: Generate a comprehensive quality report for each retained GenBank file.

**Metrics extracted per genome**:

| Metric | Description |
|------------------|------------------------------------------------------|
| `sequence_length` | Total nucleotide length |
| `gene_count` | Total annotated genes |
| `CDS` | Number of standard plastid CDS (from the 80-gene reference set) |
| `tRNA` / `rRNA` | Count of tRNA and rRNA features |
| `unclear_bases` | Number of bases not in {A, T, C, G} |
| `unclear_ratio` | Proportion of ambiguous bases |

**Flagging criteria**:

- **Low CDS count**: `CDS < cds_threshold` (default: 80)
- **High ambiguity**: `unclear_ratio > ambig_threshold` (default: 0.2)

Problematic genomes are exported as `{accession}_reannotated.fasta` for subsequent PGA-NG re-annotation (Stage 5).

**Outputs**:

- `gb_info.csv`: Complete quality-control table
- `{accession}_reannotated.fasta` files for flagged genomes

------------------------------------------------------------------------

### Stage 4: PGA-NG Re-annotation (`call_pga.py`)

**Function**: Re-annotate problematic GenBank files using the **PGA-NG** (Plastid Genome Annotator) tool, using reference genomes from appropriate clades (Angiosperms or Gymnosperms).

**Workflow**:

``` mermaid
flowchart TD
    A["Identify pending genomes"] --> B["Prepare temp folders"]
    B --> C["Execute PGA-NG"]
    C --> D["Monitor annotation progress"]
    D --> E{"All complete?"}
    E -->|"No"| D
    E -->|"Yes"| F["Merge annotations\ninto original .gb files"]
    F --> G["Clean up temp folders"]
```

**Key features**:

- Incremental annotation: skips genomes with existing re-annotated files
- Multi-threaded progress monitoring and annotation merging
- Graceful recovery from interrupted runs

**Reference sets**: Two clade-specific reference genome collections are embedded in the PGA-NG installation:

- **Angiosperms** — for flowering plants
- **Gymnosperms** — for conifers and related lineages

------------------------------------------------------------------------

### Stage 5: CDS Extraction (`get_cds.py`)

**Function**: Extract individual coding sequences from all GenBank files (original + re-annotated), producing one FASTA file per gene.

**Gene nomenclature**: Utilizes the standard 80 plastid gene set defined in `PPA_80_CDS`, which includes:

- Photosystem I / II genes (e.g., `psaA`, `psbD`, `petB`)
- ATP synthase genes (e.g., `atpA`, `atpB`)
- RNA polymerase genes (e.g., `rpoA`, `rpoB`)
- Ribosomal protein genes (e.g., `rpl16`, `rps12`)
- Ribosomal RNA genes (`rrn16`, `rrn23`, `rrn4.5`, `rrn5`)
- Other essential plastid genes (`rbcL`, `matK`, `ycf4`, etc.)

**Feature extraction**:

- Handles split features (disjoint locations)
- Correctly processes reverse-complement strands
- Maps alternative gene names to standard nomenclature via `PPA_80_CDS` dictionary

**Outputs**:

- `{gene}.fasta` — one file per gene, containing all accession-level sequences
- `cds_num.csv` — per-accession CDS counts
- `cds_loc.txt` — per-accession CDS location strings (tab-separated)
- `length.csv` — per-accession per-gene sequence lengths

------------------------------------------------------------------------

### Stage 6: Length Filtering (`filter_seq.py`)

**Function**: Remove abnormally long or short CDS sequences based on reference genome length distributions.

**Filtering formula**:

$$L_{\min} = \alpha \times L_{\text{ref}} \qquad L_{\max} = \beta \times L_{\text{ref}}$$

where $L_{\text{ref}}$ is the reference gene length (from `ANG_REF_LEN` for angiosperms or `GYM_REF_LEN` for gymnosperms), and default bounds are $\alpha = 0.5$, $\beta = 2.0$.

Sequences with length outside $[L_{\min}, L_{\max}]$ are excluded. For genes not present in the reference set, the longest sequence per accession is retained without filtering.

**Outputs**:

- Filtered `{gene}.fasta` files
- `length.csv`: updated per-accession per-gene lengths

------------------------------------------------------------------------

### Stage 7: Species-level Selection (`select_seq_by_acc.py`)

**Function**: Select a single representative chloroplast genome for each species based on the maximum cumulative CDS length, and optionally standardize taxonomic names.

**Selection criterion**: For each species with multiple chloroplast genome submissions, retain the genome with the greatest total CDS length (`sum of all CDS column lengths`).

**Name standardization** (optional, via `-f` flag):

When a standardization file (`file_organism_name`) is provided, an **inner join** on the `organism` column maps original names to standardized names (`new_name` column). Species not present in the standardization table are excluded.

``` mermaid
flowchart TD
    A["length.csv"] --> B["make_tab()"]
    B -->|"organism.csv"| C["Optional: manual name standardization"]
    C -->|"file_organism_name"| D["Inner join → new_name"]
    D --> E["select_seq_by_acc()"]
    E -->|"Per species"| F["Representative CDS FASTA"]
```

**Outputs**:

- `organism.csv`: deduplicated organism list with IDs
- Representative CDS FASTA files (one per selected accession)

------------------------------------------------------------------------

## Reference Data

| Resource | Description |
|---------------|---------------------------------------------------------|
| `PPA_80_CDS` | Standard 80 plastid gene name mapping dictionary (alternative names → standard names) |
| `ANG_REF_LEN` | Reference CDS lengths for**angiosperm** plastid genes |
| `GYM_REF_LEN` | Reference CDS lengths for**gymnosperm** plastid genes |

------------------------------------------------------------------------

## Complete Data Flow

``` mermaid
flowchart TD
    subgraph sg_Input["Input"]
        A1["Accession list"]
        A2["NCBI GenBank"]
    end

    subgraph sg_Acquisition["Acquisition"]
        B1["download_gb_file.py<br/>→ *.gb files"]
    end

    subgraph sg_Filtering["Filtering"]
        C1["pre_filter_gb_file.py<br/>→ Retained *.gb + pre_filter.csv"]
        C2["quality_ctrl.py<br/>→ gb_info.csv + _reannotated.fasta"]
    end

    subgraph sg_Reannotation["Re-annotation"]
        D1["call_pga.py<br/>→ Fixed *.gb files"]
    end

    subgraph sg_GeneLevel["Gene-level Processing"]
        E1["get_cds.py<br/>→ per-gene *.fasta + cds tables"]
        E2["filter_seq.py<br/>→ filtered *.fasta + length.csv"]
    end

    subgraph sg_SpeciesLevel["Species-level Processing"]
        F1["select_seq_by_acc.py<br/>→ Representative CDS set"]
    end

    subgraph sg_Output["Output"]
        G1["Final representative chloroplast CDS collection"]
        G2["organism.csv"]
        G3["length.csv"]
    end

    A1 --> B1
    A2 --> B1
    B1 --> C1
    C1 --> C2
    C2 -->|"flagged"| D1
    C2 -->|"OK"| E1
    D1 --> E1
    E1 --> E2
    E2 --> F1
    F1 --> G1
    F1 --> G2
    F1 --> G3

    classDef input fill:#e3f2fd,stroke:#1565c0
    classDef acquisition fill:#fff3e0,stroke:#ef6c00
    classDef filtering fill:#fff8e1,stroke:#f9a825
    classDef reannotation fill:#ffebee,stroke:#c62828
    classDef geneLevel fill:#f3e5f5,stroke:#6a1b9a
    classDef speciesLevel fill:#e8f5e9,stroke:#2e7d32
    classDef output fill:#e0f2f1,stroke:#00695c

    class sg_Input input
    class sg_Acquisition acquisition
    class sg_Filtering filtering
    class sg_Reannotation reannotation
    class sg_GeneLevel geneLevel
    class sg_SpeciesLevel speciesLevel
    class sg_Output output
```

------------------------------------------------------------------------

## Dependencies

- **Python ≥ 3.12**
- `biopython` — sequence file I/O
- `pandas` — tabular data processing
- `func_timeout` — request timeout enforcement
- `PGA-NG` — chloroplast genome re-annotation (external tool)

------------------------------------------------------------------------

## Author

**Ruijing Cheng, Wang Yuxuan, Li Dan**
