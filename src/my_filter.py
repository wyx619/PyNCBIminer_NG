import shutil
from datetime import datetime
from pathlib import Path

from miner_filter import Miner_filter


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


def call_miner_filter(
    in_path,
    out_path,
    action,
    consensus_value,
    len_shresh,
    emit_log_callback=None,
    enable_tnrs=False,
    tnrs_sources=None,
    tnrs_accuracy=None,
    remove_genus_rank=True,
):
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
                emit_log(
                    "Results directory not found. Please run 'Submit New BLAST' first.",
                    "WARNING",
                )
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
                emit_log(
                    "Results directory not found. Please run 'Submit New BLAST' first.",
                    "WARNING",
                )
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
                remove_genus_rank=remove_genus_rank,
                emit_log=emit_log,
            )
            t1 = datetime.now()
            print("Running time: %s seconds" % (t1 - t0))
    elif action == 3:  # control extension, then reduce dataset
        for wd in wd_list:
            print("Control extension: %s" % wd)
            try:
                my_miner_filter = Miner_filter(wd, out_path)
            except FileNotFoundError as e:
                print(f"[WARNING] {e}")
                emit_log(
                    "Results directory not found. Please run 'Submit New BLAST' first.",
                    "WARNING",
                )
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
                emit_log(
                    "Results directory not found. Please run 'Submit New BLAST' first.",
                    "WARNING",
                )
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
                remove_genus_rank=remove_genus_rank,
                emit_log=emit_log,
            )
            t2 = datetime.now()
            print("Running time: %s seconds" % (t2 - t1))
