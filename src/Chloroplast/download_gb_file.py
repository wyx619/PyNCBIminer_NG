# *-* coding:utf-8 *-*
# @Time:2022/1/5 10:02
# @Author:Ruijing Cheng
# @File:download_gb_file.py
# @Software:PyCharm



from pathlib import Path

from concurrent.futures import ThreadPoolExecutor, as_completed
from Bio import Entrez, SeqIO
import func_timeout
from func_timeout import func_set_timeout
import time
from threading import Lock
import pandas as pd

@func_set_timeout(600)
def download_single(email, accession, out_path, request_lock, last_request_time):
    """下载单个基因组文件（带速率控制）"""
    with request_lock:
        elapsed = time.time() - last_request_time[0]
        if elapsed < 0.34:
            time.sleep(0.34 - elapsed)
        last_request_time[0] = time.time()
    
    Entrez.email = email
    
    with Entrez.efetch(db="nucleotide", rettype="gb", id=accession) as handle:
        record = SeqIO.read(handle, "gb")
    
    accession_clean = record.id.split(".")[0]
    out_file = Path(out_path) / f"{accession_clean}.gb"
    with open(out_file, "w") as f:
        SeqIO.write(record, f, "gb")
    
    return accession_clean


def download_gb_file(email, in_path, out_path, max_threads=10, batch_size=None):
    """批量下载基因组文件
    
    Args:
        email: NCBI联系邮箱
        in_path: accession列表文件路径
        out_path: 输出目录路径
        max_threads: 最大线程数
        batch_size: 批大小（此版本不再使用，兼容旧接口）
    """
    in_path = Path(in_path)
    out_path = Path(out_path)

    with open(in_path, "r") as fr:
        accession_list = fr.read().splitlines()

    out_path.mkdir(parents=True, exist_ok=True)
    error_file = out_path / "error_downloaded_index.csv"

    if error_file.exists() and error_file.stat().st_size > 0:
        error_df = pd.read_csv(error_file, header=None)
        existing_files = {p.stem for p in out_path.glob("*.gb")} | set(error_df.iloc[:, 0].astype(str))
    else:
        existing_files = {p.stem for p in out_path.glob("*.gb")}
    to_download = []
    skipped = []
    for acc in accession_list:
        acc_clean = acc.split(".")[0]
        if acc and acc_clean not in existing_files:
            to_download.append(acc)
        else:
            skipped.append(acc_clean)

    print(f"Total accessions: {len(accession_list)}")
    print(f"Already downloaded: {len(skipped)}")
    print(f"To download: {len(to_download)}")

    request_lock = Lock()
    last_request_time = [time.time()]

    success, failed = 0, 0

    def attempt_download(acc, retries=3):
        """Download attempt with retry"""
        for attempt in range(retries):
            try:
                return download_single(email, acc, out_path, request_lock, last_request_time), True, None
            except func_timeout.exceptions.FunctionTimedOut:
                if attempt < retries - 1:
                    sleep_time = 2 ** attempt
                    print(f"[Retry {attempt + 1}/{retries - 1}] {acc}: Timeout, waiting {sleep_time}s...")
                    time.sleep(sleep_time)
                    continue
                return acc, False, "Timeout"
            except Exception as e:
                error_msg = str(e)
                if "429" in error_msg and attempt < retries - 1:
                    sleep_time = 5 * (attempt + 1)
                    print(f"[Retry {attempt + 1}/{retries - 1}] {acc}: 429 Rate limit, waiting {sleep_time}s...")
                    time.sleep(sleep_time)
                    continue
                if attempt < retries - 1:
                    sleep_time = min(60, 2 ** attempt)
                    print(f"[Retry {attempt + 1}/{retries - 1}] {acc}: {error_msg[:50]}, waiting {sleep_time}s...")
                    time.sleep(sleep_time)
                    continue
                return acc, False, error_msg[:100]
        return acc, False, "Unknown"

    with ThreadPoolExecutor(max_workers=max_threads) as executor:
        futures = {
            executor.submit(attempt_download, acc): acc 
            for acc in to_download
        }
        
        for future in as_completed(futures):
            acc = futures[future]
            try:
                result, ok, error = future.result()
                if ok:
                    success += 1
                    print(f"[OK] {result}")
                else:
                    failed += 1
                    print(f"[FAILED] {acc}: {error}")
            except Exception as e:
                failed += 1
                print(f"[ERROR] {acc}: {str(e)[:100]}")

    print(f"All downloads completed. Success: {success}, Failed: {failed}")

    
    file_sizes = [f.stat().st_size for f in out_path.glob("*.gb")]
    print(f"Total downloaded: {len(file_sizes)}")
    if not file_sizes:
        print("No .gb files found in out_path!")
        return len(accession_list), len(skipped), len(to_download), success, failed

    small_files = [f for f in out_path.glob("*.gb")]

    error_files = []
    for f in small_files:
        with open(f, "r") as fr:
            lines = fr.readlines()
        for i, line in enumerate(lines):
            if line.startswith("ORIGIN"):
                if i + 1 < len(lines) and lines[i + 1].strip():
                    break
        else:
            error_files.append((f, f.stat().st_size))
            f.unlink()
    if error_files:
        with open(out_path / "error_downloaded_index.csv", "w") as fw:
            for f, size in error_files:
                fw.write(f"{f.stem},{size / 1024:.2f}\n")
                print(f"Deleted {f.name} without ORIGIN section")
        print(f"Quality check completed! Deleted {len(error_files)} invalid files.")
    else:
        print("Quality check completed! All files are valid.")



    return len(accession_list), len(skipped), len(to_download), success, failed
