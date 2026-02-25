# -*- mode: python ; coding: utf-8 -*-

import sys
import os
from pathlib import Path

# 获取项目根目录（使用当前工作目录）
project_root = Path.cwd()

# 版本信息文件
version_info_file = str(project_root / "version_info.txt")

# 分析主程序
a = Analysis(
    [str(project_root / "src" / "Main_Fluent.py")],
    pathex=[str(project_root)],
    binaries=[],
    datas=[
        # 包含图标（图标在 src/icons 目录下）
        (str(project_root / "src" / "icons"), "icons"),
        # 包含BLAST参数文件（blast_parameters 在 src 目录下）
        (str(project_root / "src" / "blast_parameters"), "blast_parameters"),
        # 包含初始查询序列（initial_queries 在 src 目录下）
        (str(project_root / "src" / "initial_queries"), "initial_queries"),
    ],
    hiddenimports=[
        # PySide6相关
        'PySide6.QtCore',
        'PySide6.QtGui',
        'PySide6.QtWidgets',
        # 科学计算库
        'pandas',
        'numpy',
        'scipy',
        'scikit-learn',
        'markov_clustering',
        'networkx',
        # BioPython
        'Bio',
        'Bio.SeqIO',
        'Bio.Blast',
        'qfluentwidgets',
        # 其他依赖
        'func_timeout',
        # 动态导入的模块
        'src.main_utils',
        'src.aligner',
        'src.blast_put_get',
        'src.blast_results_extend',
        'src.call_mafft2',
        'src.call_trimal',
        'src.format_wizard',
        'src.functional',
        'src.hits_parse_join_select',
        'src.install_dependencies',
        'src.iterated_blast',
        'src.miner_filter',
        'src.my_entrez',
        'src.my_filter',
        'src.nt_calculator',
        'src.select_new_queries',
        'src.seq_check_download',
        'src.sequence_indexer'
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        # 排除不需要的模块以减小体积
        'tkinter',
        'matplotlib',
        'IPython',
        'jupyter',
        'notebook',
        'pytest',
        'test',
        'tests',
        'setuptools',
        'pip',
        'PIL',
        'PIL.Image',
        'PIL._tkinter_finder',
        # 排除测试模块
        'pandas.tests',
        'numpy.tests',
        'scipy.tests',
        'scikit-learn.tests',
        'networkx.tests',
        'Bio.tests',
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=None,
    noarchive=True,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='PyNCBIminer-NG',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=str(project_root / "src" / "icons" / "app_icon.ico"),
    version=version_info_file,
)
