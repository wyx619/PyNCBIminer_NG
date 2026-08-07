import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from pathlib import Path

import pandas as pd
from Bio import SeqIO

_selected_table = None


def init_worker(selected_table):
    global _selected_table
    _selected_table = selected_table


def process_file(file, in_path, out_path):
    """处理单个文件的辅助函数"""
    if file.split(".")[-1].lower() not in ["fa", "fas", "fasta"]:
        return file, None, None


    in_path = Path(in_path)
    out_path = Path(out_path)

    seq_dict = SeqIO.to_dict(
        SeqIO.parse(in_path / file, "fasta"),
        key_function=lambda record: record.description.split("|")[0].split(".")[0],
    )

    selected_table = _selected_table.set_index("filename")

    records = []
    accession_map = {}  # species (underscored) -> accession with version
    for index in selected_table.index:
        if index in seq_dict:
            record = seq_dict[index]
            species_name = (
                selected_table.loc[index]["organism"].strip().replace(" ", "_")
            )
            accession_map[species_name] = record.description.split("|")[0]
            record.id = species_name
            record.description = ""
            records.append(record)

    if records:
        SeqIO.write(records, out_path / file, "fasta")



    return file, accession_map, None


def select_seq_by_acc(
    in_path: str, out_path: str, selected_table: pd.DataFrame, num_processes: int = 3
):
    """使用多进程处理文件"""
    selected_table = selected_table.set_index("filename")
    in_path = Path(in_path)
    out_path = Path(out_path)

    file_list = [f.name for f in in_path.iterdir() if f.is_file()]

    if not file_list:
        print("No fasta files found")
        return

    out_path.mkdir(parents=True, exist_ok=True)

    selected_table = selected_table.reset_index()

    task_args = [(file, str(in_path), str(out_path)) for file in file_list]

    processes = max(1, min(num_processes, len(file_list)))

    with ThreadPoolExecutor(max_workers=processes, initializer=init_worker, initargs=(selected_table,)) as executor:
        futures = {
            executor.submit(process_file, arg[0], arg[1], arg[2]): arg[0]
            for arg in task_args
        }

        per_gene = {}  # gene stem -> {species: accession with version}
        for future in as_completed(futures):
            file, accession_map, error = future.result()
            if error:
                print(f"Error processing {file}: {error}")
                continue
            if accession_map is None:  # non-FASTA file, skipped
                continue
            per_gene[Path(file).stem] = accession_map

        _write_selected_table(per_gene, out_path)


def _write_selected_table(per_gene, out_path):
    """Write selected_sequences.csv: one row per species with its representative
    accession and the comma-separated list of missing genes.

    All genes of a species come from the same representative accession, so the
    per-gene matrix is redundant; a single species-level table suffices.
    """
    if not per_gene:
        print("No gene files produced selected sequences; no table written.")
        return
    genes = sorted(per_gene.keys())
    species_map = {}  # species -> [accession, set of present genes]
    for gene in genes:
        for species, acc in per_gene[gene].items():
            entry = species_map.setdefault(species, [acc, set()])
            entry[1].add(gene)

    if not species_map:
        print("No selected species; no table written.")
        return

    rows = [
        {
            "species": species,
            "accession": entry[0],
            "missing_genes": ",".join(g for g in genes if g not in entry[1]),
        }
        for species, entry in sorted(species_map.items())
    ]

    out_csv = Path(out_path) / "selected_sequences.csv"
    pd.DataFrame(rows, columns=["species", "accession", "missing_genes"]).to_csv(
        out_csv, index=False
    )
    print(f"Selected-species table written to {out_csv} ({len(rows)} species).")


