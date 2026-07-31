# -*- mode: python ; coding: utf-8 -*-

import warnings
from pathlib import Path

project_root = Path.cwd()
version_info_file = str(project_root / "version_info.txt")

warnings.filterwarnings('ignore', message='.*Matplotlib not present.*')

a = Analysis(
    [str(project_root / "src" / "Main_Fluent.py")],
    pathex=[str(project_root), str(project_root / "src")],
    binaries=[],
    datas=[
        (str(project_root / "src" / "icons"), "icons"),
        (str(project_root / "src" / "blast_parameters"), "blast_parameters"),
        (str(project_root / "src" / "initial_queries"), "initial_queries"),
    ],
    hiddenimports=[
        # PySide6
        'PySide6.QtCore',
        'PySide6.QtGui',
        'PySide6.QtWidgets',
        'qfluentwidgets',
        # Scientific computing
        'pandas',
        'numpy',
        'scipy',
        'mcl',
        # BioPython
        'Bio',
        'Bio.SeqIO',
        'Bio.Blast',
        # Other dependencies
        'func_timeout',
        # Project modules (src/)
        'main_utils',
        'blast_put_get',
        'blast_results_extend',
        'call_mafft2',
        'call_trimal',
        'combine_markers',
        'format_wizard',
        'functional',
        'hits_parse_join_select',
        'install_dependencies',
        'iterated_blast',
        'miner_filter',
        'my_entrez',
        'my_filter',
        'nt_calculator',
        'replacement',
        'select_new_queries',
        'seq_check_download',
        'sequence_indexer',
        # Chloroplast submodules
        'Chloroplast',
        'Chloroplast.PPA_80_CDS',
        'Chloroplast.TNRS',
        'Chloroplast.call_pga',
        'Chloroplast.download_gb_file',
        'Chloroplast.filter_seq',
        'Chloroplast.get_cds',
        'Chloroplast.pre_filter_gb_file',
        'Chloroplast.quality_ctrl',
        'Chloroplast.select_seq_by_acc',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        # GUI frameworks not used
        'tkinter',
        'matplotlib',
        # Dev/test tools
        'IPython',
        'jupyter',
        'notebook',
        'pytest',
        'test',
        'tests',
        'setuptools',
        'pip',
        'unittest',
        'doctest',
        'pdb',
        'lib2to3',
        'pydoc',
        # PIL (dev-only)
        'PIL',
        'PIL.Image',
        'PIL._tkinter_finder',
        # Test submodules
        'pandas.tests',
        'numpy.tests',
        'numpy.f2py',
        'scipy.tests',
        'Bio.tests',
    ],
    noarchive=True,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='PyNCBIminer-NG',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=str(project_root / "src" / "icons" / "app_icon.ico"),
    version=version_info_file,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='PyNCBIminer-NG',
)
