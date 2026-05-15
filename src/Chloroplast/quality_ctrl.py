# -*- coding = utf-8 -*-

import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from Bio import SeqIO
from datetime import datetime
import pandas as pd
import multiprocessing
import warnings
warnings.filterwarnings("ignore")

from Chloroplast.PPA_80_CDS import PPA_80_CDS

def process_single_file(file_path, out_folder_path, cds_threshold, ambig_threshold):
    """处理单个GB文件的辅助函数"""
    #print(f"Collect information of : {file_path.name}\n")
    results = {
        "filename": file_path.stem,
        "organism": None,
        "unclear_bases": None,
        "unclear_ratio": None,
        "CDS": 0,
        "tRNA": 0,
        "rRNA": 0,
        "gene_count": 0,
        "sequence_length": None,
        "error": None,
    }
    is_problematic = False

    try:
        with open(file_path) as handle:
            record = SeqIO.read(handle, "genbank")

        gb_seq = str(record.seq).upper()
        results["sequence_length"] = len(gb_seq)
        un_atcg = sum(1 for c in gb_seq if c not in {"A", "T", "C", "G"})
        results["organism"] = record.annotations["organism"]
        results["unclear_bases"] = un_atcg
        results["unclear_ratio"] = un_atcg / len(gb_seq) if len(gb_seq) > 0 else 0

        feature_counts = {"CDS": 0, "tRNA": 0, "rRNA": 0}
        for feature in record.features:
            if feature.type == "gene":
                results["gene_count"] += 1
            elif feature.type == "CDS":
                gene = feature.qualifiers.get("gene", [""])[0]
                std_name = PPA_80_CDS.get(gene)
                if std_name is not None:
                    feature_counts["CDS"] += 1
            elif feature.type in feature_counts:
                feature_counts[feature.type] += 1

        results.update(feature_counts)

        if results["CDS"] < cds_threshold or results["unclear_ratio"] > ambig_threshold:
            is_problematic = True
            out_file = Path(out_folder_path) / (file_path.stem + "_reannotated.fasta")
            try:
                record.id = file_path.stem
                record.description = f"{record.annotations.get('organism', '')}|{record.description}"
                SeqIO.write([record], out_file, "fasta")

            except Exception as e:
                print(f"Error saving {file_path}: {str(e)}")
                results["error"] = f"Save failed: {str(e)}"
    except Exception as e:
        print(f"Error parsing {file_path}: {str(e)}\n")
        results["error"] = str(e)

    return results, is_problematic


def _process_file_wrapper(args):
    """Wrapper function for threading"""
    file_path, out_folder_path, cds_threshold, ambig_threshold = args
    from pathlib import Path
    return process_single_file(Path(file_path), Path(out_folder_path), cds_threshold, ambig_threshold)


def generate_genome_report(
    in_folder_path, out_folder_path, cds_threshold=80, ambig_threshold=0.2, threads=3
):
    """多进程生成基因组统计报告"""
    in_path = Path(in_folder_path)

    extensions = (".gb", ".gbf", ".gbk", ".genbank")
    gb_files = [f for ext in extensions for f in in_path.glob(f"*{ext}")]

    print(f"Found {len(gb_files)} GenBank files in {in_folder_path}")

    Path(out_folder_path).mkdir(parents=True, exist_ok=True)

    for stale in Path(out_folder_path).glob("*_reannotated.fasta"):
        stale.unlink()
        print(f"Cleared stale file: {stale.name}")

    all_results = []
    import  math
    if threads is None:
        threads = min(math.ceil(multiprocessing.cpu_count() * 0.25), len(gb_files))
    else:
        threads = min(threads, len(gb_files))

    print(f"Using {threads} threads for processing")

    args_list = [
        (str(f), str(out_folder_path), cds_threshold, ambig_threshold)
        for f in gb_files
    ]

    with ThreadPoolExecutor(max_workers=threads) as executor:
        futures = {executor.submit(_process_file_wrapper, arg): arg for arg in args_list}
        results = []
        for future in as_completed(futures):
            results.append(future.result())

    for r in results:
        all_results.append(r[0])

    df = pd.DataFrame(all_results)
    columns = [
        "filename",
        "organism",
        "sequence_length",
        "gene_count",
        "CDS",
        "tRNA",
        "rRNA",
        "unclear_bases",
        "unclear_ratio",
        "error",
    ]
    df = df.reindex(columns=columns)
    df.to_csv(in_path / "gb_info.csv", index=False)

    return len(df[df["error"].notna()])


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Quality control for chloroplast genomes"
    )
    parser.add_argument(
        "-i", "--input_dir", help="Input directory path of gb file.", required=True
    )
    parser.add_argument(
        "-o",
        "--output_dir",
        help="Output directory for fasta files (only created for problematic GenBank annotations)",
        required=True,
    )
    parser.add_argument(
        "-c",
        "--cds_threshold",
        type=int,
        default=80,
        help="Minimum CDS count threshold (default: %(default)s)",
    )
    parser.add_argument(
        "-a",
        "--ambig_threshold",
        type=float,
        default=0.2,
        help="Maximum ambiguous base proportion (default: %(default)s)",
    )
    parser.add_argument(
        "-t",
        "--threads",
        type=int,
        default=None,
        help="Number of threads to use (default: auto-detect)",
    )

    args = parser.parse_args()

    print("\n" + "=" * 50)
    print(f"{'Configuration Summary':^50}")
    print("=" * 50)
    print(f"Input directory:      {args.input_dir}")
    print(f"Output directory:     {args.output_dir}")
    print(f"CDS threshold:        {args.cds_threshold}")
    print(f"Ambiguity threshold:  {args.ambig_threshold:.1%}")
    print(f"Processing threads:   {args.threads}")
    print("=" * 50 + "\n")

    input_dir = Path(args.input_dir)
    output_dir = Path(args.output_dir)
    cds_threshold = args.cds_threshold
    ambig_threshold = args.ambig_threshold
    threads = args.threads

    time0 = datetime.now()
    error_count = generate_genome_report(
        input_dir,
        output_dir,
        cds_threshold,
        ambig_threshold,
        threads,
    )
    time1 = datetime.now()

    if error_count:
        print(f"\nCompleted with {error_count} file(s) having errors.")
    else:
        print("\nAll gb files processed successfully.")

    print(f"Total running time: {time1 - time0}")
