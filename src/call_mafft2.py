import shutil
from datetime import datetime
from pathlib import Path

from Bio import SeqIO

from format_wizard import (
    check_inpath_validity,
    check_outpath_validity,
    get_file_handles,
)
from functional import run_command


def get_mafft_path():
    """Get path to mafft executable"""

    mafft_bat = Path.cwd() / "mafft" / "mafft-win" / "mafft.bat"
    if mafft_bat.exists():
        # mafft-win 的 mafft.bat 依赖 usr/bin/bash.exe 等配套文件，
        # 若只复制了 mafft.bat 而未复制整个 mafft-win 目录，运行时会报
        # "系统找不到指定的路径"，这里提前给出明确提示。
        if not (mafft_bat.parent / "usr" / "bin" / "bash.exe").exists():
            raise FileNotFoundError(
                "MAFFT installation is incomplete: usr/bin files are missing under "
                f"{mafft_bat.parent}. Please reinstall MAFFT from Settings page."
            )
        return str(mafft_bat)

    if shutil.which("mafft"):
        return "mafft"

    raise FileNotFoundError(
        "mafft not found. Please go to Settings page to install MAFFT first"
    )


def _resolve_same_path(p1, p2):
    """比较两个路径是否指向同一文件（忽略大小写），避免 cmd 重定向截断输入"""
    try:
        return str(Path(p1).resolve()).casefold() == str(Path(p2).resolve()).casefold()
    except Exception:
        return False


def mafft_add(in_path, in_file, out_path, cmd_str):
    print(f"Aligning {in_file}...")

    def _run_checked(command, out_file):
        r = run_command(command)
        if r.returncode != 0:
            print(
                f"[ERROR] MAFFT command failed (RC={r.returncode}): {command}",
                flush=True,
            )
            return False
        if not Path(out_file).exists() or Path(out_file).stat().st_size == 0:
            print(
                f"[ERROR] MAFFT produced an empty output: {out_file}",
                flush=True,
            )
            return False
        return True

    in_file_path = Path(in_path) / in_file
    records = list(SeqIO.parse(in_file_path, "fasta"))
    len_list = [(rec.description, len(rec.seq)) for rec in records]
    len_list.sort(key=lambda x: x[1], reverse=True)

    if len(len_list) > 100:
        a = len_list[99][1]
        b = a * 0.5

        file1 = Path(out_path) / f"long_{in_file}"
        file2 = Path(out_path) / f"add1_{in_file}"
        file3 = Path(out_path) / f"add2_{in_file}"

        with open(file1, "w") as fw1, open(file2, "w") as fw2, open(file3, "w") as fw3:
            long_count = 0
            for record in records:
                seq_len = len(record.seq)
                if seq_len >= a and long_count < 100:
                    SeqIO.write(record, fw1, "fasta")
                    long_count += 1
                elif seq_len > b:
                    SeqIO.write(record, fw3, "fasta")
                else:
                    SeqIO.write(record, fw2, "fasta")

        msa1 = Path(out_path) / f"step1_{in_file}"
        msa2 = Path(out_path) / f"step2_{in_file}"
        msa3 = Path(out_path) / f"step3_{in_file}"

        ok = _run_checked(f"{cmd_str[0]} --quiet {file1} > {msa1}", msa1)

        # 中间分组可能为空（如没有短于 a/2 的片段）。MAFFT 对空输入会
        # 静默产出空文件（RC=0），导致整个比对失败，因此分组为空时跳过对应步骤。
        if ok and file2.stat().st_size > 0:
            ok = _run_checked(
                f"{cmd_str[1]} --quiet --auto --addfragments {file2} {msa1} > {msa2}",
                msa2,
            )
            if not ok:  # 部分数据不适合 addfragments，改用 --add 重试
                ok = _run_checked(
                    f"{cmd_str[1]} --quiet --auto --add {file2} {msa1} > {msa2}", msa2
                )
            msa_base = msa2
        else:
            msa_base = msa1

        if ok and file3.stat().st_size > 0:
            ok = _run_checked(
                f"{cmd_str[2]} --quiet --auto --add {file3} {msa_base} > {msa3}", msa3
            )
            final_msa = msa3
        else:
            final_msa = msa_base

        file1.unlink(missing_ok=True)
        file2.unlink(missing_ok=True)
        file3.unlink(missing_ok=True)
        # 中间结果若本身就是最终结果（跳过 add 步骤时）则不能删除
        for f in (msa1, msa2):
            if f != final_msa:
                f.unlink(missing_ok=True)

        if final_msa.exists():
            shutil.move(str(final_msa), str(Path(out_path) / in_file))
        return ok
    else:
        out_file = Path(out_path) / in_file
        return _run_checked(f"{cmd_str[0]} --quiet {in_file_path} > {out_file}", out_file)


