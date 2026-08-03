from pathlib import Path
import time
import subprocess
import sys

def check_inpath_validity(path):
    """check if an input path is valid (an existing path except shortcuts and .result files)
    ----------
    Parameters
    - path - the path whose validity is to be checked
    -------
    Returns
    True if path is valid
    False if path is NOT valid"""
    if not isinstance(path, str):  # invalid input: value type
        return False
    if path.endswith(".lnk"):
        return False  # do nothing with shortcut files
    if not Path(path).exists():  # invalid input: no such path
        return False
    return True


def check_outpath_validity(path):
    """check if an output path is valid (an existing folder except shortcuts)
    ----------
    Parameters
    - path - the path whose validity is to be checked
    -------
    Returns
    True if path is valid
    False if path is NOT valid"""
    if not isinstance(path, str):
        return False
    if path.endswith(".lnk"):
        return False  # do nothing with shortcut files
    path_obj = Path(path)
    if not path_obj.exists():  # invalid input: no such path
        return False
    if not path_obj.is_dir():
        return False  # must be an existing folder
    return True


def create_folder(path):
    """create a new folder if one with the same name hasn't been created.
    ----------
    Parameters
    - path - the path of the folder to be created
    -------
    Returns
    - path - if folder is created
    0 - if not
    -1 if illegal characters are in the path"""
    try:
        path_obj = Path(path)
        if not path_obj.exists():
            path_obj.mkdir()
            return path
        else:
            return 0
    except Exception:
        return -1


def get_file_handles(in_path):
    """in_path could be a file/folder, a list of files/folders or a list of both
    Therefore, there is need to consider each condition and get all file handles
    ----------
    Parameters
    - in_path - the input file(s) and folder(s). could be a list or a string.
    -------
    Returns
    - file_handles - all file handles in a list"""
    # STEP 1: if in_path is not a list, then make it a list
    if not isinstance(in_path, list):
        in_path = [in_path]

    # STEP 2: for all elements in the given list, decide whether it's a file or a folder:
    abs_handles = {}  # in case duplicates but in different forms like abs/relative
    file_handles = []  # result, returned value
    for file_path in in_path:
        # if path is invalid, collect warning message
        if not check_inpath_validity(file_path):
            warning_message = f"{file_path} invalid, thus omitted."
            print(f"NOTE: {warning_message}")
            continue

        # substep 1 : if an element is a file, add the file to result
        file_path_obj = Path(file_path)
        if file_path_obj.is_file():
            file_handles.append(file_path)

        # substep 2 : if an element is a folder, get files directly in the folder
        else:  # is a folder
            file_handles += [
                str(file_path_obj / file)
                for file in file_path_obj.iterdir()
                if ((file_path_obj / file).is_file() and not file.endswith(".lnk"))
            ]  # exclude shortcut

    # STEP 3: replace reverse slash, remove duplicates and sort
    file_handles = list(map(lambda x: x.replace("\\", "/"), file_handles))
    for handle in file_handles:
        abs_handles.setdefault(str(Path(handle).absolute()), [])
        abs_handles[str(Path(handle).absolute())].append(handle)
    file_handles = []
    for handle_list in abs_handles.values():
        min_len = min(list(map(lambda x: len(x), handle_list)))
        for handle in handle_list:
            if len(handle) == min_len:
                file_handles.append(handle)
                break
    # if there are paths omitted, collect warning message
    if len(abs_handles.values()) != len(file_handles):
        warning_message = (
            "Redundant input files detected, duplicates automatically removed"
        )
        print(f"NOTE: {warning_message}")

    # if there are no paths kept, show error message, else show warning message
    if len(file_handles) == 0:
        error_message = "All input file(s) invalid, please check your input!"
        print(f"ERROR: {error_message}")
    else:
        pass

    file_handles.sort()

    return file_handles


def overwriting_potential(in_path, out_path):
    """check whether there is potential danger that original file may be overwritten
        happens when out_path is in one of the folders of in_path,
        or out_path is one of the parent folders of files in in_path
    ----------
    Parameters
    - in_path - the input file(s) and folder(s). could be a list or a string.
    - out_path - destination folder of output, where log files and result will be written.
    -------
    Returns
    - overwriting_potential - True if there is potential danger of overwriting original file
    """
    # transform in_path into list object if needed
    if not isinstance(in_path, list):
        in_path = [in_path]

    # get absolutely path for each path in in_path
    in_path = list(map(lambda path: str(Path(path).absolute()), in_path))

    # replace files in in_path with parent folder for each file in in_path
    # and keep folders in_path
    in_path = [path for path in in_path if Path(path).is_dir()] + [
        str(Path(path).parent) for path in in_path if Path(path).is_file()
    ]

    # check if overwriting is possible
    overwriting_potential = False
    out_path = str(Path(out_path).absolute())
    if out_path in in_path:
        overwriting_potential = True

    return overwriting_potential


