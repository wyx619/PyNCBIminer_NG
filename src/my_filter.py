# *-* coding:utf-8 *-*
# @Time:2024/2/3 15:17
# @Author:Ruijing Cheng
# @File:my_filter.py
# @Software:PyCharm

from pathlib import Path
from miner_filter import Miner_filter
from datetime import datetime
import shutil
import pandas as pd
from Bio import SeqIO


def rename_results(wd):
    file_list = [f.name for f in (Path(wd) / "results").iterdir()]
    if (
        "blast_results_controlled.fasta" in file_list
        and "blast_results_checked.fasta" in file_list
    ):
        (Path(wd) / "results" / "not_controlled").mkdir(exist_ok=True)
        shutil.copy(
            Path(wd) / "results" / "blast_results_checked.fasta",
            Path(wd) / "results" / "not_controlled" / "blast_results_checked.fasta",
        )
        (Path(wd) / "results" / "blast_results_checked.fasta").unlink()
        (Path(wd) / "results" / "blast_results_controlled.fasta").rename(
            Path(wd) / "results" / "blast_results_checked.fasta"
        )
        print("Copy blast_result_checked.fasta the not_controlled folder. ")
        print("Renamed blast_result_controlled.fasta as blast_results_checked.fasta. ")


def combine_keep_records(wd_list, out_path):
    #print("Combining keep records...")
    combined_records = None
    col_list = ["taxon_name"]
    out_path = Path(out_path)

    for wd in wd_list:
        wd = Path(wd)
        name = wd.name
        col_list.append(name)

        # 当 out_path == wd 时，结果直接在 out_path/results/
        # 当 out_path != wd 时，结果在 out_path/name/results/
        if out_path == wd:
            kept_file = out_path / "results" / "blast_result_kept.txt"
        else:
            kept_file = out_path / name / "results" / "blast_result_kept.txt"

        try:
            df = pd.read_table(kept_file, sep="\t")
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
            print("%s has not been reduced." % name)

    if combined_records is not None:
        combined_records = combined_records.fillna("-")
        combined_records.to_csv(
            out_path / "combined_records.txt", index=False, sep="\t"
        )
        print(f"Combined records save in {out_path / 'combined_records.txt'}")
    else:
        print("No records found to combine.")


def put_filtered_seq_together(wd_list, out_path):
    print("Copying filtered sequences into one directory...")
    out_path = Path(out_path)

    for wd in wd_list:
        wd = Path(wd)
        name = wd.name
        filtered_seqs_path = out_path / "filtered_seqs"
        if not filtered_seqs_path.exists():
            filtered_seqs_path.mkdir()

        # 当 out_path == wd 时，结果直接在 out_path/results/
        # 当 out_path != wd 时，结果在 out_path/name/results/
        if out_path == wd:
            filtered_file = out_path / "results" / "blast_results_filtered.fasta"
        else:
            filtered_file = out_path / name / "results" / "blast_results_filtered.fasta"

        try:
            with open(filtered_seqs_path / (name + ".fasta"), "w") as fw:
                for record in SeqIO.parse(filtered_file, "fasta"):
                    fw.write(">" + record.description.split("|")[1])
                    fw.write("\n")
                    fw.write(str(record.seq))
                    fw.write("\n")

        except FileNotFoundError:
            print("%s has not been copied." % name)

    print("All filtered sequences are into ‘filtered_seqs’ folder")


