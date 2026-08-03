# -*- coding: utf-8 -*-

import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path
import numpy as np
from Bio import SeqIO, SeqRecord, AlignIO

from format_wizard import check_outpath_validity, create_folder, get_file_handles


def _run_silent(command):

    if sys.platform == "win32":
        startupinfo = subprocess.STARTUPINFO()
        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        startupinfo.wShowWindow = subprocess.SW_HIDE
        creationflags = subprocess.CREATE_NO_WINDOW
        subprocess.run(
            command,
            shell=True,
            startupinfo=startupinfo,
            creationflags=creationflags,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            stdin=subprocess.DEVNULL,
        )
    else:
        subprocess.run(
            command, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
        )


def get_trimal_path():
    """Get path to trimal executable"""
    trimal_dir = Path.cwd() / "trimal"

    if trimal_dir.exists():
        for file in trimal_dir.rglob("*"):
            if file.is_file() and file.name.lower() in ["trimal.exe", "trimal"]:
                return str(file)

    if shutil.which("trimal"):
        return "trimal"

    raise FileNotFoundError(
        "trimal not found. Please go to Settings page to install trimAl first"
    )


def trimal(
    in_path,
    out_path="",
    htmlout=True,
    bp_length=False,
    implement_methods="automated1",
    gt="",
    st="",
    ct="",
    cons="",
    additional_params="",
    pure_command_mode=False,
    pure_command="",
    progress_callback=None,
):
    """
    call trimal to trim a set of aligned sequences
    ----------
    Parameters
    - in_path - the input file(s) and folder(s). could be a list or a string.
    - out_path - destination folder of output, where log files and result will be written.
    - htmlout - if True, produce report(s) in html format.
    - bp_length - if True, the description of each record in output file will be followed by kept length after trimal
    - implement_methods - corresponding to trimal params [gappyout, strict, strictplus, automated1]
    - gt - corresponding to trimal params gt: gapthreshold, 1 - (fraction of sequences with a gap allowed).
    - st - corresponding to trimal params st: simthreshold, Minimum average similarity allowed.
    - ct - corresponding to trimal params ct: conthreshold, Minimum consistency value allowed.
    - cons - corresponding to trimal params cons: Minimum percentage of the positions in the original alignment to conserve.
    - additional_params - additional parameters in the form of command
    - pure_command_mode - if True, only run commands in the textbox, one command per line
    - pure_command - run only if pure_command_mode is True, replace the GUI operations
    - progress_callback - optional callback function(message) to report progress
    -------
    Returns
    - file_handles - the valid input files if not in pure command mode
    - commands - the commands in pure command mode
    - total_time - total running time in seconds
    [] if path invalid"""
    # STEP 0: if pure command, then only execute input command
    if pure_command_mode:
        pure_command = pure_command.split("\n")
        for command in pure_command:
            _run_silent(command)
        return pure_command

    # STEP 1: check path validity and get file handles
    file_handles = get_file_handles(in_path)
    if len(file_handles) == 0:
        print("Could not find any fasta file in the input.")
        return [], None
    if not check_outpath_validity(out_path):
        return [], None

    # STEP 2: get parameters and call trimal
    total_time = 0.0
    for in_file in file_handles:
        basename = Path(in_file).name
        print(f"Trimming {basename}...")
        if progress_callback:
            progress_callback(f"Trimming {basename}...")
        t0 = datetime.now()
        out_file = Path(out_path) / f"trim_{basename}"
        in_file_str = str(Path(in_file))
        out_file_str = str(out_file)
        trimal_exe = get_trimal_path()

        command_parts = [
            f'"{trimal_exe}"',
            f'-in "{in_file_str}"',
            f'-out "{out_file_str}"',
        ]

        if htmlout:
            html_folder = Path(out_path) / "htmlout"
            create_folder(html_folder)
            html_out_file = html_folder / (Path(basename).stem + ".html")
            command_parts.append(f'-htmlout "{html_out_file}"')

        automated_methods = ["automated1", "strict", "strictplus", "gappyout"]
        is_automated = implement_methods in automated_methods

        if implement_methods:
            command_parts.append(f"-{implement_methods}")

        if is_automated:
            pass  # 自动化方法不传递手动阈值参数
        else:
            if gt:
                command_parts.append(f"-gt {gt}")
            if st:
                command_parts.append(f"-st {st}")
            if ct:
                print(
                    f"WARNING: -ct option is not compatible with -in input method, skipping ct={ct}"
                )
            if cons:
                command_parts.append(f"-cons {cons}")

        command_parts.append(additional_params)
        command = " ".join(command_parts)
        # print(f"DEBUG: Running trimal command: {command}")
        _run_silent(command)

        if not out_file.exists():
            print(f"Output file not created: {out_file}")
            continue

        # STEP 3: if bp_length is False:
        if not bp_length:
            records = []
            record_iter = SeqIO.parse(out_file, "fasta")
            records = [
                SeqRecord.SeqRecord(
                    record.seq,
                    # id=' '.join(record.description.split()[0]),
                    id="".join(record.description.split()[0]),
                    description="",
                )
                for record in record_iter
            ]
            SeqIO.write(records, out_file, "fasta")
        t1 = datetime.now()
        elapsed = (t1 - t0).total_seconds()
        total_time += elapsed
        print(" trimal Running time: %s seconds" % elapsed)

    return file_handles, total_time


def trim_start_end_optimized(boundaries_threshold=0.025, in_path=None):
    """
    边界修剪：去除比对序列两端高gap比例的区域
    
    Parameters:
    - boundaries_threshold: gap比例阈值，默认0.025
    - in_path: 输入文件夹路径，处理后会原地替换原文件
    """
    in_path_obj = Path(in_path)
    
    if in_path_obj.is_file():
        file_list = [in_path_obj]
    else:
        file_list = list(in_path_obj.glob("*.fasta")) + \
                    list(in_path_obj.glob("*.fas")) + \
                    list(in_path_obj.glob("*.fa"))
    
    if not file_list:
        print(f"No fasta files found in {in_path}")
        return
    
    total_time = 0.0
    
    for fasta_file in file_list:
        #print(f"Processing {fasta_file.name}...")
        
        try:
            
            alignments = AlignIO.read(fasta_file, "fasta")
            n_row = len(alignments)
            n_col = len(alignments[0])
            
            seq_array = np.array([[c for c in str(record.seq)] for record in alignments])
            gap_ratios = (seq_array == '-').sum(axis=0) / n_row
            
            valid_cols = np.where(gap_ratios < boundaries_threshold)[0]
            if len(valid_cols) == 0:
                i, j = 0, n_col
            else:
                i = valid_cols[0]
                j = valid_cols[-1] + 1
            
            trimmed_records = []
            for record in alignments:
                trimmed_seq = record.seq[i:j]
                record.seq = trimmed_seq
                trimmed_records.append(record)
            
            SeqIO.write(trimmed_records, fasta_file, "fasta")
        
            #print(f"  Completed in {elapsed:.2f}s")
            
        except Exception as e:
            print(f"  Error processing {fasta_file.name}: {e}")
            continue
    
    print(f"Boundary trimming completed: {len(file_list)} files processed in {total_time:.2f}s")
