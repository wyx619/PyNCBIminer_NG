from pathlib import Path
import pandas as pd
from math import floor
from Bio import SeqIO
from main_utils import get_query_accession
from call_mafft2 import mafft
import tempfile
import shutil


def add_all_queries2(wd):
    print(
        "Aligning all reference sequences to calculate the missing length on the left and right side..."
    )
    ref_seq_path = Path(wd) / "parameters" / "ref_seq"
    # 2. 使用 Path 对象的 .iterdir() 方法，并将结果转换为列表，只保留.fasta文件
    queries_file_list = sorted([f for f in ref_seq_path.iterdir() if f.suffix == ".fasta"])
    # todo: think about only 1 round of blast
    if len(queries_file_list) == 0:
        print("Could not find query sequences in the parameters folder.")
        return

    # for queries_file in queries_file_list:
    #     fw = open(Path(wd)/Path("parameters")/Path("ref_msa")/Path(queries_file), "w")
    #     for record in SeqIO.parse(Path(wd)/Path("parameters")/Path("ref_seq")/Path(queries_file), "fasta"):
    #         fw.write((">%d|"+record.description+"\n") % int(Path(queries_file).stem.split("_")[-1]))
    #         fw.write(str(record.seq)+"\n")
    #     fw.close()
    msa_path = (
        Path(wd) / Path("parameters") / Path("ref_msa") / Path("msa_queries_1.fasta")
    )
    if not msa_path.exists() or msa_path.stat().st_size == 0:
        mafft(
            in_path=str(Path(wd) / Path("parameters") / Path("ref_seq") / Path("queries_1.fasta")),
            out_path=str(Path(wd) / Path("parameters") / Path("ref_msa")),
            algorithm="localpair",
            additional_params="--maxiterate 1000",
        )
        generated_msa = Path(wd) / Path("parameters") / Path("ref_msa") / Path("queries_1.fasta")
        if generated_msa.exists():
            generated_msa.rename(msa_path)

    if len(queries_file_list) > 1:
        ref_msa_file = "msa_queries_1_to_%d.fasta" % len(queries_file_list)
        ref_msa_dir = Path(wd) / Path("parameters") / Path("ref_msa")
        ref_msa_path = ref_msa_dir / ref_msa_file
        print(f"Expected MSA file: {ref_msa_file}")
        print(f"MSA file exists: {ref_msa_path.exists()}")
        if ref_msa_path.exists():
            print(f"MSA file size: {ref_msa_path.stat().st_size}")
        if not ref_msa_path.exists() or ref_msa_path.stat().st_size == 0:
            for n in range(2, len(queries_file_list) + 1):
                queries_file = Path(wd) / Path("parameters") / Path("ref_seq") / Path("queries_%d.fasta" % n)
                if n == 2:
                    prev_msa = Path(wd) / Path("parameters") / Path("ref_msa") / Path("msa_queries_1.fasta")
                else:
                    prev_msa = Path(wd) / Path("parameters") / Path("ref_msa") / Path("msa_queries_1_to_%d.fasta" % (n - 1))
                out_msa = Path(wd) / Path("parameters") / Path("ref_msa") / Path("msa_queries_1_to_%d.fasta" % n)

                print(f"Processing queries_{n}.fasta")
                print(f"  queries_file exists: {queries_file.exists()}")
                print(f"  prev_msa: {prev_msa.name}")
                print(f"  prev_msa exists: {prev_msa.exists()}")
                if not queries_file.exists():
                    print(f"  Skipping queries_{n}.fasta (file not found)")
                    continue
                if not prev_msa.exists():
                    print(f"  Skipping queries_{n}.fasta (previous MSA not found)")
                    continue

                print("Aligning %s with mafft..." % queries_file.name)
                with tempfile.TemporaryDirectory(dir=ref_msa_dir) as tmp_dir:
                    mafft(
                        in_path=str(prev_msa),
                        out_path=tmp_dir,
                        add_choice="addfragments",
                        add_path=str(queries_file),
                        algorithm="multipair",
                        thread=-1,
                    )
                    
                    generated_msa = Path(tmp_dir) / prev_msa.name
                    if generated_msa.exists() and generated_msa.stat().st_size > 0:
                        shutil.copy(generated_msa, out_msa)
                        print(f"  Generated: {out_msa.name}")
                    else:
                        print(f"  ERROR: Alignment failed for {queries_file.name}")
                
                print(f"  out_msa exists after alignment: {out_msa.exists()}")
                if out_msa.exists():
                    print(f"  out_msa size: {out_msa.stat().st_size}")

    else:
        ref_msa_file = "msa_queries_1.fasta"
    # todo:删除序列
    return ref_msa_file


