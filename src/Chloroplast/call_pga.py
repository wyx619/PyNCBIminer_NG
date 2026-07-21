# *-* coding:utf-8 *-*
import shutil
import threading
import time
from pathlib import Path

from functional import run_command


def run_pga(in_folder, ori_gb_folder, clade, ref_folder=None, emit_log=None):
    if emit_log is None:
        def emit_log(msg, level=None):
            return print(msg)

    in_folder = Path(in_folder)
    ori_gb_folder = Path(ori_gb_folder)

    root_path = Path.cwd()
    pga_dir = root_path / r"./PGA-NG"

    temp_folder = in_folder / "pga_temp"
    temp_out = temp_folder / "output"
    out_folder = in_folder / "pga_output"

    if temp_folder.exists():
        if temp_out.exists():
            existing_gb = list(temp_out.glob("*.gb"))
            if existing_gb:
                emit_log(f"Found {len(existing_gb)} files from previous run in temp folder", "INFO")
                if not out_folder.exists():
                    out_folder.mkdir(parents=True, exist_ok=True)
                recovered_count = 0
                for f in existing_gb:
                    dest_file = out_folder / f.name
                    if not dest_file.exists():
                        shutil.copy2(f, dest_file)
                        recovered_count += 1
                        emit_log(f"Recovered: {f.name}")
                if recovered_count > 0:
                    emit_log(f"Recovered {recovered_count} files", "INFO")
        emit_log("Cleaning up previous temp folder...", "INFO")
        shutil.rmtree(temp_folder, ignore_errors=True)

    if not _check_pga_installed(pga_dir, emit_log):
        return

    if not _check_input_folder(in_folder, emit_log):
        return

    pending_info = _get_pending_genomes(in_folder, ori_gb_folder, emit_log)
    if pending_info is None:
        return

    fasta_files, pending_stems, num_pending, num_total = pending_info

    if num_pending == 0:
        emit_log("All genomes have been annotated. Skipping annotation...", "SUCCESS")
        return

    emit_log(
        f"{num_pending}/{num_total} genomes will be reannotated using {clade} reference genomes",
        "INFO",
    )

    ref_folder = _get_ref_folder(pga_dir, clade, ref_folder, emit_log)
    if ref_folder is None:
        return

    pga_main = Path(pga_dir / "PGA-NG.exe")
    out_folder = in_folder / "pga_output"
    out_folder.mkdir(exist_ok=True)

    temp_out = _prepare_temp_folders(in_folder, fasta_files, pending_stems, emit_log)
    pga_command = f"{pga_main} -r {ref_folder} -t {temp_folder} -o {temp_out}"

    done_flag = [False]

    def monitor_thread():
        processed_stems = set()
        while not done_flag[0]:
            current_gb_files = list(temp_out.glob("*.gb"))
            current_stems = {f.stem.replace("_reannoated", "") for f in current_gb_files}
            completed_stems = current_stems & pending_stems
            new_stems = completed_stems - processed_stems
            if new_stems:
                for stem in new_stems:
                    emit_log(
                        f"Fixed: {len(completed_stems)}/{num_pending} - {stem}",
                        "INFO",
                    )
                processed_stems = completed_stems
            time.sleep(3)
        final_gb = list(temp_out.glob("*.gb"))
        final_stems = {f.stem.replace("_reannoated", "") for f in final_gb}
        completed_stems = final_stems & pending_stems
        for stem in completed_stems:
            if stem not in processed_stems:
                emit_log(
                    f"Progressed: {len(completed_stems)}/{num_pending} - {stem}",
                    "SUCCESS",
                )

    def run_pga_thread():
        result = run_command(pga_command)
        done_flag[0] = True

        if result.returncode != 0:
            emit_log(f"Annotation failed with code {result.returncode}", "ERROR")
            shutil.rmtree(temp_folder, ignore_errors=True)
            return

        for f in temp_folder.glob("*.njs"):
            f.unlink(missing_ok=True)

        for f in temp_out.glob("*.gb"):
            shutil.copy2(f, out_folder / f.name)

        if not Path(ori_gb_folder).exists():
            emit_log(f"Original GenBank folder does not exist: {ori_gb_folder}", "ERROR")
            shutil.rmtree(temp_folder, ignore_errors=True)
            return

        _fix_annotated_files(ori_gb_folder, out_folder, temp_folder, num_pending, emit_log)

    thread1 = threading.Thread(target=monitor_thread)
    thread1.daemon = True
    thread1.start()

    thread2 = threading.Thread(target=run_pga_thread)
    thread2.daemon = True
    thread2.start()


def _check_pga_installed(pga_dir, emit_log):
    if not pga_dir.exists():
        emit_log(
            "PGA directory not found. Please go to Settings Page to install PGA first.", "WARNING"
        )
        return False
    return True


def _check_input_folder(in_folder, emit_log):
    if not in_folder.exists() or not any(in_folder.iterdir()):
        emit_log("Input genome not found.", "WARNING")
        return False
    return True


