# 确保 sys.stdout 存在（PyInstaller 打包时可能为 None）
import os
import shutil
import sys
from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd
from Bio import AlignIO, SeqIO
from scipy.sparse import csr_matrix

from call_mafft2 import get_mafft_path
from functional import run_command
from main_utils import get_query_accession

# 导入MCL聚类模块
from mcl import get_clusters, run_mcl
from seq_check_download import seq_check_download_main

if sys.stdout is None:
    sys.stdout = open(os.devnull, "w")
if sys.stderr is None:
    sys.stderr = open(os.devnull, "w")


def geometric_adjacency(n, radius, positions):
    """Build the symmetric adjacency matrix of a geometric random graph.

    Nodes i and j (i != j) are connected iff their Euclidean distance <= radius.
    Equivalent to nx.random_geometric_graph + nx.to_scipy_sparse_array,
    including the inclusive (<=) edge threshold used by networkx.
    """
    coords = np.array([positions[i] for i in range(n)], dtype=float)
    diff = coords[:, None, :] - coords[None, :, :]
    dist_sq = np.sum(diff * diff, axis=2)
    adj = dist_sq <= radius * radius
    np.fill_diagonal(adj, False)
    return csr_matrix(adj.astype(float))


def cluster_queries(wd, ref_list=None):
    # todo: do this again if all selected sequences have low quality?
    df = pd.read_table(Path(wd) / Path("hits_selected.txt"), sep="\t", engine="python")
    # df.index = df["subject_acc.ver"]

    # delete reference sequences that have been used in previous search
    if ref_list is not None:
        df = df[~df["subject_acc.ver"].isin(ref_list)]

    df["qcluster"] = df["query_acc.ver"]
    sum_table = pd.read_table(
        Path(wd) / Path("blast_summary.txt"), sep="\t", engine="python"
    )
    groups = df.groupby(df["query_acc.ver"])
    index_list = []
    for name, group in groups:
        try:
            print("%s, %d sequences" % (name, len(group)))
            if len(group) < 3:
                print("Selecting one sequence found by this query randomly ...")
                index_list.append(np.random.choice(group.index, 1, replace=False)[0])
            else:
                query_ref_len = sum_table[sum_table["Query"] == name].iloc[0][
                    "Sequence_length"
                ]

                # todo: remove the sequences with too high or too low bit-score?
                print("remove the sequences with too high or too low bit-score")
                high_score = group["sum_hits_score"].quantile(0.75)
                low_score = group["sum_hits_score"].quantile(0.25)
                group = group[group["sum_hits_score"] <= high_score]
                group = group[group["sum_hits_score"] >= low_score]

                if len(group) > 1000:
                    print("Selecting 1000 sequences randomly...")
                    group = group.loc[
                        np.random.choice(group.index, 1000, replace=False)
                    ]
                time0 = datetime.now()
                print("Extracting positions...", end="")
                positions = {
                    i: (group.iloc[i]["q_start"], group.iloc[i]["q_end"])
                    for i in range(len(group))
                }
                time1 = datetime.now()
                print("running time: %s Seconds" % (time1 - time0))
                print("Generating network...", end="")
                matrix = geometric_adjacency(
                    group.shape[0], radius=0.1 * query_ref_len, positions=positions
                )  # get 56 clusters
                time2 = datetime.now()
                print("running time: %s Seconds" % (time2 - time1))
                print("Running MCL...", end="")

                result = run_mcl(matrix)
                time3 = datetime.now()
                print("running time: %s Seconds" % (time3 - time2))
                print("Getting clusters...", end="")
                clusters = get_clusters(result)
                time4 = datetime.now()
                print("running time: %s Seconds" % (time4 - time3))
                print("Total running time: %s Seconds" % (time4 - time0))
                print("get %d clusters" % len(clusters))
                print(
                    "Selecting the sequence with the longest align length from each cluster..."
                )
                for i, cluster in enumerate(clusters):
                    print("cluster %d, %d sequences" % (i, len(cluster)))
                    indices = group.iloc[list(cluster)].index
                    df.loc[indices, "qcluster"] = str(i)
                    index_list.append(
                        df.loc[indices]
                        .sort_values(
                            by=["sum_hits_alignlen", "sum_hits_score"],
                            ascending=[False, True],
                        )
                        .index[0]
                    )
                df.to_csv(
                    Path(wd) / Path("hits_selected_clusters.txt"), index=False, sep="\t"
                )
        except Exception as result:
            print(result)

    df1 = df.loc[index_list]
    df1 = df1.drop_duplicates(
        subset=None, keep="first", inplace=False, ignore_index=False
    )
    df1 = df1.sort_values(by="subject_acc.ver")
    # sort table
    df1.to_csv(Path(wd) / Path("hits_clustered.txt"), index=False, sep="\t")
    # Error: The truth value of a Series is ambiguous. Use a.empty, a.bool(), a.item(), a.any() or a.all().
    print("Selected %d sequences" % len(index_list))