def extend_hits(df, maxlen, qreflen, missing_left, missing_right):
    # df = df.copy()
    df[["sum_hits_score", "q_start", "q_end", "s_start", "s_end"]] = df[
        ["sum_hits_score", "q_start", "q_end", "s_start", "s_end"]
    ].apply(pd.to_numeric)
    df["hit_len"] = abs(df["s_end"] - df["s_start"]) + 1
    df["max_extension"] = maxlen - df["hit_len"]

    # auto_extension is used to add the unmatched two ends between query and subject to the subject
    df["auto_extension_left"] = df["q_start"] - 1
    df["auto_extension_right"] = qreflen - df["q_end"]

    # extra_extension extends the subject further if a query is a partial sequence of the target genetic marker
    df["extra_extension_left"] = missing_left
    df["extra_extension_right"] = missing_right

    # todo: use 1.2 * max_ref_len as maxlen?
    # todo: is int faster than float?
    # todo: extra 和 auto 的计算都是基于query，可以进行向量操作
    # todo: subject正向和反向的情况筛选之后也可以批量进行？
    if maxlen - qreflen > 0:  # maxlen > qreflen
        df["extension_left"] = df["auto_extension_left"] + df["extra_extension_left"]
        df["extension_right"] = df["auto_extension_right"] + df["extra_extension_right"]
        adjust_list = ((df["extension_left"] + df["extension_right"]) > 0) & (
            df["extension_left"] + df["extension_right"] > df["max_extension"]
        )
        p_ext_l = df.loc[adjust_list, "extension_left"] / (
            df.loc[adjust_list, "extension_left"]
            + df.loc[adjust_list, "extension_right"]
        )
        p_ext_r = 1 - p_ext_l
        df.loc[adjust_list, "extension_left"] = (
            df.loc[adjust_list, "max_extension"] * p_ext_l
        ).apply(floor)
        df.loc[adjust_list, "extension_right"] = (
            df.loc[adjust_list, "max_extension"] * p_ext_r
        ).apply(floor)
    else:  # maxlen < qreflen
        df["extension_left"] = df["auto_extension_left"]
        df["extension_right"] = df["auto_extension_right"]
    # todo: check the results of extension for reverse complement sequences
    df["q_extstart"] = df["q_start"] - df["extension_left"]
    df["q_extend"] = df["q_end"] + df["extension_right"]
    # positive strand
    df.loc[df["s_strand"], "s_extstart"] = (
        df.loc[df["s_strand"], "s_start"] - df.loc[df["s_strand"], "extension_left"]
    )
    df.loc[df["s_strand"], "s_extend"] = (
        df.loc[df["s_strand"], "s_end"] + df.loc[df["s_strand"], "extension_right"]
    )
    # negative strand
    # # s_end <------ s_start **** s_end - extension_left <----- s_start + extension_right
    # df.loc[~df["s_strand"], "s_extstart"] = df.loc[~df["s_strand"], "s_start"] + df.loc[~df["s_strand"], "extension_right"]
    # df.loc[~df["s_strand"], "s_extend"] = df.loc[~df["s_strand"], "s_end"] - df.loc[~df["s_strand"], "extension_left"]
    # s_end <------ s_start **** s_end - extension_right <----- s_start + extension_left
    df.loc[~df["s_strand"], "s_extstart"] = (
        df.loc[~df["s_strand"], "s_start"] + df.loc[~df["s_strand"], "extension_left"]
    )
    df.loc[~df["s_strand"], "s_extend"] = (
        df.loc[~df["s_strand"], "s_end"] - df.loc[~df["s_strand"], "extension_right"]
    )

    return df