def _get_pending_genomes(in_folder, ori_gb_folder, emit_log):
    out_folder = in_folder / "pga_output"
    annotated_stems = set()
    if out_folder.exists():
        gb_files = list(out_folder.glob("*.gb"))
        annotated_stems = {f.stem.replace("_reannoated", "") for f in gb_files}
        if annotated_stems:
            emit_log(f"Found {len(annotated_stems)} already annotated genomes", "INFO")

    if ori_gb_folder.exists():
        old_files = {f.stem for f in ori_gb_folder.glob("*.gb.old")}
        if old_files:
            already_fixed = len(old_files)
            emit_log(f"Found {already_fixed} already fixed genomes in original folder", "INFO")
            annotated_stems = annotated_stems | old_files

    fasta_files = [
        f for f in in_folder.iterdir() if f.suffix.lower() in {".fasta", ".fa"}
    ]
    if not fasta_files:
        emit_log("No FASTA files found in input folder.", "WARNING")
        return None

    fasta_stems_raw = {f.stem for f in fasta_files}
    fasta_stems = {s.replace("_reannoated", "") for s in fasta_stems_raw}
    annotated_stems_clean = {s.replace("_reannoated", "") for s in annotated_stems}
    pending_stems = fasta_stems - annotated_stems_clean
    pending_files = [f for f in fasta_files if f.stem.replace("_reannoated", "") in pending_stems]

    return pending_files, pending_stems, len(pending_stems), len(fasta_stems)


def _get_ref_folder(pga_dir, clade, ref_folder, emit_log):
    if clade == "Angiosperms":
        ref_folder = Path(pga_dir / "Reference" / "Angiosperms")
    elif clade == "Gymnosperms":
        ref_folder = Path(pga_dir / "Reference" / "Gymnosperms")
    elif clade == "User defined":
        ref_folder = Path(ref_folder)

    if not ref_folder.exists() or not any(ref_folder.iterdir()):
        emit_log("Reference genome not found.", "WARNING")
        return None
    return ref_folder


def _prepare_temp_folders(in_folder, fasta_files, pending_stems, emit_log):
    temp_folder = in_folder / "pga_temp"
    temp_out = temp_folder / "output"
    temp_folder.mkdir(exist_ok=True)

    pending_files = [f for f in fasta_files if f.stem.replace("_reannoated", "") in pending_stems]
    for f in pending_files:
        shutil.copy2(f, temp_folder / f.name)
    temp_out.mkdir(exist_ok=True)

    return temp_out


def _fix_annotated_files(ori_gb_folder, out_folder, temp_folder, num_pending, emit_log):
    def fix_thread():
        annotated_files = list(out_folder.glob("*_reannoated.gb"))

        fixed_stems = {f.stem for f in ori_gb_folder.glob("*.gb.old")}
        annotated_files = [f for f in annotated_files if f.stem.replace("_reannoated", "") not in fixed_stems]

        total = len(annotated_files)
        if total == 0:
            emit_log("All genomes already fixed, skipping...", "INFO")
            shutil.rmtree(temp_folder, ignore_errors=True)
            emit_log(f"Annotation completed. {num_pending} genomes reannotated.", "SUCCESS")
            return

        for i, annotated_file in enumerate(annotated_files):
            original_file = ori_gb_folder / annotated_file.name.replace("_reannoated", "")
            fix_annotated_genbank(original_file, annotated_file, emit_log)
            if (i + 1) % 100 == 0 or (i + 1) == total:
                emit_log(f"Fixed: {i+1}/{total} - {original_file.name.replace(".gb", "")}", "INFO")

        shutil.rmtree(temp_folder, ignore_errors=True)
        emit_log(f"Annotation completed. {num_pending} genomes reannotated.", "SUCCESS")

    fix_thread = threading.Thread(target=fix_thread)
    fix_thread.daemon = True
    fix_thread.start()


def fix_annotated_genbank(original_file, annotated_file, emit_log=None):
    import re
    from pathlib import Path

    if emit_log is None:
        def emit_log(msg, level=None):
            return print(msg)

    original_file = Path(original_file)
    annotated_file = Path(annotated_file)

    if not original_file.exists():
        emit_log(f"Original file not found, skipping: {original_file.name}", "WARNING")
        return False

    try:
        with open(original_file, "r", encoding="utf-8") as f1:
            original_lines = f1.readlines()
        with open(annotated_file, "r", encoding="utf-8") as f2:
            annotated_lines = f2.readlines()

        original_first = original_lines[0]
        annotated_first = annotated_lines[0]

        original_parts = original_first.split()
        annotated_parts = annotated_first.split()

        spaces = re.findall(r'[ \t]+', original_first)

        new_parts = [
            original_parts[0],
            original_parts[1],
            original_parts[2],
            original_parts[3],
            annotated_parts[4],
            annotated_parts[5],
            annotated_parts[6],
            annotated_parts[7],
        ]

        new_first_line = new_parts[0]
        for i, space in enumerate(spaces):
            if i == 5:
                if new_parts[i] == 'circular' and original_parts[i] == 'linear':
                    space = space[:-2] if len(space) >= 2 else space
                elif new_parts[i] == 'linear' and original_parts[i] == 'circular':
                    space = space + "  "
            new_first_line += space + new_parts[i + 1]

        features_index = None
        for i, line in enumerate(original_lines):
            if line.startswith("FEATURES"):
                features_index = i
                break

        new_lines = [new_first_line + "\n"]
        new_lines.extend(original_lines[1:features_index])
        new_lines.extend(annotated_lines[1:])

        old_file = original_file.with_suffix(".gb.old")
        original_file.rename(old_file)

        with open(original_file, "w", encoding="utf-8") as f:
            f.writelines(new_lines)

        #emit_log(f"Fixed: {original_file.name} (backed up to {old_file.name})", "INFO")
        return True
    except Exception as e:
        emit_log(f"Error processing {annotated_file.name}: {str(e)}", "WARNING")
        return False
