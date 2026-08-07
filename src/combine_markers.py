"""
Multi-marker summarization utilities.

Aggregates species-level selection results across multiple gene markers
into a unified directory of per-marker FASTA + CSV files
for downstream supermatrix construction.
"""

from pathlib import Path

from Bio import SeqIO


def _discover_working_dirs(in_path):
    """Discover marker working directories (same logic as call_miner_filter).

    Returns [in_path] when in_path itself is a working directory
    (contains results/ and tmp_files/), otherwise the subdirectories
    that qualify as working directories.
    """
    in_path = Path(in_path)
    dir_list = [f.name for f in in_path.iterdir() if (in_path / f.name).is_dir()]
    wd_list = []
    if "results" in dir_list and "tmp_files" in dir_list:
        wd_list = [in_path]
    else:
        for directory in dir_list:
            sub_dir_list = [f.name for f in (in_path / directory).iterdir()]
            if "results" in sub_dir_list and "tmp_files" in sub_dir_list:
                wd_list.append(in_path / directory)
    return wd_list


def aggregate_marker_outputs(in_path, emit_log=None):
    """Aggregate species-level selection results into an aggregated/ directory.

    For each marker working directory, writes:
        <container>/aggregated/<marker>.fasta   # clean headers (species only)
        <container>/aggregated/<marker>.csv     # accession <-> species mapping

    The container is the parent directory of a single-marker input, or the
    input directory itself when multiple markers are supplied. The aggregated/
    directory is created if missing; existing target files are overwritten.
    """
    if emit_log is None:

        def emit_log(msg, level="INFO"):
            print(f"[{level}] {msg}")

    in_path = Path(in_path)
    wd_list = _discover_working_dirs(in_path)
    if not wd_list:
        emit_log("No valid working directories found for aggregation.", "WARNING")
        return

    if len(wd_list) == 1 and wd_list[0] == in_path:
        agg_dir = in_path.parent / "aggregated"
    else:
        agg_dir = in_path / "aggregated"
    agg_dir.mkdir(parents=True, exist_ok=True)

    for wd in wd_list:
        marker = wd.name
        src = wd / "results" / "blast_results_filtered.fasta"
        if not src.exists():
            emit_log(
                f"{marker}: blast_results_filtered.fasta not found, skipped.",
                "WARNING",
            )
            continue

        fasta_out = agg_dir / f"{marker}.fasta"
        csv_out = agg_dir / f"{marker}.csv"

        n_seqs = 0
        with open(fasta_out, "w") as fw, open(csv_out, "w") as fc:
            fc.write("accession,species\n")
            for record in SeqIO.parse(src, "fasta"):
                parts = record.description.split("|")
                if len(parts) < 2:
                    continue
                species = parts[1].strip()
                fw.write(f">{species}\n{str(record.seq)}\n")
                fc.write(f"{parts[0].strip()},{species}\n")
                n_seqs += 1

        emit_log(
            f"{marker}: {n_seqs} sequences -> {fasta_out.name}, {csv_out.name}",
            "INFO",
        )

    emit_log(f"Aggregated outputs saved in {agg_dir}", "INFO")