def filter_seq(
    wd,
    max_length,
    table="hits_clustered.txt",
    fasta_file="hits_clustered.fasta",
    ref_seq_list=None,
):
    def get_accession(record):
        parts = record.description.split(":")
        return parts[0]

    df = pd.read_table(Path(wd) / Path(table), sep="\t", engine="python")
    df.index = df["subject_acc.ver"]
    file_list = [f.name for f in Path(wd).iterdir()]

    print("Removing errorneous sequences...")
    if ("erroneous_" + fasta_file in file_list) and (
        "erroneous_" + table not in file_list
    ):
        # the second condition is to avoid interruption
        seq_dict = SeqIO.to_dict(
            SeqIO.parse(Path(wd) / Path("erroneous_" + fasta_file), "fasta"),
            key_function=get_accession,
        )
        df_err = df.loc[seq_dict.keys()].copy()
        df_err.to_csv(Path(wd) / Path("erroneous_" + table), index=False, sep="\t")
        df = df.drop(seq_dict.keys())
        df.to_csv(Path(wd) / Path(table), index=False, sep="\t")

    print("Filtering low-quality sequences...")
    df["organism"] = ""
    df["seq_len"] = 0
    index_list = []
    n = 0
    if not (Path(wd) / "hits_clustered.fasta").exists():
        return 0
    if (Path(wd) / Path("hits_clustered.fasta")).stat().st_size == 0:
        return 0
    scluster = SeqIO.parse(Path(wd) / Path("hits_clustered.fasta"), "fasta")
    with open(Path(wd) / Path("hits_clustered_filtered.fasta"), "w") as fw:
        for record in scluster:
            index = record.description.split(":")[0]

            df.loc[index, "organism"] = record.description.split("|")[1].replace(
                "_", " "
            )
            seq = record.seq.lower()
            seq_len = seq.count("a") + seq.count("t") + seq.count("c") + seq.count("g")
            df.loc[index, "seq_len"] = seq_len
            if seq_len < 0.2 * max_length:
                print("Removed short sequence: " + index)
                n += 1
            elif seq_len < 0.995 * len(record.seq):
                print("Removed sequence with too many ambiguous bases: " + index)
                n += 1

            elif (ref_seq_list is not None) and (record.seq in ref_seq_list):
                print("Removed duplicate sequence: " + index)
                n += 1
            else:
                SeqIO.write(record, fw, "fasta")
                index_list.append(index)

    df1 = df.loc[index_list]
    df1.to_csv(Path(wd) / Path("hits_clustered_filtered.txt"), index=False, sep="\t")
    print("Deleted %d sequences." % n)
    print("Filtered sequences saved in hits_clustered_filtered.fasta")

    return len(df1)