def get_checked_path(in_path, out_path, overwriting_check=True):
    """do following checks:
            1. check the validity of in_path
            2. get valid inpath(s)
            3. check the validity of out_path
            4. check overwriting potential
    ----------
    Parameters
    - in_path - the input file(s) and folder(s). could be a list or a string.
    - out_path - destination folder of output, where log files and result will be written.
    - overwriting_check - if there is need to check overwriting potential
        Default: True
    -------
    Returns
    - file_handles - all file handles in a list (directly from <func> get_file_handles)
    """
    # get all file handles, inside which input path validity is checked
    file_handles = get_file_handles(in_path)
    if file_handles == []:
        return []

    # check if output path is valid
    if not check_outpath_validity(out_path):
        error_message = "Output path invalid, please check your outout path!"
        print(f"ERROR: {error_message}")
        print("Operation aborted")
        return []

    # check if there is potential danger of overwriting original files
    if overwriting_check:
        if overwriting_potential(in_path, out_path):
            error_message = "Overwriting danger! Please set another output path."
            print(f"ERROR: {error_message}")
            print("Operation aborted")
            return []

    return file_handles


def get_fasta(file_handles):
    """filter file_handles and keep only those ends with fa, fas or fasta
    ----------
    Parameters
    - file_handles - the input file(s) and folder(s). could be a list or a string.
    -------
    Returns
    """
    fasta_files = [
        in_path
        for in_path in file_handles
        if in_path.endswith(".fasta")
        or in_path.endswith(".fas")
        or in_path.endswith(".fa")
    ]

    return fasta_files


def timer(f):
    def inner(*args, **kwargs):
        start = time.time()
        ret = f(*args, **kwargs)
        end = time.time()
        print(f"time taken: {end - start} seconds")
        return ret

    return inner


class Timer:
    def __init__(self, out_path):
        self.out_path = out_path
        self.time_checkpoint = time.time()

    def record(self, msg):
        time_current = time.time()
        time_consumed = round(time_current - self.time_checkpoint, 2)
        self.time_checkpoint = time_current
        with open(self.out_path, "a") as f:
            msg = f"{msg}: {time_consumed} seconds\n"
            f.write(msg)

def run_command(command, shell=True, capture_output=False):
    """
    执行命令并隐藏命令行窗口（适用于 Windows）

    Args:
        command: 要执行的命令字符串
        shell: 是否使用 shell 执行（默认为 True）
        capture_output: 是否捕获输出（会影响 shell 重定向）

    Returns:
        subprocess.CompletedProcess 对象
    """
    if sys.platform == "win32":
        startupinfo = subprocess.STARTUPINFO()
        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        startupinfo.dwFlags |= subprocess.STARTF_USESTDHANDLES
        startupinfo.wShowWindow = subprocess.SW_HIDE
        creationflags = subprocess.CREATE_NO_WINDOW

        stdout_setting = subprocess.PIPE if capture_output else None
        stderr_setting = subprocess.PIPE if capture_output else None

        process = subprocess.Popen(
            command,
            shell=shell,
            startupinfo=startupinfo,
            creationflags=creationflags,
            stdout=stdout_setting,
            stderr=stderr_setting,
            stdin=subprocess.DEVNULL,
        )
        stdout, stderr = process.communicate()

        if stderr:
            print(f"{stderr.decode('utf-8', errors='ignore')}")

        return subprocess.CompletedProcess(
            args=command, returncode=process.returncode, stdout=stdout, stderr=stderr
        )
    else:
        capture = subprocess.PIPE if capture_output else False
        return subprocess.run(command, shell=shell, capture_output=capture, text=False)


def my_concatenation(in_path, out_path, emit_log):
    from datetime import datetime
    from pathlib import Path
    from format_wizard import taxon_completion, concat, fas2phy

    t0 = datetime.now()
    out_path_obj = Path(out_path)
    if not out_path_obj.exists():
        out_path_obj.mkdir(exist_ok=True)
    file_list = [
        file.name
        for file in Path(in_path).iterdir()
        if file.suffix in [".fasta", ".fas", ".fa"]
    ]
    for file in file_list:
        fr = open(Path(in_path) / file, "r")
        records = fr.read().replace(" ", "")
        fr.close()
        fw = open(Path(in_path) / file, "w")
        fw.write(records)
        fw.close()
    missing = taxon_completion(in_path=in_path, out_path=out_path)
    if missing:
        emit_log(f"Completion log written to {out_path}/completion/completion.log")
    else:
        emit_log("Warning: no taxa were completed (input may be empty)", "WARNING")

    marker_record = concat(
        in_path=str(Path(out_path) / "completion"), out_path=out_path
    )
    if marker_record:
        emit_log(
            f"Concatenated file written to {out_path}/concat/concat.fasta"
        )
        emit_log(f"Config file written to {out_path}/concat/concat.cfg")
        emit_log(f"Part file written to {out_path}/concat/part.txt")
    else:
        emit_log(
            "Concatenation failed: check that all input files have identical"
            " taxon sets and equal sequence lengths within each file",
            "ERROR",
        )
        t1 = datetime.now()
        emit_log(f"Running time: {t1 - t0} seconds")
        return

    written = fas2phy(
        in_path=str(Path(out_path) / "concat" / "concat.fasta"), out_path=out_path
    )
    if written:
        emit_log(f"Phylip file written to {out_path}/phylip/concat.phy")
    else:
        emit_log("Phylip conversion produced no output", "WARNING")

    t1 = datetime.now()
    emit_log(f"Running time: {t1 - t0} seconds")
    emit_log("Concatenation completed successfully!", "SUCCESS")