def calculate_missing_length(wd, ref_msa_file):
    print(
        "Calculating the missing length on the left and right side of reference sequences..."
    )
    seq_dict = SeqIO.to_dict(
        SeqIO.parse(
            Path(wd) / Path("parameters") / Path("ref_msa") / Path(ref_msa_file),
            "fasta",
        ),
        key_function=get_query_accession,
    )
    all_queries_info = pd.read_table(
        Path(wd) / Path("parameters") / Path("all_queries_info.txt"), sep="\t"
    )
    all_queries_info.index = all_queries_info["ID"]
    for key in seq_dict.keys():
        if key in all_queries_info.index:
            seq = seq_dict[key].seq.upper()
            left = [seq.find("A"), seq.find("T"), seq.find("C"), seq.find("G")]
            right = [seq.rfind("A"), seq.rfind("T"), seq.rfind("C"), seq.rfind("G")]
            all_queries_info.loc[key, "Missing_left"] = min(left)
            all_queries_info.loc[key, "Missing_right"] = len(seq) - max(right) - 1
        else:
            print(f"Warning: {key} not found in all_queries_info.txt, skipping...")
    all_queries_info.to_csv(
        Path(wd) / Path("parameters") / Path("all_queries_info.txt"),
        sep="\t",
        index=False,
    )


def blast_results_extend_main(wd, max_len):
    ref_msa_file = add_all_queries2(wd)
    calculate_missing_length(wd, ref_msa_file)
    # todo: "query_acc.ver"改成ID？
    blast_results = pd.read_table(
        Path(wd) / Path("results") / Path("blast_results.txt"),
        sep="\t",
        engine="python",
    )
    # if "s_extstart" in blast_results.columns:
    #     return
    ref_info = pd.read_table(
        Path(wd) / Path("parameters") / Path("all_queries_info.txt"),
        sep="\t",
        engine="python",
    )
    extended_blast_results = []
    for blast_round in blast_results["Source"].value_counts().index:
        tmp_df = blast_results[blast_results["Source"] == blast_round].copy()
        sum_table = pd.read_table(
            Path(wd)
            / Path("tmp_files")
            / Path("BLAST_%d" % blast_round)
            / Path("blast_summary.txt"),
            sep="\t",
            engine="python",
        )
        # extend hits
        extended_hit_tables = []
        for name, group in tmp_df.groupby(tmp_df["query_acc.ver"]):
            if name.startswith("Query"):
                # todo: use query accession for query_acc.ver, parse hit-tables also need to be changed
                ref_id = sum_table[sum_table["Query"] == name].iloc[0]["ID"]
                ref_id = ref_id.split("|")[0].split(":")[0]
                group["query_acc.ver"] = ref_id
            else:
                ref_id = name
            # print(ref_id)

            qreflen = ref_info[ref_info["ID"] == ref_id].iloc[0]["Sequence_length"]
            missing_left = ref_info[ref_info["ID"] == ref_id].iloc[0]["Missing_left"]
            missing_right = ref_info[ref_info["ID"] == ref_id].iloc[0]["Missing_right"]
            print("Extending sequences found by %s..." % ref_id)
            extended_hit_tables.append(
                extend_hits(group, max_len, qreflen, missing_left, missing_right)
            )
        extended_hit_tables = pd.concat(extended_hit_tables)
        extended_blast_results.append(extended_hit_tables)
    extended_blast_results = pd.concat(extended_blast_results)
    extended_blast_results.to_csv(
        Path(wd) / Path("results") / Path("blast_results.txt"), index=False, sep="\t"
    )
