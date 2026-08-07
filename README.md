# PyNCBIminer-NG

A user-friendly graphical interface software for efficient and precise retrieval of GenBank data.

## Overview

PyNCBIminer-NG is a next-generation bioinformatics desktop application that streamlines the retrieval, filtering, alignment, and concatenation of nucleotide sequences from NCBI GenBank. It provides three major modules:

- **DNA Sequence Module** — Iterative BLAST-based sequence mining, extension refinement, species-level deduplication, TNRS taxonomic name resolution, and multi-marker sequence aggregation
- **Chloroplast Module** — End-to-end chloroplast genome mining: batch download, quality control, PGA-NG re-annotation, CDS extraction, length filtering, and species-level representative selection
- **Supermatrix Construction Module** — Sequence replacement (merging chloroplast CDS with fragments), multiple sequence alignment (MAFFT), alignment trimming (trimAl), and multi-gene supermatrix concatenation

No programming experience is required.

***

## Key Features

### DNA Sequence Module

| Feature                      | Description                                                                                                                                                                                                  |
| ---------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| Iterative BLAST              | Automatically performs iterative BLAST searches until saturation                                                                                                                                             |
| Smart Query Selection        | Selects optimal reference sequences at each iteration                                                                                                                                                        |
| Resume Capability            | Interrupted workflows can be resumed from the last checkpoint                                                                                                                                                |
| Extended Segments Refinement | Trims non-homologous regions introduced by sequence extension                                                                                                                                                |
| Species-level Selection      | Retains one representative sequence per species (Abnormality Index + multi-criteria ranking)                                                                                                                 |
| TNRS Name Resolution         | Online taxonomic name standardization via TNRS API (wcvp/wfo sources, configurable accuracy, `Accepted`/`Synonym` status only, genus-rank exclusion on by default) |
| Sequence Aggregate           | Automatically runs after species-level selection: writes per-marker clean FASTA (`aggregated/<marker>.fasta`) plus an accession↔species CSV (`aggregated/<marker>.csv`) for downstream supermatrix construction |

### Chloroplast Module

| Feature                        | Description                                                                                                                                                                                           |
| ------------------------------ | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Entrez Search & Batch Download | Taxon-based NCBI search with date filtering and threaded GenBank download                                                                                                                             |
| Pre-filtering                  | Remove UNVERIFIED/ambiguous/hybrid genomes; retain top-N per taxon                                                                                                                                    |
| Quality Control                | Flag genomes with low CDS count or high ambiguity ratio                                                                                                                                               |
| PGA-NG Re-annotation           | Re-annotate problematic genomes with clade-specific references                                                                                                                                        |
| Get & Filter CDS               | Extract 80 standard plastid genes and filter by reference length bounds                                                                                                                               |
| Species-level CDS Selection    | Select one representative genome per species (longest total CDS); optional TNRS name resolution (score ≥ accuracy, `Accepted`/`Synonym` status only, genus-rank exclusion on by default) with batch caching; writes a species table (`selected_sequences.csv`: species, representative accession, missing genes) |

### Supermatrix Construction Module

| Feature                   | Description                                                                                  |
| ------------------------- | -------------------------------------------------------------------------------------------- |
| Replacement               | Merge chloroplast genome-derived CDS with fragment sequences for the same gene marker        |
| MAFFT Alignment           | Multiple sequence alignment with configurable algorithms and thread count                    |
| trimAl Trimming           | Alignment trimming (automated1, gappyout, strict, strictplus) with chloroplast boundary mode |
| Supermatrix Concatenation | Combine multiple gene markers into a single partitioned supermatrix                          |

### Interface

- Modern Fluent Design (PySide6 + PySide6-Fluent-Widgets)
- Light / Dark / Auto theme
- Real-time console logging with level-tagged messages
- Built-in installer for MAFFT, trimAl, and PGA-NG

***

## Installation

### Prerequisites