def call_miner_filter(in_path, out_path, action, consensus_value, len_shresh, emit_log_callback=None,
                     enable_tnrs=False, tnrs_sources=None, tnrs_accuracy=None):
    """
    Call miner_filter, and modify input and output file names, using one thread.
    :param in_path: working directory of one marker or the parent directory of multiple working directories
    :param action: 1-control extension, 2-reduce dataset, 3-control extension, then reduce dataset
    :param len_shresh:
    :param emit_log_callback: optional callback function for emitting logs
    :return:
    """
    
    def emit_log(message, level="WARNING"):
        if emit_log_callback:
            emit_log_callback(message, level)
        else:
            print(f"[{level}] {message}")
    # check in_path
    dir_list = [
        f.name for f in Path(in_path).iterdir() if (Path(in_path) / f.name).is_dir()
    ]
    wd_list = []
    if "results" in dir_list and "tmp_files" in dir_list:
        wd_list = [in_path]
    else:
        for directory in dir_list:
            sub_dir_list = [f.name for f in (Path(in_path) / directory).iterdir()]
            if "results" in sub_dir_list and "tmp_files" in sub_dir_list:
                wd_list.append(Path(in_path) / Path(directory))
    if len(wd_list) == 0:
        print("The input path is not correct.")
        print(
            "Please provide working directory of one marker or the parent directory of multiple working directories."
        )

    # check out_path

    if action == 1:  # control extension
        for wd in wd_list:
            print("Control extension: %s" % wd)
            try:
                my_miner_filter = Miner_filter(wd, out_path)
            except FileNotFoundError as e:
                print(f"[WARNING] {e}")
                emit_log("Results directory not found. Please run 'Submit New BLAST' first.", "WARNING")
                continue
            t0 = datetime.now()
            my_miner_filter.control_extension(gappyness_threshold=0.5)
            t1 = datetime.now()
            print("Running time: %s seconds" % (t1 - t0))
    elif action == 2:  # reduce dataset
        for wd in wd_list:
            rename_results(wd)
            print("Reduce dataset: %s" % wd)
            try:
                my_miner_filter = Miner_filter(wd, out_path)
            except FileNotFoundError as e:
                print(f"[WARNING] {e}")
                emit_log("Results directory not found. Please run 'Submit New BLAST' first.", "WARNING")
                continue
            t0 = datetime.now()
            my_miner_filter.reduce_dataset(
                consensus_value=consensus_value,  # for consensus calculation
                subsp=True,
                var=True,
                f=True,  # for species combination
                sp=True,
                cf=True,
                aff=True,
                x=True,
                length_threshold=len_shresh,
                ignore_gap=True,
                enable_tnrs=enable_tnrs,
                tnrs_sources=tnrs_sources,
                tnrs_accuracy=tnrs_accuracy,
                emit_log=emit_log,
            )
            t1 = datetime.now()
            print("Running time: %s seconds" % (t1 - t0))
        combine_keep_records(wd_list, out_path)
    elif action == 3:  # control extension, then reduce dataset
        for wd in wd_list:
            print("Control extension: %s" % wd)
            try:
                my_miner_filter = Miner_filter(wd, out_path)
            except FileNotFoundError as e:
                print(f"[WARNING] {e}")
                emit_log("Results directory not found. Please run 'Submit New BLAST' first.", "WARNING")
                continue
            t0 = datetime.now()
            my_miner_filter.control_extension(gappyness_threshold=0.5)
            t1 = datetime.now()
            print("Running time: %s seconds" % (t1 - t0))

            rename_results(wd)

            print("Reduce dataset: %s" % wd)
            try:
                my_miner_filter = Miner_filter(wd, out_path)
            except FileNotFoundError as e:
                print(f"[WARNING] {e}")
                emit_log("Results directory not found. Please run 'Submit New BLAST' first.", "WARNING")
                continue
            my_miner_filter.reduce_dataset(
                consensus_value=consensus_value,  # for consensus calculation
                subsp=True,
                var=True,
                f=True,  # for species combination
                sp=True,
                cf=True,
                aff=True,
                x=True,
                length_threshold=len_shresh,
                ignore_gap=True,
                enable_tnrs=enable_tnrs,
                tnrs_sources=tnrs_sources,
                tnrs_accuracy=tnrs_accuracy,
                emit_log=emit_log,
            )
            t2 = datetime.now()
            print("Running time: %s seconds" % (t2 - t1))
        combine_keep_records(wd_list, out_path)
        put_filtered_seq_together(wd_list, out_path)