def p_distance(wd, in_file):
    from scipy.spatial.distance import pdist, squareform

    alignment = AlignIO.read(Path(wd) / Path(in_file), "fasta")

    # 将序列转换为数值数组（A=0, T=1, C=2, G=3, -=4, 其他=5）
    # 使用向量化操作提高性能
    base_to_int = np.array([0] * 256, dtype=np.int8)  # 查找表
    for i, base in enumerate(b"ATCG"):
        base_to_int[base] = i
    base_to_int[ord("-")] = 4
    base_to_int[ord("N")] = 5

    # 转换为数值矩阵
    seq_array = np.zeros((len(alignment), len(alignment[0])), dtype=np.int8)
    for i, record in enumerate(alignment):
        seq_bytes = str(record.seq).upper().encode("ascii", errors="replace")
        seq_array[i, : len(seq_bytes)] = [base_to_int[b] for b in seq_bytes]

    # 使用 pdist 计算 p-distance（Hamming 距离归一化）
    distances = pdist(seq_array, metric="hamming")

    # 转换为方阵
    distance_matrix = squareform(distances)

    # 转换为 DataFrame
    df = pd.DataFrame(distance_matrix)

    return df


def my_mcl(wd, df, table):
    from scipy.sparse import lil_matrix

    # 检查输入是否为空
    if df is None or len(df) == 0:
        print("Warning: Distance matrix is empty.")
        return None

    # Nodes are considered adjacent if the distance between them is <= 0.3 units
    matrix = np.array(df)

    # 检查矩阵维度
    if matrix.ndim < 2 or matrix.shape[0] < 2 or matrix.shape[1] < 2:
        print(
            "Warning: Distance matrix has insufficient dimensions (%s)."
            % str(matrix.shape)
        )
        return None

    # 构建邻接矩阵：距离 <= 0.3 为相邻
    adj_matrix = (matrix <= 0.3).astype(int)
    np.fill_diagonal(adj_matrix, 1)  # 对角线设为 1

    # 转换为稀疏矩阵
    lil_mat = lil_matrix(adj_matrix)
    sparse_matrix = lil_mat.tocsr()

    try:
        # 运行 MCL 聚类
        result = run_mcl(sparse_matrix)
        clusters = get_clusters(result)

        # 检查聚类结果是否为空
        if clusters is None or len(clusters) == 0:
            print("Warning: MCL returned no clusters.")
            return None

        # 读取表格并处理
        df1 = pd.read_table(Path(wd) / Path(table), sep="\t", engine="python")
        df1["scluster"] = -1

        # 从每个聚类中选择序列
        index_list = []
        for i, cluster in enumerate(clusters):
            cluster_indices = list(cluster)
            df1.loc[cluster_indices, "scluster"] = i

            # 选择该聚类中最长的序列
            selected_idx = (
                df1.loc[cluster_indices]
                .sort_values(by="seq_len", ascending=False)
                .index[0]
            )
            index_list.append(selected_idx)

        # 保存聚类结果
        df1.to_csv(Path(wd) / Path(table), index=False, sep="\t")

        # 返回选中的序列
        print("get %d clusters" % len(index_list))
        df2 = df1.iloc[index_list].sort_values(by="subject_acc.ver")
        return df2

    except Exception as e:
        print("MCL clustering failed: %s" % str(e))
        return None


def cluster_sequences(wd, fasta_file=r"hits_clustered_filtered.fasta"):
    print("Clustering sequences...")
    msa_file = "msa_" + fasta_file
    table_file = Path(wd) / Path("hits_clustered_filtered.txt")
    output_file = Path(wd) / Path("sequences_clustered.txt")

    # 检查输入文件
    fasta_path = Path(wd) / Path(fasta_file)
    if not fasta_path.exists() or fasta_path.stat().st_size == 0:
        print("Warning: %s does not exist or is empty." % fasta_file)
        return None

    # 统计序列数
    n_seq = sum(1 for _ in SeqIO.parse(fasta_path, "fasta"))

    # 序列数 < 5，跳过 MCL
    if n_seq < 5:
        print(
            "Only %d sequences left after filtering. No need to do MCL step2." % n_seq
        )
        seq_clustered = pd.read_table(table_file, sep="\t")
        seq_clustered.to_csv(output_file, index=False, sep="\t")
        return seq_clustered

    # 运行 MAFFT
    print("Running MAFFT L-INS-i alignment...")
    mafft_exe = get_mafft_path()
    command = f"{mafft_exe} --localpair --maxiterate 1000 {fasta_path} > {Path(wd) / msa_file}"
    run_command(command)

    # 检查 MAFFT 结果
    msa_path = Path(wd) / Path(msa_file)
    if not msa_path.exists() or msa_path.stat().st_size == 0:
        print("Warning: MAFFT failed to generate alignment.")
        seq_clustered = pd.read_table(table_file, sep="\t")
        seq_clustered.to_csv(output_file, index=False, sep="\t")
        return seq_clustered

    # 计算 p-distance
    print("Calculating p-distance matrix...")
    seq_distance = p_distance(wd, msa_file)
    seq_distance.to_csv(
        Path(wd) / Path(Path(msa_file).stem + "_distance.txt"), index=True, sep="\t"
    )

    # 运行 MCL（带错误处理）
    print("Running MCL clustering...")
    table = r"hits_clustered_filtered.txt"

    # 尝试调用 my_mcl
    seq_clustered = my_mcl(wd, seq_distance, table)

    # Fallback：如果 MCL 失败，使用所有序列
    if seq_clustered is None:
        print("MCL failed, using all filtered sequences.")
        seq_clustered = pd.read_table(table_file, sep="\t")

    seq_clustered.to_csv(output_file, index=False, sep="\t")
    return seq_clustered