- Windows 10/11
  - **Note**: If you are using Windows 10, ensure your version is **Windows 10 1809 (Build 17763)** or later. To check your Windows version, press `Win + R`, type `winver`, and press Enter.
- [Microsoft Visual C++ Redistributable v14](https://aka.ms/vc14/vc_redist.x64.exe)

### Pre-built Setup Executable

1. Download the latest release from the [Releases Page](https://github.com/wyx619/PyNCBIminer_NG/releases)
2. Run `PyNCBIminer-NG-x.x.x-Setup.exe`

### From Source

```bash
git clone https://github.com/wyx619/PyNCBIminer_NG.git
cd PyNCBIminer_NG
uv sync
uv run python src/Main_Fluent.py
```

***

## Quick Start

### DNAseqs Workflow

1. **Set Working Directory** — choose an output folder
2. **Configure Target** — select a gene marker (ITS, rbcL, matK, etc.) or enter a custom region
3. **Submit BLAST** — iterative search runs automatically
4. **Filter** — enable Extended Segments Refinement and/or Species-level Selection (with optional TNRS). When Species-level Selection is enabled, aggregation runs automatically and writes clean FASTA + CSV into `aggregated/`
5. **Align → Trim → Concatenate** — build your supermatrix in the Construction module

### Chloroplast Workflow

1. **Search & Download** — enter taxon names, set date range, download GenBank files
2. **Pre-filter** — remove low-quality genomes, retain top-N per taxon
3. **Extract & QC** — flag problematic genomes (low CDS / high ambiguity)
4. **Reannotate** — run PGA-NG on flagged genomes
5. **Get & Filter CDS** — extract plastid genes and filter by reference length
6. **Species-level Selection** — pick one representative genome per species (with optional TNRS)

***

## Supported DNAseqs Gene Markers

| Category    | Genes                                                                                 |
| ----------- | ------------------------------------------------------------------------------------- |
| Ribosomal   | 18S, 28S, ITS                                                                         |
| Chloroplast | rbcL, matK, ndhF, ndhD, ndhI, ndhJ-ndhK-ndhC, psbA-trnH, trnL-trnF, rpoB, rpoC1, atpB |
| Custom      | User-defined regions                                                                  |

***

## Output Structure

### DNAseqs Module

```
working_directory/
├── parameters/           # BLAST parameters and initial queries
├── results/              # Final sequence data
│   ├── blast_results_checked.fasta
│   ├── blast_results_filtered.fasta
│   └── blast_result_kept.txt
├── tnrs_cache/           # TNRS batch cache (if name resolution enabled)
└── tmp_files/            # Intermediate files
```

### Aggregated Output

Automatically generated after **Species-level Selection** (reduce), written into an `aggregated/` directory next to the marker working directory (no separate UI step required):

```
parent_directory/
└── aggregated/               # Per-marker aggregation results
    ├── ITS.fasta             # Clean FASTA (species-only headers; genus-level records governed by the TNRS "Remove genus rank" switch during selection)
    ├── ITS.csv               # accession ↔ species mapping
    ├── matK.fasta
    ├── matK.csv
    └── ...
```

### Chloroplast Module

```
output_directory/
├── *.gb                  # Downloaded/pre-filtered GenBank files
├── gb_info.csv           # Quality control report
├── length.csv            # Per-accession per-gene CDS lengths
├── organism.csv          # Deduplicated species list
├── *.fasta               # Filtered/selected CDS files
├── selected_sequences.csv  # Per-species table: species, representative accession, missing genes (after species-level selection)
└── tnrs_cache/           # TNRS batch cache (if name resolution enabled)
```

***

## Dependencies

- Python >= 3.12
- PySide6 + PySide6-Fluent-Widgets
- Biopython
- pandas, numpy, scipy

External tools (auto-installable from Settings page):

- MAFFT — multiple sequence alignment
- trimAl — alignment trimming
- PGA-NG — chloroplast genome re-annotation

***

## License

MIT License

***

## Authors

Yuxuan Wang, Ruijing Cheng,Xiaoting Xu
