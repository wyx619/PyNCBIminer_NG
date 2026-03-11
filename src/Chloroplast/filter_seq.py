from pathlib import Path
import pandas as pd
import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed

from datetime import datetime
from Bio import SeqIO


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
    if gene not in _ref_len_dict:
        return file, None, f"gene {gene} is not in ref dictionary"

    try:
        seq_dict = create_seq_dict(Path(in_path) / file)
        seq_df = create_length_df(seq_dict)
        ref_len = _ref_len_dict[gene]

        filtered = filter_sequences(seq_df, seq_dict, ref_len)

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
    return {
        "Ang": {
            "accD": 1599,
            "atpA": 1524,
            "atpB": 1503,
            "atpE": 405,
            "atpF": 555,
            "atpH": 246,
            "atpI": 747,
            "ccsA": 942,
            "cemA": 690,
            "clpP": 609,
            "infA": 234,
            "matK": 1506,
            "ndhA": 1092,
            "ndhB": 1479,
            "ndhC": 363,
            "ndhD": 1503,
            "ndhE": 303,
            "ndhF": 2241,
            "ndhG": 534,
            "ndhH": 1182,
            "ndhI": 543,
            "ndhJ": 477,
            "ndhK": 762,
            "petA": 963,
            "petB": 648,
            "petD": 483,
            "petG": 114,
            "petL": 96,
            "petN": 90,
            "psaA": 2253,
            "psaB": 2205,
            "psaC": 246,
            "psaI": 111,
            "psaJ": 129,
            "psbA": 1053,
            "psbB": 1527,
            "psbC": 1422,
            "psbD": 1062,
            "psbE": 252,
            "psbF": 120,
            "psbH": 222,
            "psbI": 111,
            "psbJ": 123,
            "psbK": 186,
            "psbL": 117,
            "psbM": 108,
            "psbN": 132,
            "psbT": 108,
            "psbZ": 189,
            "rbcL": 1428,
            "rpl14": 369,
            "rpl16": 408,
            "rpl2": 822,
            "rpl20": 360,
            "rpl22": 375,
            "rpl23": 288,
            "rpl32": 174,
            "rpl33": 207,
            "rpl36": 114,
            "rpoA": 1005,
            "rpoB": 3219,
            "rpoC1": 2043,
            "rpoC2": 4110,
            "rps11": 417,
            "rps12": 258,
            "rps14": 303,
            "rps15": 264,
            "rps16": 237,
            "rps18": 306,
            "rps19": 279,
            "rps2": 711,
            "rps3": 657,
            "rps4": 606,
            "rps7": 468,
            "rps8": 399,
            "rrn16": 1490,
            "rrn23": 2814,
            "rrn4.5": 103,
            "rrn5": 121,
            "ycf1": 5385,
            "ycf15": 147,
            "ycf2": 6915,
            "ycf3": 507,
            "ycf4": 708,
            "ycf68": 234,
        },
        "Gym": {
            "accD": 1041,
            "atpA": 1524,
            "atpB": 1479,
            "atpE": 417,
            "atpF": 555,
            "atpH": 246,
            "atpI": 747,
            "ccsA": 966,
            "cemA": 786,
            "clpP": 609,
            "infA": 249,
            "matK": 1500,
            "ndhA": 1107,
            "ndhB": 1485,
            "ndhC": 363,
            "ndhD": 1503,
            "ndhE": 303,
            "ndhF": 2208,
            "ndhG": 543,
            "ndhH": 1182,
            "ndhI": 558,
            "ndhJ": 522,
            "ndhK": 813,
            "petA": 963,
            "petB": 648,
            "petD": 507,
            "petG": 114,
            "petL": 129,
            "petN": 90,
            "psaA": 2253,
            "psaB": 2205,
            "psaC": 246,
            "psaI": 111,
            "psaJ": 135,
            "psbA": 1062,
            "psbB": 1527,
            "psbC": 1422,
            "psbD": 1062,
            "psbE": 252,
            "psbF": 120,
            "psbH": 228,
            "psbI": 111,
            "psbJ": 123,
            "psbK": 177,
            "psbL": 117,
            "psbM": 105,
            "psbN": 132,
            "psbT": 108,
            "psbZ": 264,
            "rbcL": 1428,
            "rpl14": 369,
            "rpl16": 417,
            "rpl2": 831,
            "rpl20": 348,
            "rpl22": 420,
            "rpl23": 276,
            "rpl32": 210,
            "rpl33": 201,
            "rpl36": 114,
            "rpoA": 1026,
            "rpoB": 3219,
            "rpoC1": 2046,
            "rpoC2": 4101,
            "rps11": 393,
            "rps12": 258,
            "rps14": 303,
            "rps15": 270,
            "rps16": 255,
            "rps18": 228,
            "rps19": 279,
            "rps2": 708,
            "rps3": 657,
            "rps4": 606,
            "rps7": 471,
            "rps8": 399,
            "rrn16": 1475,
            "rrn23": 2813,
            "rrn4.5": 103,
            "rrn5": 121,
            "ycf1": 5082,
            "ycf15": 363,
            "ycf2": 7308,
            "ycf3": 510,
            "ycf4": 555,
            "ycf68": 240,
        },
    }.get(ref_type)


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