def select_new_queries(tmp_wd, blast_round, ref_number):
    seq_clustered = pd.read_table(
        Path(tmp_wd) / Path(r"sequences_clustered.txt"), sep="\t", engine="python"
    )
    seq_clustered.index = seq_clustered["subject_acc.ver"]

    """
    if "all_new_queries_info.txt" in file_list:
        all_new_queries = pd.read_table(Path(wd) / Path("parameters") / Path(r"all_new_queries_info.txt"), sep='\t',
                                        engine='python')
    #     all_new_queries.index = all_new_queries["subject_acc.ver"]
    #     indices = set(seq_clustered.index) - set(all_new_queries.index)
    #     if len(indices) < 1:
    #         print("Cannot find more new references. Stop iteration.")
    #         return 0
    #     seq_clustered = seq_clustered.loc[indices]
    else:
        all_new_queries = None
    """

    if seq_clustered.shape[0] > ref_number:
        print("Selecting %d sequences randomly..." % ref_number)
        index_list = np.random.choice(
            range(seq_clustered.shape[0]), ref_number, replace=False
        )
        seq_clustered = seq_clustered.iloc[index_list]

    seq_clustered["blast_round"] = blast_round

    """
    if all_queries is None:
        all_queries = seq_clustered
    else:
        all_queries = all_queries.append(seq_clustered)
    """

    fw = open(Path(tmp_wd) / Path("new_queries.fasta"), "w")
    fw.close()
    fasta_file = r"hits_clustered_filtered.fasta"
    seq_dict = SeqIO.to_dict(
        SeqIO.parse(Path(tmp_wd) / Path(fasta_file), "fasta"),
        key_function=get_query_accession,
    )
    for index in seq_clustered.index:
        record = seq_dict[index]
        with open(Path(tmp_wd) / Path("new_queries.fasta"), "a") as fw:
            SeqIO.write(record, fw, "fasta")
    print("Selected %d new references. " % seq_clustered.shape[0])

    seq_clustered.to_csv(
        Path(tmp_wd) / Path("new_queries_info.txt"), index=False, sep="\t"
    )  # write info table after new seq added to fas file
    # all_new_queries.to_csv(Path(wd) / Path("parameters") / Path("all_queries_info.txt"), index=False, sep="\t")

    return seq_clustered.shape[0]


def _valid_table(wd, table):
    """True if the table file exists and contains at least one data row.

    A stale file that only contains the header (e.g. produced by a crashed
    run) is treated as invalid so that the corresponding step is re-run.
    """
    path = Path(wd) / table
    if not path.exists() or path.stat().st_size == 0:
        return False
    try:
        return pd.read_table(path, sep="\t", engine="python").shape[0] > 0
    except Exception:
        return False


