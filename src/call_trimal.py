# -*- coding: utf-8 -*-
from pathlib import Path
from Bio import SeqIO, SeqRecord
from format_wizard import check_outpath_validity, get_file_handles, create_folder
from datetime import datetime

import os
import shutil
import subprocess
import sys


def _run_silent(command):
    """静默执行命令，不输出任何内容到控制台"""
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
        subprocess.run(command, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def get_trimal_path():
    """Get path to trimal executable"""
    # Try to find trimal in common locations
    trimal_dir = Path.cwd() / "trimal"

    if trimal_dir.exists():
        # Recursively search for trimal executable
        for root, dirs, files in os.walk(trimal_dir):
            for file in files:
                if file.lower() in ["trimal.exe", "trimal"]:
                    return str(Path(root) / file)

    # Check if it's in PATH
    if shutil.which("trimal"):
        return "trimal"

    # If not found, return "trimal" and let's error show
    return "trimal"


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
        print("Trimming %s..." % in_file)
        if progress_callback:
            progress_callback(f"Trimming {Path(in_file).name}...")
        t0 = datetime.now()
        basename = Path(in_file).name
        out_file = Path(out_path) / f"trim_{basename}"
        in_file_str = str(Path(in_file))
        out_file_str = str(out_file)
        print(f"Input file: {in_file_str}")
        print(f"Output file: {out_file_str}")

        trimal_exe = get_trimal_path()
        print(f"Using trimal: {trimal_exe}")

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

        if implement_methods:
            command_parts.append(f"-{implement_methods}")
        if gt:
            command_parts.append(f"-gt {gt}")
        if st:
            command_parts.append(f"-st {st}")
        if ct:
            print(f"WARNING: -ct option is not compatible with -in input method, skipping ct={ct}")
        if cons:
            command_parts.append(f"-cons {cons}")

        command_parts.append(additional_params)
        command = " ".join(command_parts)
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
