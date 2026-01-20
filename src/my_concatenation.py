# *-* coding:utf-8 *-*
# @Time:2024/2/2 14:36
# @Author:Ruijing Cheng
# @File:my_concatenation.py
# @Software:PyCharm

from datetime import datetime
from pathlib import Path
from format_wizard import taxon_completion, concat, fas2phy


def my_concatenation(in_path, out_path):
    t0 = datetime.now()
    out_path_obj = Path(out_path)
    if not out_path_obj.exists():
        out_path_obj.mkdir(exist_ok=True)
    file_list = [
        file.name
        for file in Path(in_path).iterdir()
        if file.suffix in [".fasta", ".fas", ".fa"]
    ]
    # todo: the description of trimal output seqs contain blank space?
    for file in file_list:
        fr = open(Path(in_path) / file, "r")
        records = fr.read().replace(" ", "")
        fr.close()
        fw = open(Path(in_path) / file, "w")
        fw.write(records)
        fw.close()
    taxon_completion(in_path=in_path, out_path=out_path)
    concat(in_path=str(Path(out_path) / "completion.result"), out_path=out_path)
    fas2phy(in_path=str(Path(out_path) / "concat.result"), out_path=out_path)
    t1 = datetime.now()
    print("Running time: %s seconds" % (t1 - t0))
