# PyNCBIminer-NG

A powerful, user-friendly graphical interface for efficient retrieval and analysis of GenBank sequence data.

## Overview

PyNCBIminer-NG is a next-generation bioinformatics tool that simplifies the retrieval of nucleotide sequences from NCBI GenBank. Whether you are studying plant phylogenetics, bacterial diversity, or any organism of interest, PyNCBIminer-NG streamlines your workflow by automating BLAST iterations, sequence filtering, multiple sequence alignment, and supermatrix construction—no programming experience required.

---

## Key Features

### 🔍 Intelligent Sequence Retrieval

- **Automated BLAST Iterations**: Automatically performs iterative BLAST searches until no new relevant sequences are found
- **Smart Query Selection**: Intelligently selects optimal reference sequences at each iteration to maximize retrieval coverage
- **Resume Capability**: Interrupted workflow? No problem—resume from where you left off anytime
- **Customizable Taxa & Genes**: Specify your target taxa and gene markers (ITS, rbcL, matK, ndhF, and more)

### 🧬 Comprehensive Sequence Processing

- **Sequence Filtering**: Remove erroneous annotations, control sequence extensions, and reduce datasets to one representative sequence per species
- **Quality Control**: Built-in tools to identify and handle potentially erroneous sequences
- **Flexible Output**: Results organized in clear folder structures with detailed sequence information

### 📊 Multiple Sequence Alignment & Trimming

- **MAFFT Integration**: High-quality multiple sequence alignments using the industry-standard MAFFT algorithm
- **trimAl Support**: Automated alignment trimming with customizable methods (automated1, gappyout, strict, strictplus)
- **Chloroplast Mode**: Specialized workflow for chloroplast genome analysis with boundary trimming

### 🏗️ Supermatrix Construction

- **Concatenation**: Combine multiple gene markers into a single supermatrix for phylogenomic analysis
- **Automatic Gap Handling**: Missing markers are automatically filled with gaps

### 🌿 Chloroplast Genome Analysis (New!)

- Specialized tools for chloroplast genome mining
- Extract CDS regions from GenBank files
- Quality control and sequence filtering for chloroplast sequences

### 🖥️ User-Friendly Interface

- **Modern Fluent Design**: Clean, intuitive PySide6-based interface
- **Real-time Progress Tracking**: Monitor BLAST iterations and sequence processing
- **Customizable Themes**: Light, Dark, or Auto (follows system) mode
- **Software Auto-Installation**: MAFFT, trimAl, and PGA-NG can be installed directly from the app

---

## Installation

### Prerequisites

- Windows 10/11
- Microsoft Visual C++ Redistributable v14 required, if not installed, [download](https://aka.ms/vc14/vc_redist.x64.exe) and install first.

### Pre-built Executable

1. Download the latest release from [Release Page](https://github.com/wyx619/PyNCBIminer_NG/releases)
2. Double-click `PyNCBIminer-NG.exe` to launch

---

## Quick Start Guide

### Step 1: Set Your Working Directory

Choose a folder where all outputs will be saved.

### Step 2: Configure Target Region

- Select a predefined gene marker (ITS, rbcL, matK, etc.) or enter a custom region
- Optionally provide your email for NCBI compliance

### Step 3: Submit BLAST

Click "Submit New BLAST" and watch as PyNCBIminer automatically:

- Searches NCBI for matching sequences
- Identifies and retrieves new reference sequences
- Iterates until no new sequences are found

### Step 4: Process Your Sequences

Use the Construction Module to:

1. **Filter** sequences (remove errors, reduce to one per species)
2. **Align** sequences with MAFFT
3. **Trim** alignments with trimAl
4. **Concatenate** multiple genes into a supermatrix

---

## Supported Gene Markers

PyNCBIminer-NG comes pre-configured with reference sequences for:

| Category    | Genes                                                                           |
| ----------- | ------------------------------------------------------------------------------- |
| Ribosomal   | 18S, 28S, ITS                                                                   |
| Chloroplast | rbcL, matK, ndhF, ndhD, ndhI, ndhJ-ndhK-ndhC, psbA-trnH, trnL-trnF, rpoB, rpoC1 |
| Custom      | User-defined regions                                                            |

---

## Output Structure

After a successful retrieval, your working directory will contain:

```
working_directory/
├── parameters/           # BLAST parameters and initial queries
│   ├── blast_parameters.txt
│   ├── initial_queries.fasta
│   └── ref_seq/         # Reference sequences
├── results/              # Final sequence data
│   ├── blast_results.txt
│   ├── blast_results_checked.fasta    # Clean sequences for analysis
│   └── erroneous_sequences.fasta
└── tmp_files/           # Intermediate files from each BLAST round
```

---

## Documentation

For detailed instructions, parameter explanations, and example workflows, please refer to the Manunal.

---

## Troubleshooting

**Q: NCBI is blocking my requests**
A: Provide a valid email address in the Entrez Email field. NCBI may temporarily block requests without an email.

**Q: Some sequences are missing**
A: Check if your target taxa have sequences deposited in GenBank. You can also try extending the search date range.

**Q: MAFFT/trimAl not found**
A: Use the "Software Settings" page in PyNCBIminer-NG to automatically download and install these tools.

---

## Citation

If you use PyNCBIminer-NG in your research, please cite:

> PyNCBIminer: A user-friendly graphical interface for efficient and precise retrieval of GenBank data

---

## License

MIT License

---

*PyNCBIminer-NG — Empowering phylogenetic research for everyone.*
