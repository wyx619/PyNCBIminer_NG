"""
Multi-marker summarization utilities.

Combines species-level selection results across multiple gene markers
into unified records and sequence collections for downstream supermatrix construction.
"""

from pathlib import Path

import pandas as pd
from Bio import SeqIO


def combine_keep_records(wd_list, out_path):
    """Merge blast_result_kept.txt from multiple markers into one combined table.

    Parameters
    ----------
    wd_list : list of str/Path
        Working directories of each marker.
    out_path : str/Path
        Output directory for combined_records.txt.
    """
    combined_records = None
    col_list = ["taxon_name"]
    out_path = Path(out_path)

    for wd in wd_list:
        wd = Path(wd)
        name = wd.name
        col_list.append(name)

        if out_path == wd:
            kept_file = out_path / "results" / "blast_result_kept.txt"
        else:
            kept_file = out_path / name / "results" / "blast_result_kept.txt"

        try:
            df = pd.read_table(kept_file, sep="\t")
            # keep only species-level taxa (name must contain at least one "_")
            df = df[df["taxon_name"].astype(str).str.contains("_", na=False)]
            if combined_records is None:
                combined_records = df[["taxon_name", "subject_acc.ver"]]
            else:
                combined_records = pd.merge(
                    combined_records,
                    df[["taxon_name", "subject_acc.ver"]],
                    how="outer",
                    on="taxon_name",
                )
            combined_records.columns = col_list
        except FileNotFoundError:
            print(f"{name} has not been reduced.")

    if combined_records is not None:
        combined_records = combined_records.fillna("-")
        combined_records.to_csv(
            out_path / "combined_records.txt", index=False, sep="\t"
        )
        print(f"Combined records save in {out_path / 'combined_records.txt'}")
    else:
        print("No records found to combine.")


def put_filtered_seq_together(wd_list, out_path):
    """Copy filtered FASTA from multiple markers into a single directory.

    Parameters
    ----------
    wd_list : list of str/Path
        Working directories of each marker.
    out_path : str/Path
        Output directory; filtered_seqs/ will be created inside.
    """
    print("Copying filtered sequences into one directory...")
    out_path = Path(out_path)

    for wd in wd_list:
        wd = Path(wd)
        name = wd.name
        filtered_seqs_path = out_path / "filtered_seqs"
        if not filtered_seqs_path.exists():
            filtered_seqs_path.mkdir()

        if out_path == wd:
            filtered_file = out_path / "results" / "blast_results_filtered.fasta"
        else:
            filtered_file = out_path / name / "results" / "blast_results_filtered.fasta"

        try:
            skipped = 0
            with open(filtered_seqs_path / (name + ".fasta"), "w") as fw:
                for record in SeqIO.parse(filtered_file, "fasta"):
                    parts = record.description.split("|")
                    if len(parts) < 2:
                        skipped += 1
                        continue
                    species = parts[1].strip()
                    # drop genus-level records (name without any "_")
                    if "_" not in species:
                        skipped += 1
                        continue
                    fw.write(">" + species)
                    fw.write("\n")
                    fw.write(str(record.seq))
                    fw.write("\n")
            if skipped:
                print(
                    f"{name}: skipped {skipped} genus-level sequence(s) "
                    f"(no species epithet in the name)."
                )

        except FileNotFoundError:
            print(f"{name} has not been copied.")

    print("All filtered sequences are into 'filtered_seqs' folder")
