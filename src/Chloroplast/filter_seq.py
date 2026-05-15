from pathlib import Path
import pandas as pd
import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed

from datetime import datetime
from Bio import SeqIO

from Chloroplast.PPA_80_CDS import PPA_80_CDS, ANG_REF_LEN, GYM_REF_LEN


_ref_len_dict = None
_lower_bound = None
_upper_bound = None


def init_worker(ref_len_dict, lower_bound, upper_bound):
    global _ref_len_dict, _lower_bound, _upper_bound
    _ref_len_dict = ref_len_dict
    _lower_bound = lower_bound
    _upper_bound = upper_bound


def create_seq_dict(fasta_path):
    return SeqIO.to_dict(
        SeqIO.parse(fasta_path, "fasta"), key_function=lambda r: r.description
    )


def create_length_df(seq_dict):
    data = [(key.split("|")[0], key, len(seq_dict[key].seq)) for key in seq_dict]
    return pd.DataFrame(data, columns=["accession", "description", "length"])


def filter_sequences(seq_df, seq_dict, ref_len):
    low = _lower_bound * ref_len
    high = _upper_bound * ref_len

    results = []
    for name, group in seq_df.groupby("accession"):
        idx_max = group["length"].idxmax()
        seq_rec = seq_dict[group.loc[idx_max, "description"]]
        seq_len = len(seq_rec.seq)

        if low <= seq_len <= high:
            results.append((seq_rec, seq_len))

    return results


def process_file(args):
    in_path, out_path, file = args
    global _ref_len_dict, _lower_bound, _upper_bound
    gene = Path(file).stem
    print(f"Filter record of : {gene} by length")

    try:
        seq_dict = create_seq_dict(Path(in_path) / file)
        seq_df = create_length_df(seq_dict)

        if gene in _ref_len_dict:
            ref_len = _ref_len_dict[gene]
            filtered = filter_sequences(seq_df, seq_dict, ref_len)
        else:
            filtered = []
            for name, group in seq_df.groupby("accession"):
                idx_max = group["length"].idxmax()
                seq_rec = seq_dict[group.loc[idx_max, "description"]]
                seq_len = len(seq_rec.seq)
                filtered.append((seq_rec, seq_len))

        if filtered:
            records = [seq_rec for seq_rec, seq_len in filtered]
            SeqIO.write(records, Path(out_path) / file, "fasta")

        return (
            file,
            {
                seq_rec.description.split("|")[0].split(".")[0]: seq_len
                for seq_rec, seq_len in filtered
            },
            None,
        )
    except Exception as e:
        return file, None, str(e)


def select_seq_by_len(
    in_path, out_path, ref_len_dict, lower_bound, upper_bound, threads=3
):
    in_path = Path(in_path)
    out_path = Path(out_path)

    file_list = [
        f.name
        for f in in_path.iterdir()
        if f.suffix.lower() in {".fa", ".fas", ".fasta"}
    ]
    if not file_list:
        print("No fasta files found")
        return

    cds_num_path = in_path / "cds_num.csv"
    if not cds_num_path.exists():
        print(f"Error: {cds_num_path} not found")
        return

    df0 = pd.read_csv(cds_num_path, index_col="filename", sep=",")
    out_path.mkdir(parents=True, exist_ok=True)

    task_args = [
        (str(in_path), str(out_path), file)
        for file in file_list
    ]

    threads = max(1, min(threads, len(file_list)))

    with ThreadPoolExecutor(max_workers=threads, initializer=init_worker, initargs=(ref_len_dict, lower_bound, upper_bound)) as executor:
        futures = {
            executor.submit(process_file, arg): Path(arg[2]).stem for arg in task_args
        }

        for future in as_completed(futures):
            file, updates, error = future.result()
            gene = Path(file).stem

            if error:
                print(f"Processing {file} error: {error}")
                continue

            df0[gene] = df0.get(gene, pd.NA)

            if updates:
                for acc, length in updates.items():
                    if acc in df0.index:
                        df0.loc[acc, gene] = length

    df0.to_csv(out_path / "length.csv", index=True, sep=",")


def validate_args(args):
    if not (0 < args.lower_bound <= 3) or not (0 < args.upper_bound <= 3):
        print("Error: Bounds must be between 0 and 3")
        exit(1)
    if args.lower_bound >= args.upper_bound:
        print("Error: Lower bound must be less than upper bound")
        exit(1)
    if args.threads < 1:
        print("Warning: Thread count reset to minimum value 1")
        args.threads = 1
    if not Path(args.input_dir).exists():
        print(f"Error: Input directory does not exist: {args.input_dir}")
        exit(1)


def get_ref_dict(ref_type):
    if ref_type == "Ang":
        return ANG_REF_LEN
    if ref_type == "Gym":
        return GYM_REF_LEN
    return None


class CustomHelpFormatter(argparse.HelpFormatter):
    def format_help(self):
        help_text = super().format_help()
        description = """
        Function: Filter sequences with CDS lengths within a defined percentile range(default: 50%-200%) of the 
        orthologous CDS length distribution from reference genomes.
        Author: Ruijing Cheng
        """
        return f"{description}\n\n{help_text}"


if __name__ == "__main__":
    parser = argparse.ArgumentParser(formatter_class=CustomHelpFormatter)
    parser.add_argument(
        "-i",
        "--input_dir",
        help="Input directory containing CDS files (.fasta)",
        required=True,
    )
    parser.add_argument(
        "-o",
        "--output_dir",
        help="Output directory for filtered CDS sequences (.fasta)",
        required=True,
    )
    parser.add_argument(
        "-r",
        "--ref_orthologous",
        choices=["Ang", "Gym"],
        help="Reference orthologous CDS lengths:\n"
        "Ang: Angiosperm (flowering plants)\n"
        "Gym: Gymnosperm (conifers, cycads, etc.)",
        required=True,
    )
    parser.add_argument(
        "-lb",
        "--lower_bound",
        type=float,
        default=0.5,
        help="Lower bound multiplier for reference length (default: %(default)s)",
    )
    parser.add_argument(
        "-ub",
        "--upper_bound",
        type=float,
        default=2.0,
        help="Upper bound multiplier for reference length (default: %(default)s)",
    )
    parser.add_argument(
        "-t",
        "--threads",
        type=int,
        default=3,
        help="Number of processing threads to use (default: %(default)s)",
    )

    args = parser.parse_args()

    validate_args(args)

    Path(args.output_dir).mkdir(parents=True, exist_ok=True)


    print(f"Input directory:     {args.input_dir}")
    print(f"Output directory:    {args.output_dir}")
    print(
        f"Reference type:      {'Angiosperm' if args.ref_orthologous == 'Ang' else 'Gymnosperm'}"
    )
    print(f"Length range:       {args.lower_bound}x - {args.upper_bound}x of reference")
    print(f"Processing threads:  {args.threads}")
    print("=" * 50 + "\n")

    ref_dict = get_ref_dict(args.ref_orthologous)

    time0 = datetime.now()
    select_seq_by_len(
        args.input_dir,
        args.output_dir,
        ref_dict,
        args.lower_bound,
        args.upper_bound,
        args.threads,
    )
    time1 = datetime.now()
    print(f"Total running time: {time1 - time0}")
