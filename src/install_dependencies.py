# -*- coding: utf-8 -*-
# @Time:2024/2/2 14:15
# @Author:Ruijing Cheng
# @File:install_dependencies.py
# @Software:PyCharm

from pathlib import Path
import zipfile
from urllib.request import urlretrieve


def schedule(blocknum, blocksize, totalsize):
    if totalsize == 0:
        print(f"Downloaded: {blocknum * blocksize / 1024 / 1024:.2f} MB", end="\r")
        return
    per = 100.0 * blocknum * blocksize / totalsize
    if per > 100:
        per = 100
    if per % 10 < (100.0 * blocksize / totalsize):
        print("%.2f%%" % per, end=" ")


def _log_callback(message, level="INFO"):
    print(message)


def install_mafft(log_callback=None):
    """
    download mafft to the same directory as pyncbiminer and extract the zip file
    https://mafft.cbrc.jp/alignment/software/mafft-7.526-win64-signed.zip
    path to trimal after extraction: ./mafft/mafft-win
    :param log_callback: optional callback function for logging
    :return:
    """
    log = log_callback if log_callback else _log_callback
    
    mafft_url = r"https://mafft.cbrc.jp/alignment/software/mafft-7.526-win64-signed.zip"
    root_path = Path.cwd()
    mafft_dir = root_path / r"./mafft"
    
    if mafft_dir.exists() and any(mafft_dir.iterdir()):
        log("MAFFT already installed, skipping...")
        return
    
    if not mafft_dir.exists():
        mafft_dir.mkdir(exist_ok=True)
    file_path = mafft_dir / r"mafft-7.526-win64-signed.zip"
    log("Downloading MAFFT...")
    file_path, _ = urlretrieve(mafft_url, file_path, schedule)
    log("Extracting files...")
    with zipfile.ZipFile(file_path, "r") as zip:
        zip.extractall(mafft_dir)
    log("Installation finished.")
    file_path.unlink()
    log("Zip file deleted.")


def install_trimal(log_callback=None):
    """
    download trimal to the same directory as pyncbiminer and extract the zip file
    https://gh-proxy.org/https://github.com/inab/trimal/releases/download/v1.5.0/trimAl_Windows_x86-64.zip
    path to trimal after extraction: ./trimal/trimAl/bin
    :param log_callback: optional callback function for logging
    :return:
    """
    log = log_callback if log_callback else _log_callback
    
    trimal_url = r"https://gh-proxy.org/https://github.com/inab/trimal/releases/download/v1.5.0/trimAl_Windows_x86-64.zip"
    root_path = Path.cwd()
    trimal_dir = root_path / r"./trimal"
    
    if trimal_dir.exists() and any(trimal_dir.iterdir()):
        log("trimAl already installed, skipping...")
        return
    
    if not trimal_dir.exists():
        trimal_dir.mkdir(exist_ok=True)
    file_path = trimal_dir / r"trimAl_Windows_x86-64.zip"
    log("Downloading trimAl...")
    file_path, _ = urlretrieve(trimal_url, file_path, schedule)

    log("Extracting files...")
    with zipfile.ZipFile(file_path, "r") as zip:
        zip.extractall(trimal_dir)
    log("Installation finished.")
    file_path.unlink()
    log("Zip file deleted.")


def install_pga(pga_url=r"https://gh-proxy.org/https://github.com/wyx619/PGA-NG/releases/download/release/PGA-NG.zip", log_callback=None):
    """
    download pga to the same directory as pyncbiminer and extract the zip file
    path to pga after extraction: ./PGA-NG
    :param pga_url: URL to download the pga zip file
    :param log_callback: optional callback function for logging
    :return:
    """
    log = log_callback if log_callback else _log_callback
    
    root_path = Path.cwd()
    pga_dir = root_path / r"./PGA-NG"
    
    if pga_dir.exists() and any(pga_dir.iterdir()):
        log("PGA-NG already installed, skipping...")
        return
    
    if not pga_dir.exists():
        pga_dir.mkdir(exist_ok=True)
    file_path = pga_dir / r"PGA-NG.zip"
    log("Downloading PGA-NG...")
    file_path, _ = urlretrieve(pga_url, file_path, schedule)

    log("Extracting files...")
    with zipfile.ZipFile(file_path, "r") as zip:
        zip.extractall(pga_dir)
    log("Installation finished.")
    file_path.unlink()
    log("Zip file deleted.")