def make_tab(
    in_path,
    enable_tnrs=False,
    tnrs_sources=None,
    tnrs_accuracy=None,
    remove_genus_rank=True,
    on_duplicates="keep_longest",
    emit_log=None,
):
    if emit_log is None:
        def emit_log(msg, level="INFO"):
            print(f"[{level}] {msg}")

    df = pd.read_csv(Path(in_path) / "length.csv", sep=",")

    meta_cols = {"filename", "organism", "cds_num"}
    cds_cols = [col for col in df.columns if col not in meta_cols]

    df1 = df[["filename", "organism", "cds_num"]].copy()
    df1["length"] = df[cds_cols].sum(axis=1)

    df_organism_all = df1[["organism"]].drop_duplicates().copy()
    df_organism_all.index = range(1, len(df_organism_all) + 1)
    df_organism_all.index.name = "ID"
    df_organism_all.to_csv(Path(in_path) / "organism.csv", index=True)

    if enable_tnrs:
        from Chloroplast.TNRS import TNRS_cached

        names = [n.strip() for n in df_organism_all["organism"].tolist()]
        cache_dir = Path(in_path) / "tnrs_cache"

        tnrs_result = TNRS_cached(
            taxonomic_names=names,
            sources=tnrs_sources,
            accuracy=tnrs_accuracy,
            cache_dir=cache_dir,
            emit_log=emit_log,
        )

        if tnrs_result is None:
            emit_log(
                "TNRS name resolution failed. Aborting selection. Re-run to retry failed batches.",
                "WARNING",
            )
            return None
        else:
            resolved_mask = (
                tnrs_result["Overall_score"].notna()
                & (tnrs_result["Overall_score"] >= (tnrs_accuracy or 0))
                & tnrs_result["Accepted_name"].notna()
                & (tnrs_result["Accepted_name"] != "")
                & tnrs_result["Taxonomic_status"].isin(["Accepted", "Synonym"])
            )
            if remove_genus_rank:
                resolved_mask &= tnrs_result["Accepted_name_rank"] != "genus"
            resolved = tnrs_result[resolved_mask].copy()

            rename_map = dict(
                zip(resolved["Name_submitted"], resolved["Accepted_name"])
            )

            n_unmatched = len(names) - len(rename_map)
            if n_unmatched > 0:
                unmatched = [n for n in names if n not in rename_map]
                emit_log(
                    f"TNRS: {len(rename_map)}/{len(names)} names resolved, "
                    f"{n_unmatched} not resolved (will be excluded): {unmatched[:10]}",
                    "WARNING",
                )

            df1["organism"] = df1["organism"].map(rename_map)
            df1 = df1.dropna(subset=["organism"])
            emit_log(f"TNRS completed. {df1['organism'].nunique()} species retained.", "INFO")

    # NOTE: no string-based genus heuristic here. Genus-level exclusion is
    # controlled exclusively by remove_genus_rank (TNRS rank filter above),
    # so the UI switch governs all genus handling.

    duplicate_counts = df1["organism"].value_counts().loc[lambda x: x > 1]
    if len(duplicate_counts):
        if on_duplicates == "skip":
            emit_log(f"Skipped {len(duplicate_counts)} duplicate species", "WARNING")
            return None
        elif on_duplicates == "keep_longest":
            emit_log(f"Keeping longest for {len(duplicate_counts)} duplicate species", "INFO")
            return df1.loc[df1.groupby("organism")["length"].idxmax()]
        else:
            raise ValueError(f"Invalid on_duplicates: {on_duplicates}")
    else:
        emit_log("No duplicate species.", "INFO")
        return df1.loc[df1.groupby("organism")["length"].idxmax()]


class CustomHelpFormatter(argparse.HelpFormatter):
    def format_help(self):
        help_text = super().format_help()
        description = """
Function: Correct the organism's scientific names and select the representative chloroplast genome for each species based on the maximum cumulative CDS length.
Author: Ruijing Cheng
        """
        return f"{description}\n\n{help_text}"


if __name__ == "__main__":
    parser = argparse.ArgumentParser(formatter_class=CustomHelpFormatter)
    # 输入输出参数
    parser.add_argument(
        "-i",
        "--input_dir",
        help="Input directory of filtered CDS files (.fasta)",
        required=True,
    )
    parser.add_argument(
        "-o",
        "--output_dir",
        help="Output directory for CDS sequences (.fasta) of unique organisms",
        required=True,
    )
    parser.add_argument(
        "-f",
        "--file_organism_name",
        help="Input path of standardized organism name file(.csv)",
        required=False,
    )
    parser.add_argument(
        "-t",
        "--threads",
        type=int,
        default=3,
        help="Number of threads to use %(default)s",
        required=False,
    )

    args = parser.parse_args()

    # 验证输入目录存在
    if not Path(args.input_dir).is_dir():
        raise NotADirectoryError(f"Input directory does not exist: {args.input_dir}")

    print(f"{'Input directory:':<20} {Path(args.input_dir).resolve()}")
    print(f"{'Output directory:':<20} {Path(args.output_dir).resolve()}")
    print(f"{'Organism names:':<20} {args.file_organism_name or 'Not specified'}")
    print(f"{'Threads:':<20} {args.threads}")

    if args.file_organism_name:
        if not Path(args.file_organism_name).is_file():
            raise FileNotFoundError(
                f"Organism name file not found: {args.file_organism_name}"
            )

    time0 = datetime.now()
    df_organism = make_tab(args.input_dir, args.file_organism_name)
    if df_organism is not None:
        select_seq_by_acc(
            args.input_dir,
            args.output_dir,
            df_organism,
            num_processes=args.threads,
        )

    time1 = datetime.now()
    print("Total running time: %s seconds" % (time1 - time0))