def select_new_queries_main(
    wd,
    tmp_wd,
    key_annotations,
    exclude_sources,
    entrez_email,
    max_length,
    blast_round,
    ref_number,
    allowed_taxa,
    stop_flag=None,
):
    if not _valid_table(tmp_wd, "hits_clustered.txt"):
        print("Selecting new references...")

        if (Path(wd) / "parameters" / "all_queries_info.txt").exists():
            all_queries = pd.read_table(
                Path(wd) / Path("parameters") / Path(r"all_queries_info.txt"),
                sep="\t",
                engine="python",
            )
            all_queries_list = all_queries["ID"]
            cluster_queries(wd=tmp_wd, ref_list=all_queries_list)
            # todo: what to do if no more new reference sequnces could be found
        else:
            cluster_queries(wd=tmp_wd)
    else:
        qcluster_table = pd.read_table(
            Path(tmp_wd) / Path("hits_clustered.txt"), sep="\t", engine="python"
        )
        print(
            "Get %d clusters according to query start and query end."
            % qcluster_table.shape[0]
        )
        del qcluster_table
    # todo: hits_clustered.txt main contain repeated rows???

    if not _valid_table(tmp_wd, "hits_clustered_filtered.txt"):
        seq_check_download_main(
            wd=tmp_wd,
            acc_file=r"hits_clustered.txt",
            out_file=r"hits_clustered.fasta",
            key_annotations=key_annotations,
            exclude_sources=exclude_sources,
            entrez_email=entrez_email,
            allowed_taxa=allowed_taxa,
            stop_flag=stop_flag,
        )
        if (Path(wd) / "parameters" / "ref_seq").exists():
            ref_file_list = [
                f.name for f in (Path(wd) / "parameters" / "ref_seq").iterdir()
            ]
            ref_seq_list = []
            for file in ref_file_list:
                for record in SeqIO.parse(
                    Path(wd) / Path("parameters") / Path("ref_seq") / Path(file),
                    "fasta",
                ):
                    ref_seq_list.append(record.seq)
            n_hits_clustered_filtered = filter_seq(
                wd=tmp_wd, max_length=max_length, ref_seq_list=ref_seq_list
            )
            # print("Number of hits_clustered_filtered %d" % n_hits_clustered_filtered)
            # todo: sometimes the clustering will fail when sequences number is too small.
            if n_hits_clustered_filtered < 1:
                print("Cannot find more new reference, stop iteration. ")
                return None
    # if hits_clustered.fasta only contain no more than 5 sequences, then no need to do MCL step2
    if not _valid_table(tmp_wd, "sequences_clustered.txt"):
        scluster_table = cluster_sequences(wd=tmp_wd)
    else:
        scluster_table = pd.read_table(
            Path(tmp_wd) / Path("sequences_clustered.txt"), sep="\t", engine="python"
        )

    if scluster_table is None:
        print("No sequence passed filtering.")
        print("Cannot find more new reference, stop iteration. ")
        return None

    elif scluster_table.shape[0] > 0:
        if "scluster" in scluster_table.columns:
            print(
                "Get %d clusters according to sequence distance."
                % scluster_table.shape[0]
            )
        else:
            print(
                "Using all of the %d sequences selected in MCL step1."
                % scluster_table.shape[0]
            )
        del scluster_table

    else:
        print("Cannot find more new reference, stop iteration. ")
        del scluster_table
        return None

    blast_round += 1
    if not _valid_table(tmp_wd, "new_queries_info.txt"):
        new_quereis_num = select_new_queries(tmp_wd, blast_round, ref_number)
        # todo: new ref seqs need to be more than 2???
        if new_quereis_num < 1:
            print("Cannot find more new reference. Stop iteration.")
            return None
    else:
        new_queries = pd.read_table(
            Path(tmp_wd) / Path(r"new_queries_info.txt"), sep="\t", engine="python"
        )
        new_quereis_num = new_queries.shape[0]
        print("Selected %d new queries." % new_quereis_num)

    if not (
        Path(wd) / "parameters" / "ref_seq" / ("queries_%d.fasta" % blast_round)
    ).exists():
        shutil.copy2(
            Path(tmp_wd) / Path("new_queries.fasta"),
            Path(wd)
            / Path("parameters")
            / Path("ref_seq")
            / Path("queries_%d.fasta" % blast_round),
        )

    # extend hits After BLAST iteration.
    return new_quereis_num
