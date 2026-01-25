# -*- coding: utf-8 -*-
# @Time:2024/2/2 14:15
# @Author:Ruijing Cheng
# @File:install_dependencies.py
# @Software:PyCharm

from pathlib import Path
import zipfile
from urllib.request import urlretrieve


def schedule(blocknum, blocksize, totalsize):
    per = 100.0 * blocknum * blocksize / totalsize
    if per > 100:
        per = 100
    if per % 10 < (100.0 * blocksize / totalsize):
        print("%.2f%%" % per, end=" ")


def install_mafft():
    """
    download mafft to the same directory as pyncbiminer and extract the zip file
    https://mafft.cbrc.jp/alignment/software/mafft-7.526-win64-signed.zip
    path to trimal after extraction: ./mafft/mafft-win
    :return:
    """
    # todo: this url needs to be updated or dynamically maintained.
    mafft_url = r"https://mafft.cbrc.jp/alignment/software/mafft-7.526-win64-signed.zip"
    root_path = Path.cwd()
    mafft_dir = root_path / r"./mafft"
    if not mafft_dir.exists():
        mafft_dir.mkdir(exist_ok=True)
    file_path = mafft_dir / r"mafft-7.526-win64-signed.zip"
    print("Downloading MAFFT...")
    file_path, _ = urlretrieve(mafft_url, file_path, schedule)
    print("Extracting files...")
    with zipfile.ZipFile(file_path, "r") as zip:
        zip.extractall(mafft_dir)
    print("Installation finished.")
    file_path.unlink()  # Delete zip file
    print("Zip file deleted.")


def install_trimal():
    """
    download trimal to the same directory as pyncbiminer and extract the zip file
    https://gh-proxy.org/https://github.com/inab/trimal/releases/download/v1.5.0/trimAl_Windows_x86-64.zip
    path to trimal after extraction: ./trimal/trimAl/bin
    :return:
    """
    # todo: this url needs to be updated or dynamically maintained.
    trimal_url = r"https://gh-proxy.org/https://github.com/inab/trimal/releases/download/v1.5.0/trimAl_Windows_x86-64.zip"
    root_path = Path.cwd()
    trimal_dir = root_path / r"./trimal"
    if not trimal_dir.exists():
        trimal_dir.mkdir(exist_ok=True)
    file_path = trimal_dir / r"trimAl_Windows_x86-64.zip"
    print("Downloading trimAl...")
    file_path, _ = urlretrieve(trimal_url, file_path, schedule)

    print("Extracting files...")
    with zipfile.ZipFile(file_path, "r") as zip:
        zip.extractall(trimal_dir)
    print("Installation finished.")
    file_path.unlink()  # Delete zip file
    print("Zip file deleted.")


def install_pga(pga_url, exe_name="pga.exe"):
    """
    download pga executable to the same directory as pyncbiminer
    path to pga after download: ./pga/pga.exe
    :param pga_url: URL to download the pga exe file
    :param exe_name: Name of the executable file (default: pga.exe)
    :return:
    """
    root_path = Path.cwd()
    pga_dir = root_path / r"./pga"
    if not pga_dir.exists():
        pga_dir.mkdir(exist_ok=True)
    file_path = pga_dir / exe_name
    print("Downloading PGA...")
    file_path, _ = urlretrieve(pga_url, file_path, schedule)
    print("PGA downloaded successfully.")
    print(f"PGA installed at: {file_path}")