def mafft(
    in_path,
    out_path="",
    add_choice="",
    add_path="",
    algorithm="auto",
    thread=-1,
    reorder=True,
    additional_params="",
    pure_command_mode=False,
    pure_command="",
    progress_callback=None,
    message=True,
):
    """
    call mafft to do multiple sequence alignment
    ----------
    Parameters
    - in_path - the input file(s) and folder(s). could be a list or a string.
    - out_path - destination folder of output, where log files and result will be written.
    - add_choice - corresponding to mafft param [add, addfragments, addfull]
    - add_path - corresponding to mafft param new_sequences and in_path becomes aligned sequences
    - algorithm - corresponding to mafft param Algorithm,
        see manual https://mafft.cbrc.jp/alignment/software/manual/manual.html
    - thread - the number of threads, -1 if unsure
    - reorder - reorder the aligned sequences, False to keep input oreder
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
            run_command(command)
        return pure_command

    # STEP 1: check path validity and get file handles
    file_handles = get_file_handles(in_path)
    if not check_outpath_validity(out_path):
        return []
    if add_choice and not check_inpath_validity(
        add_path
    ):  # if add is True, then the following path should be valid
        return []

    # STEP 2: get parameters and call mafft
    mafft_exe = get_mafft_path()
    if message:
        print(f"Using MAFFT: {mafft_exe}")

    # for in_file in file_handles:
    #     basename = os.path.basename(in_file)
    #     out_file = os.path.join(out_path, basename)
    #     if add_choice:
    #         command = f"mafft --{algorithm} --{add_choice} {add_path} --thread {thread} {'--reorder' * reorder} {additional_params} {in_file} > {out_file}"
    #     else:
    #         command1 = f"mafft --{algorithm} --thread {thread} {'--reorder' * reorder} {additional_params} {in_file} > {out_file}"
    #     run_command(command)

    # multiple files in a directory
    if Path(in_path).is_dir():
        file_list = [f.name for f in Path(in_path).iterdir()]
    # one file
    else:
        file_list = [Path(in_path).name]
        in_path = str(Path(in_path).parent)
    file_list = [x for x in file_list if Path(x).suffix in [".fasta", ".fas", ".fa"]]
    if len(file_list) == 0:
        print("Could not find any fasta file in the input.")
        return [], None

    total_time = 0.0
    failed = False
    if add_choice:
        for file in file_list:
            t0 = datetime.now()
            in_file = str(Path(in_path) / file)
            final_out = str(Path(out_path) / file)
            # 输出与输入同路径时，cmd 的 ">" 会先截断输入文件，必须先写到临时文件
            out_file = (
                str(Path(out_path) / f".mafft_tmp_{file}")
                if _resolve_same_path(in_file, final_out)
                else final_out
            )
            command = f"{mafft_exe} --quiet --{algorithm} --{add_choice} {add_path} --thread {thread} {'--reorder' * reorder} {additional_params} {in_file} > {out_file}"
            if message:
                print(f"Aligning {file}...")
            if progress_callback:
                progress_callback(f"Aligning {file}...")
            r = run_command(command)
            if r.returncode != 0:
                failed = True
                if progress_callback:
                    progress_callback(
                        f"MAFFT command failed (RC={r.returncode}): {command}", "ERROR"
                    )
            if out_file != final_out and Path(out_file).exists():
                shutil.move(out_file, final_out)
            if not Path(final_out).exists() or Path(final_out).stat().st_size == 0:
                failed = True
                if progress_callback:
                    progress_callback(
                        f"MAFFT produced an empty output: {final_out}", "ERROR"
                    )
            t1 = datetime.now()
            elapsed = (t1 - t0).total_seconds()
            total_time += elapsed
            if message:
                print(f"MAFFT Used: {elapsed:.2f} seconds")
    elif algorithm.startswith("auto"):
        for file in file_list:
            t0 = datetime.now()
            in_file = str(Path(in_path) / file)
            final_out = str(Path(out_path) / file)
            # 输出与输入同路径时，cmd 的 ">" 会先截断输入文件，必须先写到临时文件
            out_file = (
                str(Path(out_path) / f".mafft_tmp_{file}")
                if _resolve_same_path(in_file, final_out)
                else final_out
            )
            command = f"{mafft_exe} --quiet --auto --thread {thread} {'--reorder' * reorder} {additional_params} {in_file} > {out_file}"
            if message:
                print(f"Aligning {file}...")
            if progress_callback:
                progress_callback(f"Aligning {file}...")
            r = run_command(command)
            if r.returncode != 0:
                failed = True
                if progress_callback:
                    progress_callback(
                        f"MAFFT command failed (RC={r.returncode}): {command}", "ERROR"
                    )
            if out_file != final_out and Path(out_file).exists():
                shutil.move(out_file, final_out)
            if not Path(final_out).exists() or Path(final_out).stat().st_size == 0:
                failed = True
                if progress_callback:
                    progress_callback(
                        f"MAFFT produced an empty output: {final_out}", "ERROR"
                    )
            t1 = datetime.now()
            elapsed = (t1 - t0).total_seconds()
            total_time += elapsed
            if message:
                print(f"MAFFT Used: {elapsed:.2f} seconds")
    else:
        command1 = f"{mafft_exe} --quiet --localpair --maxiterate 1000 --thread {thread} {'--reorder' * reorder} {additional_params}"
        command2 = f"{mafft_exe} --quiet --thread {thread} {'--reorder' * reorder} {additional_params}"
        command3 = f"{mafft_exe} --quiet --thread {thread} {'--reorder' * reorder} {additional_params}"
        cmd_str = [command1, command2, command3]

        for file in file_list:
            t0 = datetime.now()
            if not mafft_add(in_path, file, out_path, cmd_str):
                failed = True
            t1 = datetime.now()
            elapsed = (t1 - t0).total_seconds()
            total_time += elapsed
            print(f"MAFFT Used: {elapsed:.2f} seconds")

    # 任一命令失败即返回 None，避免上层误报 SUCCESS
    return file_handles, (None if failed else total_time)
