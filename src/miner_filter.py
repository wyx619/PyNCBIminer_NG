import os
import re
import shutil
import sys
import time
from pathlib import Path

import pandas as pd
from Bio import SeqIO
from Bio.Seq import Seq

from functional import create_folder
from nt_calculator import nt_Calculator

try:
    DEVNULL = os.devnull
except Exception:
    DEVNULL = "nul"

if sys.stdout is None:
    sys.stdout = open(DEVNULL, "w")
if sys.stderr is None:
    sys.stderr = open(DEVNULL, "w")


from call_mafft2 import get_mafft_path

mafft_exe = None


def _get_mafft_exe():
    global mafft_exe
    if mafft_exe is None:
        mafft_exe = get_mafft_path()
    return mafft_exe


class Miner_filter:
    """CLass Miner_filter - filter retrieved seqs, including three main functions:
        1. <func> control_extension: control the extension of all seqs, trim if necessary.
        2. <func> combine_species: combine specific records to corresponding species (subsp., var., f.)
        3. <func> remove_exceptional_records: remove specific records (sp., cf., aff., x, and short ones)
        4. <func> reduce_dataset: select best marker for each taxon.

    Public:
        <func> Miner_filter - construction method
        <func> control_extension: control the extension of all seqs, trim if necessary.
        <func> combine_species: combine specific records to corresponding species (subsp., var., f.)
        <func> remove_exceptional_records: remove specific records (sp., cf., aff., x, and short ones)
        <func> reduce_dataset: select best marker for each taxon.
        <func> get_consensus_dict: "get method" to get taxa consensus dict

    Private:
        <attr> in_path - input path of this class, usually the output (working directory) of "retrived sequences"
        <attr> out_path - output path of this class, usually the output (working directory) of "retrived sequences"
        <attr> tmp_path - destination folder of temporary files
        <attr> log_path - destination folder of log files
        <attr> num_query - the number of sequences in the query
        <attr> quality_control_max_size_subset - the maximum size when spliting subsets
        <attr> <class> nt_calculator - some functions for pairwise identity calculation, etc.
        <attr> taxa_consensus_dict - a dictionary storing consensus sequence for each taxon

        <func> get_input_filename - get the most valid (suitable) filename as input fasta file

        ================================== for <func> control_extension ===========================================
        <func>[static] get_upper_taxonomic_unit - get the upper taxonomic group of the given taxonomy
        <func> split_by_genus - split the fasta file according to genus of the records
        <func> split_by_length - split the fastas according to relative length of the records
        <func> split_large_subset - split the fastas according to number of the records
        <func> align_subset - align the subsets split previously
        <func> remove_erroneous_extension - remove extension if the extension part is too gappy in the MSA

        ================================== for <func> reduce_dataset ==============================================
        <func>[static] get_length_without_wobble - get the number of ATCGs in the sequence
        <func>[static] check_record_coverage - check if given segment contains too many gaps (NOT IN USE)
        <func> calculate_consensus_dict - calculate consensus sequence for each taxon and store to a dictionary
        <func> count_num_query - count the number of sequences in the first query
        <func> align_long_seq - align sequences from the blast_result_long (chosen ones) using --add (NOT IN USE)
        <func> evaluate_seq - evaluate each sequence for representative selecton
        <func> select_seqs_to_keep - select sequences from each taxon according to 3 criteria and write into tsv
        <func> save_selected_seqs - save only the selected sequences into fasta according to the saved csv
    """

    def __init__(self, in_path, out_path, DEBUG_MODE=False):
        """construction and method
        ----------
        Parameters
        - in_path - input path of this class, usually the output (working directory) of "retrived sequences"
        - out_path - output path of this class, usually the output (working directory) of "retrived sequences"
        """
        self.__in_path = Path(
            in_path
        )  # usually the output folder (working directory) of the "retrived sequences"
        self.__out_path = Path(out_path)

        # Check if results directory exists
        results_path = self.__out_path / "results"
        if not results_path.exists():
            raise FileNotFoundError(f"Results directory not found: {results_path}")

        self.__tmp_path = self.__out_path / "tmp_files"
        self.__log_path = self.__out_path
        self.__num_query = 0  # the number of sequences in the query, initiated as 0
        self.__quality_control_max_size_subset = 0
        self.__nt_calculator = nt_Calculator()
        self.__taxa_consensus_dict = {}  # {"Magnolia coco": "AATTCCGG", "taxon 2": "AATCGCCTT", ...}
        self.DEBUG_MODE = DEBUG_MODE

        files = [
            "blast_results_non_duplicate.fasta",
            "blast_results_exception_removed.fasta",
            "blast_results_checked_seq_info_modified.txt",
            "blast_result_kept.txt",
            "blast_results_filtered.fasta",
        ]

        file_time = False
        backup_folder = self.__out_path / "results" / "history_backup"
        create_folder(backup_folder)
        for file in [f.name for f in (self.__out_path / "results").iterdir()]:
            if file in files:
                if not file_time:
                    file_time = time.localtime(
                        (self.__out_path / "results" / file).stat().st_mtime
                    )
                    file_time = time.strftime("%Y-%m-%d.%H.%M'.%S''", file_time)
                    backup_folder = backup_folder / file_time
                    create_folder(backup_folder)
                shutil.move(self.__out_path / "results" / file, backup_folder / file)

        tmp_files = [
            # "consensus_calculation",
            "blast_result_kept.txt",
            "blast_result_long.fasta",
            "blast_result_long.txt",
        ]
        for path in self.__tmp_path.iterdir():
            if path.name in tmp_files:
                try:
                    if path.is_dir():
                        shutil.rmtree(path)
                    else:
                        path.unlink()
                except Exception:
                    pass

    def remove_exceptional_records(
        self,
        in_path=None,
        out_path=None,
        sp=True,
        cf=True,
        aff=True,
        x=True,
        length_threshold=0,
        ignore_gap=True,
    ):
        """remove specific records (sp., cf., aff., x, and short ones)
        ----------
        Parameters
        - in_path - input path of fasta file (for independent calling), or None to remain the same as this class
        - out_path - output path of fasta file (for independent calling), or None to remain the same as this class
        - sp  - if True, records with " sp. "  will be removed
        - cf  - if True, records with " cf. "  will be removed
        - aff - if True, records with " aff. " will be removed
        - x   - if True, records with " x "    will be removed
        - length_threshold - sequences shorter than this value will be removed
        - ignore_gap - if True, gaps will be ignored when counting lengths of sequences
            for example:
                for record.seq = "AATT-CGGAA", length_threshold = 10, ignore_gap = True,
                    this length will be recorded as 9, thus lower than threshold, will be removed
                while for record.seq = "AATT-CGGAA", length_threshold = 10, ignore_gap = False,
                    this length will be recorded as 10, thus not lower than threshold, will be kept.
        """
        ## STEP 1: get paths ready, independent calling allowed
        if in_path:
            this_in_path = Path(in_path)
        else:
            curr_step = "blast_results_exception_removed.fasta"
            this_in_path = (
                self.__in_path / "results" / self.__get_input_filename(curr_step)
            )

        if out_path:
            this_out_path = Path(out_path)
        else:
            this_out_path = self.__out_path / "results"

        df_path = self.__in_path / "results" / self.__get_info_csv()
        df_records_info = pd.read_csv(df_path, sep="\t")
        out_file_name = "blast_results_exception_removed.fasta"

        ## STEP 2: set special tokens to be removed
        remove_list = []
        if sp:
            remove_list.append("_sp._")
            remove_list.append("_sp_")
        if cf:
            remove_list.append("_cf._")
            remove_list.append("_cf_")
        if aff:
            remove_list.append("_aff._")
            remove_list.append("_aff_")
        if x:
            remove_list.append("_x._")
            remove_list.append("_x_")

        ## STEP 3: keep seqs other than sequences with specified token or lower than length threshold
        record_iter = SeqIO.parse(this_in_path, "fasta")
        accession_to_organism = dict(
            zip(df_records_info["accession"].values, df_records_info["organism"].values)
        )
        filtered_records = []
        for record in record_iter:
            if ignore_gap:
                record.seq = Seq(str(record.seq).replace("-", ""))

            accession = record.description.split("|")[0].split(":")[0]
            organism = accession_to_organism.get(accession)
            if organism is None:
                continue

            organism = organism.replace(" ", "_")
            if any([banned_word in organism for banned_word in remove_list]):
                continue

            if len(record.seq) < length_threshold:
                continue
            filtered_records.append(record)

        out_fasta = str(this_out_path / out_file_name)
        SeqIO.write(filtered_records, out_fasta, "fasta")

        df_records_info.dropna(subset=["organism"], inplace=True)
        df_records_info.to_csv(df_path, index=False, sep="\t")

    def combine_species(self, subsp=True, var=True, f=True):
        """combine specific records(subsp, var, f) into their species
                method: by renaming the column ['organism'] in table blast_results_checked_seq_info.txt
                example: if subsp == True, treat V._rafinesquianum_var._affine and V._rafinesquianum equally in next steps
        ----------
        Parameters
        - subsp - if True, records with " subsp. "  will be combined to their species
        - var   - if True, records with " var. "    will be combined to their species
        - f     - if True, records with " f. "      will be combined to their species
        """
        ## STEP 1: load blast_results_checked_seq_info.txt
        df_records_info = pd.read_csv(
            self.__in_path / "results" / "blast_results_checked_seq_info.txt", sep="\t"
        )

        ## STEP 2: set special tokens to be removed
        combine_list = []
        if subsp:
            combine_list.append(" subsp. ")
            combine_list.append(" subsp ")
            combine_list.append(" ssp. ")
            combine_list.append(" ssp ")
        if var:
            combine_list.append(" var. ")
            combine_list.append(" var ")
        if f:
            combine_list.append(" f. ")
            combine_list.append(" f ")

        ## STEP 3: modify the info csv (blast_results_checked_seq_info.txt)
        rows_to_drop = []
        for i in df_records_info.index:
            organism = df_records_info.loc[i, "organism"]
            if not isinstance(organism, str):
                rows_to_drop.append(i)
                continue
            for word in combine_list:
                if word in organism:
                    df_records_info.loc[i, "organism"] = organism[
                        : organism.index(word)
                    ]
                    break

        df_records_info.drop(rows_to_drop, axis=0, inplace=True)

        csv_out_path = (
            self.__in_path / "results" / "blast_results_checked_seq_info_modified.txt"
        )
        df_records_info.to_csv(csv_out_path, sep="\t", index=False)

    def _tnrs_correct_names(self, tnrs_sources, tnrs_accuracy, emit_log):
        """Correct organism names via TNRS API before species-level selection.

        Returns False if TNRS fails (caller should abort), True otherwise.
        """
        import shutil

        from Chloroplast.TNRS import TNRS_cached

        info_path = self.__in_path / "results" / self.__get_info_csv()
        df = pd.read_csv(info_path, sep="\t")

        names = [n.strip() for n in df["organism"].dropna().unique().tolist()]
        if not names:
            emit_log("No organism names found. Skipping TNRS.", "WARNING")
            return True

        cache_dir = self.__in_path / "tnrs_cache"

        tnrs_result = TNRS_cached(
            taxonomic_names=names,
            sources=tnrs_sources,
            accuracy=tnrs_accuracy,
            cache_dir=cache_dir,
            emit_log=emit_log,
        )

        if tnrs_result is None:
            emit_log(
                "TNRS name resolution failed. Aborting reduce_dataset. "
                "Re-run to retry failed batches.",
                "WARNING",
            )
            return False

        resolved = tnrs_result[
            tnrs_result["Overall_score"].notna()
            & (tnrs_result["Overall_score"] >= (tnrs_accuracy or 0))
            & tnrs_result["Accepted_name"].notna()
            & (tnrs_result["Accepted_name"] != "")
            & tnrs_result["Taxonomic_status"].isin(["Accepted", "Synonym"])
            & (tnrs_result["Accepted_name_rank"] != "genus")
        ]
        rename_map = dict(zip(resolved["Name_submitted"], resolved["Accepted_name"]))

        backup_path = info_path.with_suffix(".txt.bak")
        shutil.copy2(info_path, backup_path)

        df["organism"] = df["organism"].map(
            lambda x: rename_map.get(x.strip()) if isinstance(x, str) else None
        )
        df.to_csv(info_path, sep="\t", index=False)

        n_resolved = len(rename_map)
        n_corrected = sum(1 for n in names if n in rename_map and rename_map[n] != n)
        n_excluded = len(names) - n_resolved
        emit_log(
            f"TNRS: {n_resolved}/{len(names)} names resolved "
            f"({n_corrected} corrected), {n_excluded} not resolved (will be excluded).",
            "INFO",
        )
        return True

    def reduce_dataset(
        self,
        consensus_value=True,
        subsp=True,
        var=True,
        f=True,  # for species combination
        sp=True,
        cf=True,
        aff=True,
        x=True,
        length_threshold=0,
        ignore_gap=True,  # for exception removal
        max_insertion_length=20,
        max_insertion_num=1,  # for deletion of large inserted fragment
        enable_tnrs=False,
        tnrs_sources=None,
        tnrs_accuracy=None,
        emit_log=None,
    ):
        """to reduce the dataset by select the best representative sequence for each taxon
        ----------
        Parameters
        - sp  - if True, records with " sp. "  will be removed
        - cf  - if True, records with " cf. "  will be removed
        - aff - if True, records with " aff. " will be removed
        - x   - if True, records with " x "    will be removed
        - length_threshold - sequences shorter than this value will be removed
        - ignore_gap - if True, gaps will be ignored when counting lengths of sequences
        - enable_tnrs - if True, correct organism names via TNRS API before selection
        - tnrs_sources - comma-separated TNRS sources (e.g. "wcvp,wfo")
        - tnrs_accuracy - minimum TNRS matching accuracy (0 < value <= 1)
        - emit_log - optional callback(message, level) for GUI logging
        """
        if emit_log is None:

            def emit_log(msg, level="INFO"):
                print(f"[{level}] {msg}")

        if enable_tnrs:
            if not self._tnrs_correct_names(tnrs_sources, tnrs_accuracy, emit_log):
                return

        df = pd.read_csv(self.__in_path / "results" / self.__get_info_csv(), sep="\t")
        for row_index, row in df.iterrows():
            organism = row["organism"]
            if isinstance(organism, str):
                if "'" in organism:
                    df.loc[row_index, "organism"] = organism.replace("'", "")
        df.to_csv(
            self.__in_path / "results" / self.__get_info_csv(), sep="\t", index=False
        )

        self.__count_consensus_value = consensus_value

        self.combine_species(subsp=subsp, var=var, f=f)
        self.remove_exceptional_records(
            sp=sp,
            cf=cf,
            aff=aff,
            x=x,
            length_threshold=length_threshold,
            ignore_gap=ignore_gap,
        )
        self.remove_duplicate()
        if self.__count_consensus_value:
            self.__calculate_consensus_dict(
                length_threshold=max_insertion_length, taxa_threshold=max_insertion_num
            )
        self.__evaluate_seq()  # may need further discussion
        self.__select_seqs_to_keep()
        self.__save_selected_seqs()

    def remove_duplicate(self):
        """remove redundant records (records with exactly same voucher name and sequence are defined redundancy)"""
        ## STEP 1: load blast_results_checked_seq_info.txt and fasta file
        curr_step = "blast_results_non_duplicate.fasta"
        df_records_info = pd.read_csv(
            self.__in_path / "results" / "blast_results_checked_seq_info.txt", sep="\t"
        )
        record_iter = list(
            SeqIO.parse(
                self.__in_path / "results" / self.__get_input_filename(curr_step),
                "fasta",
            )
        )
        df_records_info["specimen_voucher"] = df_records_info[
            "specimen_voucher"
        ].fillna("unknown")

        accession_set = set(df_records_info["accession"])
        record_iter = [
            record
            for record in record_iter
            if record.description.split("|")[0].split(":")[0] in accession_set
        ]

        accession_to_voucher = dict(
            zip(
                df_records_info["accession"].values,
                df_records_info["specimen_voucher"].values,
            )
        )
        accession_to_organism = dict(
            zip(df_records_info["accession"].values, df_records_info["organism"].values)
        )

        record_iter = sorted(
            list(record_iter),
            key=lambda record: accession_to_voucher.get(
                record.description.split("|")[0].split(":")[0], "      "
            ),
        )

        vouchers = [
            accession_to_voucher.get(
                record.description.split("|")[0].split(":")[0], "      "
            )
            for record in record_iter
        ]
        vouchers = [
            "      " if voucher == "unknown" else voucher for voucher in vouchers
        ]

        organisms = [
            accession_to_organism.get(record.description.split("|")[0].split(":")[0])
            for record in record_iter
        ]

        ## STEP 2: traverse all the records and record non duplicate ones, those with vouchers first

        df = pd.DataFrame(
            {
                "accession": [
                    record.description.split("|")[0].split(":")[0]
                    for record in record_iter
                ],
                "seq": [record.seq for record in record_iter],
                "voucher": vouchers,
                "organism": organisms,
            }
        )

        df = df.groupby("organism").apply(
            lambda x: x.sort_values(
                by=["seq", "voucher"], ascending=[True, False]
            ).drop_duplicates(subset=["seq", "voucher"], keep="first"),
            include_groups=False,
        )

        accession_numbers = list(df["accession"])

        ## STEP 3: save records according to list accession_numbers
        records = [
            record
            for record in record_iter
            if record.description.split("|")[0].split(":")[0] in accession_numbers
        ]
        SeqIO.write(records, self.__in_path / "results" / curr_step, "fasta")

    def control_extension(self, gappyness_threshold=0.5):
        """control the extension of all seqs, trim if necessary
        ----------
        Parameters
        - gappyness_threshold - if extension with gappyness more than this number will be removed/trimmed
        """
        from functional import create_folder

        # Check and remove duplicates if needed
        out_file = self.__out_path / "results" / "blast_results_non_duplicate.fasta"
        if not out_file.exists():
            self.remove_duplicate()

        create_folder(self.__out_path / "tmp_files/extension_control")
        print("Step 1/3: splitting sequences by genus...")
        self.__split_by_genus()
        print("Step 2/3: aligning subsets with MAFFT...")
        self.__align_subset()
        print("Step 3/3: checking gappyness and trimming extensions...")
        self.__remove_erroneous_extension(gappyness_threshold=gappyness_threshold)

    def get_consensus_dict(self):
        """get method: get taxa consensus dict
        -------
        Returns
        - self.__taxa_consensus_dict - the dictionary of consensus sequence of each taxon
        """
        return self.__taxa_consensus_dict

    def __get_input_filename(self, curr_step=None):
        """get the most valid (suitable) filename as input fasta file
        ----------
        Parameters
        - curr_step - output filename of current step, for limitation of searching space
        -------
        Returns
        - matching_filename - the most valid (suitable) filename as input fasta file
        """
        path = self.__in_path / "results"
        existing_files = set(f.name for f in path.iterdir())
        files = [
            "blast_results_checked.fasta",
            "blast_results_controlled.fasta",
            "blast_results_exception_removed.fasta",
            "blast_results_non_duplicate.fasta",
        ]
        if not curr_step:
            curr_step = len(files) - 1
        else:
            curr_step = files.index(curr_step)

        file_range = max(len(files) - 1, curr_step - 1)
        for i in range(file_range, -1, -1):
            if files[i] in existing_files:
                matching_filename = files[i]
                return matching_filename

        raise FileNotFoundError(
            f"No valid input fasta file found in {path}. "
            f"Expected one of: {files[: file_range + 1]}. "
            f"Found: {existing_files}"
        )

    ## ===========================================================================================================
    ## ================================== for <func> reduce_dataset ==============================================
    def __get_info_csv(self):
        """check if there are modified seq info table in the path, if not, load original one"""
        if (
            self.__in_path / "results" / "blast_results_checked_seq_info_modified.txt"
        ).is_file():
            return "blast_results_checked_seq_info_modified.txt"
        else:
            return "blast_results_checked_seq_info.txt"

    @staticmethod
    def __get_length_without_wobble(record):
        """get the number of ATCGs in the sequence (only ATCG are counted, RYKMSWBDHVN and gap '-' are ignored)
        ----------
        Parameters
        - record - the record to count length
        -------
        Returns
        - seq_length - the length of the sequence (not counting wobbles like WSPYN...)
        """
        seq_str = str(record.seq).upper()
        trans_table = str.maketrans("", "", "RYKMSWBDHVN-")
        return len(seq_str.translate(trans_table))

    @staticmethod
    def __remove_minor_large_insertion(
        record_path, length_threshold=20, taxa_threshold=1, keep_tmp=False
    ):
        import numpy as np

        ## STEP 1: load related information
        record_iter = list(SeqIO.parse(record_path, "fasta"))
        records = np.array([list(str(record.seq).upper()) for record in record_iter])

        ## STEP 2: record minor large insertion (in list remove_ends)
        single_insertion_columns = []
        num_taxa = records.shape[0]
        for col in range(records.shape[1]):
            if np.sum(records[:, col] == "-") >= num_taxa - taxa_threshold:
                single_insertion_columns.append(col)

        if not single_insertion_columns:
            return []

        prev_col = single_insertion_columns[0]
        final_col = single_insertion_columns[-1]
        start = single_insertion_columns[0]
        remove_ends = []  # [[0,50], [start2, end2]] means 0~50 bp and start2~end2 bp will be removed
        count = 1

        for col in single_insertion_columns[1:]:
            if col - prev_col == 1 and col != final_col:
                count += 1
            elif col - prev_col == 1 and col == final_col:
                count += 1
                if count >= length_threshold:
                    remove_ends.append([start, col])
                count = 1
                start = col
            else:
                if count >= length_threshold:
                    remove_ends.append([start, prev_col])
                count = 1
                start = col

            prev_col = col

        ## STEP 3: remove those recorded insertion in both msa file and unaligned file
        ## substep 1: remove those insertion in all records
        for record in record_iter:
            if not remove_ends:
                return []
            if keep_tmp and Path(record_path).is_file():
                shutil.copy(record_path, record_path.replace(".fasta", "_backup.fasta"))
                shutil.copy(
                    record_path.replace("_msa.fasta", ".fasta"),
                    record_path.replace("_msa.fasta", "_backup.fasta"),
                )
            for ends in remove_ends:
                sequence = record.seq
                sequence = (
                    sequence[: ends[0]]
                    + "-" * (ends[1] - ends[0] + 1)
                    + sequence[ends[1] + 1 :]
                )
            sequence = Seq(str(sequence).replace("-", ""))
            record.seq = sequence

        ## substep 2: write into unaligned file

        SeqIO.write(record_iter, record_path, "fasta")

        ## substep 3: write into msa file (直接使用 subprocess)
        import subprocess

        temp_output = str(record_path).replace(".fasta", "_temp.fasta")

        record_path_str = Path(record_path).as_posix()
        temp_output_str = Path(temp_output).as_posix()
        mafft_exe_str = Path(_get_mafft_exe()).as_posix()

        commandstr = f'"{mafft_exe_str}" --auto --quiet "{record_path_str}" > "{temp_output_str}"'

        result = subprocess.run(commandstr, shell=True, capture_output=True, text=True)

        if result.returncode != 0:
            raise RuntimeError(f"MAFFT failed: {result.stderr}")

        if not Path(temp_output).exists():
            raise RuntimeError("MAFFT output file not created")

        Path(temp_output).replace(record_path)
        size2 = record_path.stat().st_size
        if size2 == 0:
            raise ValueError(f"MAFFT failed to align {record_path}")

        return remove_ends

    def __calculate_consensus_dict(self, length_threshold=20, taxa_threshold=1):
        """calculate consensus sequence for each taxon and store to a dictionary
        ----------
        Parameters
        - length_threshold - for <func> remove_long_insertion:  insertion longer than this threshold will be removed
        - taxa_threshold - for <func> remove_long_insertion: insertion in at most [taxa_threshold] taxa will be removed
        """
        in_path = self.__in_path / "results"
        tmp_path = self.__tmp_path / "consensus_calculation"
        create_folder(tmp_path)

        df_records_info = pd.read_csv(
            self.__in_path / "results" / self.__get_info_csv(), sep="\t"
        )
        record_iter = SeqIO.parse(in_path / self.__get_input_filename(), "fasta")

        accession_to_organism = dict(
            zip(df_records_info["accession"].values, df_records_info["organism"].values)
        )

        records_grouped = {}  # {"Magnolia coco":[SeqRecord1, SeqRecord2], "taxon 2": [SeqRecord1], ...}
        records_consensus = {}  # {"Magnolia coco": "AATTCCGG", "taxon 2": "AATCGCCTT", ...}

        for record in record_iter:
            accession = record.description.split("|")[0].split(":")[0]
            organism = accession_to_organism.get(accession, "")
            if not organism:
                continue
            organism = organism.replace(" ", "_")
            records_grouped.setdefault(organism, [])
            records_grouped[organism].append(record)

        from concurrent.futures import ThreadPoolExecutor, as_completed

        taxon_list = [
            (taxon, records)
            for taxon, records in records_grouped.items()
            if len(records) > 3
        ]
        total_taxa = len(taxon_list)

        for taxon, records in taxon_list:
            records_path = tmp_path / f"{taxon}.fasta"
            if records_path.exists() and records_path.stat().st_size > 0:
                continue
            else:
                SeqIO.write(records, records_path, "fasta")

        create_folder(f"{tmp_path}/msa")

        def run_mafft_and_rename(taxon):
            import subprocess

            msa_file = tmp_path / "msa" / f"{taxon}_msa.fasta"
            if msa_file.exists():
                if msa_file.stat().st_size == 0:
                    msa_file.unlink()
                else:
                    return taxon

            in_file = tmp_path / f"{taxon}.fasta"
            out_file = tmp_path / "msa" / f"{taxon}_msa.fasta"
            temp_out = tmp_path / "msa" / f"{taxon}_msa_temp.fasta"

            in_file_str = in_file.as_posix()
            temp_out_str = temp_out.as_posix()
            mafft_exe_str = Path(_get_mafft_exe()).as_posix()

            commandstr = (
                f'"{mafft_exe_str}" --auto --quiet "{in_file_str}" > "{temp_out_str}"'
            )

            result = subprocess.run(
                commandstr, shell=True, capture_output=True, text=True
            )

            if result.returncode != 0:
                raise RuntimeError(f"MAFFT failed: {result.stderr}")

            if temp_out.exists():
                temp_out.rename(out_file)

            return taxon

        completed = 0
        with ThreadPoolExecutor(
            max_workers=min(total_taxa, 12, os.cpu_count())
        ) as executor:
            futures = {
                executor.submit(run_mafft_and_rename, taxon): taxon
                for taxon, _ in taxon_list
            }
            for future in as_completed(futures):
                taxon = future.result()
                completed += 1
                print(f"MAFFT: {completed}/{total_taxa} - {taxon}")

        def remove_insertion(taxon):
            temp_output_file = tmp_path / "msa" / f"{taxon}_msa.fasta"
            self.__remove_minor_large_insertion(
                temp_output_file,
                length_threshold=length_threshold,
                taxa_threshold=taxa_threshold,
                keep_tmp=self.DEBUG_MODE,
            )
            consensus_sequence = self.__nt_calculator.get_consensus_sequence(
                SeqIO.parse(temp_output_file, "fasta")
            )
            return taxon, consensus_sequence

        completed = 0
        with ThreadPoolExecutor(
            max_workers=min(total_taxa, 12, os.cpu_count())
        ) as executor:
            futures = {
                executor.submit(remove_insertion, taxon): taxon
                for taxon, _ in taxon_list
            }
            for future in as_completed(futures):
                taxon, consensus_sequence = future.result()
                records_consensus[taxon] = consensus_sequence
                completed += 1
                if completed % 100 == 0 and completed != total_taxa:
                    print(f"Consensus: {completed}/{total_taxa} - {taxon}")

        self.__taxa_consensus_dict = records_consensus

    def __evaluate_seq(self):
        """get [max_num] most longest sequence of each taxon and save
        ----------
        Parameters
        - int max_num - the number of seqs that are chosen to consider
        """
        ## STEP 1: load blast result
        blast_result = self.__out_path / "results" / self.__get_input_filename()
        record_iter = SeqIO.parse(blast_result, "fasta")
        df_records_info = pd.read_csv(
            self.__in_path / "results" / self.__get_info_csv(), sep="\t"
        )

        ## STEP 6: store information of records chosen
        # substep 1: get info (that will be used for filtering) from original blast result text file
        blast_result_txt = self.__in_path / "results/blast_results.txt"
        df_blast_info = pd.read_csv(
            blast_result_txt,
            sep="\t",
            usecols=["subject_acc.ver", "sum_hits_score", "Source"],
        )

        seq_info_txt = self.__in_path / "results/blast_results_checked_seq_info.txt"
        df_seq_info = pd.read_csv(
            seq_info_txt,
            sep="\t",
            usecols=["accession", "date", "journal", "specimen_voucher"],
        )
        df_seq_info.rename(columns={"accession": "subject_acc.ver"}, inplace=True)

        df_blast_info = pd.merge(
            df_blast_info, df_seq_info, on="subject_acc.ver", how="left"
        )

        # substep 2: create a file consisting of acc_num and taxon_name
        record_taxon_info = []

        accession_to_organism = dict(
            zip(df_records_info["accession"].values, df_records_info["organism"].values)
        )

        record_iter = sorted(
            list(SeqIO.parse(blast_result, "fasta")),
            key=lambda record: accession_to_organism.get(
                record.description.split("|")[0].split(":")[0], ""
            ),
        )
        curr_taxon = ""
        consensus_msa_path = self.__in_path / "tmp_files/consensus_calculation/msa"

        for record in record_iter:
            subject_acc_ver = str(record.description.split("|")[0].split(":")[0])
            organism = accession_to_organism.get(subject_acc_ver, "")
            if not organism:
                organism = ""
            else:
                organism = organism.replace(" ", "_")
            record_length = self.__get_length_without_wobble(
                record
            )  # length without wobble

            if (
                organism in self.__taxa_consensus_dict.keys()
                and self.__count_consensus_value
            ):
                if curr_taxon != organism:
                    aligned_record_iter = list(
                        SeqIO.parse(
                            consensus_msa_path / f"{organism}_msa.fasta", "fasta"
                        )
                    )
                    curr_taxon = organism
                matching_records = [
                    record
                    for record in aligned_record_iter
                    if record.description.split("|")[0].split(":")[0] == subject_acc_ver
                ]
                if matching_records:
                    aligned_record = matching_records[0]
                    consensus_value = self.__nt_calculator.calculate_PI(
                        aligned_record,
                        self.__taxa_consensus_dict[organism],
                        [0, len(aligned_record)],
                        [0, len(aligned_record)],
                    )
                else:
                    consensus_value = -1

            else:
                consensus_value = -1

            record_taxon_info.append(
                [subject_acc_ver, organism, record_length, consensus_value]
            )

        df_taxon_name = pd.DataFrame(
            record_taxon_info,
            columns=[
                "subject_acc.ver",
                "taxon_name",
                "record_length",
                "consensus_value",
            ],
        )

        # substep 3: merge two tables (and change the order of columns)
        df_blast_info = df_blast_info.merge(df_taxon_name)
        column_order = [
            "subject_acc.ver",
            "taxon_name",
            "date",
            "journal",
            "specimen_voucher",
            "consensus_value",
            "sum_hits_score",
            "Source",
            "record_length",
        ]
        df_blast_info = df_blast_info[column_order]  # change the order of columns
        df_blast_info.to_csv(
            self.__tmp_path / "blast_result_long.txt", index=False, sep="\t"
        )

    def __select_seqs_to_keep(
        self, voucher_info_required=1, publish_required=2, newest=3
    ):
        """select sequences from each taxon according to all criteria and write into tsv
        only default is implemented in current version:
        ones with highest consensus value first,
        then ones with voucher info,
        then ones with published info,
        then ones that is updated most recently,
        then ones that are longer and has higher sum_hits_score, and are found during earilier blast iertations
        """
        ## STEP 1: load input parameter
        blast_result_long_txt = self.__tmp_path / "blast_result_long.txt"
        df = pd.read_csv(blast_result_long_txt, sep="\t")
        df["specimen_voucher"] = df["specimen_voucher"].fillna("unknown")
        creteria = {
            "date": newest,
            "journal": publish_required,
            "specimen_voucher": voucher_info_required,
        }
        creteria = dict(
            sorted(creteria.items(), key=lambda item: item[1])
        )  # sort by dict.values()
        for key, value in creteria.items():
            if not value:
                del creteria[key]
        creteria = list(creteria.keys())

        if "specimen_voucher" in creteria:
            df.loc[
                df["specimen_voucher"].str.lower() == "unknown", "specimen_voucher"
            ] = "       "

        if "journal" in creteria:
            unpublished = ["unknown", "unpublished", "published only in database"]
            pattern = "|".join(unpublished)
            mask = df["journal"].str.lower().str.contains(pattern, na=False)
            df.loc[mask, "journal"] = "       "

        if "date" in creteria:
            df["date_f"] = pd.to_datetime(
                df["date"], dayfirst=True, format="%d/%m/%Y", errors="coerce"
            )

        ## STEP 2: for each sequence, get rank of non_gap_length, sum_hits_score
        """
        column_order = ["subject_acc.ver", "taxon_name", "date", "journal", "specimen_voucher",
                        "consensus_value", "sum_hits_score", "Source", "record_length",
                        "Rank_sum_hits_score", "Rank_source", "Rank_record_length", "Sum_of_rank"]"""

        df["Rank_sum_hits_score"] = df["sum_hits_score"].rank(
            ascending=False, method="average"
        )
        df["Rank_source"] = df["Source"].rank(ascending=True, method="average")
        df["Rank_record_length"] = df["record_length"].rank(
            ascending=False, method="average"
        )
        df["Sum_of_rank"] = df[["Rank_sum_hits_score", "Rank_record_length"]].sum(
            axis=1
        )

        ## STEP 3: keep only one sequence for every taxon, the kept sequence has the largest sum of rank
        keeping_frame_list = []
        name_list = list(set(list(df["taxon_name"])))
        for organism in name_list:
            df_organism = df.loc[df["taxon_name"] == organism]

            if not not self.__count_consensus_value:
                smallest_sum_of_rank = min(df_organism["Sum_of_rank"])
                df_organism = df_organism.loc[
                    df_organism["Sum_of_rank"] == smallest_sum_of_rank
                ]

            ## substep 1: try searching for a seq with the highest consensus value
            max_consensus_value = max(df_organism["consensus_value"])
            df_organism = df_organism.loc[
                df_organism["consensus_value"] == max_consensus_value
            ]

            if df_organism.shape[0] == 1:
                keeping_frame_list.append(df_organism)
                continue

            ## substep 2: if there are multiple seqs with highest consensus value, select according to "creteria"
            df_organism = self.__filter_on_voucher_info(df_organism)
            if df_organism.shape[0] == 1:
                keeping_frame_list.append(df_organism)
                continue

            df_organism = self.__filter_on_journal_info(df_organism)
            if df_organism.shape[0] == 1:
                keeping_frame_list.append(df_organism)
                continue

            df_organism = self.__filter_on_date_info(df_organism)
            if df_organism.shape[0] == 1:
                keeping_frame_list.append(df_organism)
                continue

            ## substep 3: if there are still more than one, select according to ranks
            df_organism.sort_values(by="Sum_of_rank", ascending=True, inplace=True)
            df_organism.drop_duplicates(subset="taxon_name", keep="first", inplace=True)
            keeping_frame_list.append(df_organism)

        df = pd.concat(keeping_frame_list)
        df.drop("date_f", axis=1, inplace=True)

        ## STEP 4: save to blast_result_kept.txt
        blast_result_kept_txt = self.__tmp_path / "blast_result_kept.txt"
        df.to_csv(blast_result_kept_txt, sep="\t", index=False)
        blast_result_kept_txt = self.__out_path / "results" / "blast_result_kept.txt"
        df.to_csv(blast_result_kept_txt, sep="\t", index=False)

    @staticmethod
    def __filter_on_voucher_info(df):
        """if all records have no voucher info, do nothing, else delete ones without voucher info
        ----------
        Parameters
        - df - the dataframe of an organism that is to be filtered
        -------
        Returns
        - df - the filtered dataframe
        """
        voucher_set = set(df["specimen_voucher"])
        if voucher_set == {"       "}:
            return df
        else:
            df = df.loc[df["specimen_voucher"] != "       "]
            return df

    @staticmethod
    def __filter_on_journal_info(df):
        """if all records have no publication info, do nothing, else delete ones without publication info
        ----------
        Parameters
        - df - the dataframe of an organism that is to be filtered
        -------
        Returns
        - df - the filtered dataframe
        """
        journal_set = set(df["journal"])
        if journal_set == {"       "}:
            return df
        else:
            df = df.loc[df["journal"] != "       "]
            return df

    @staticmethod
    def __filter_on_date_info(df):
        """sort dataframe by date info
        ----------
        Parameters
        - df - the dataframe of an organism that is to be filtered
        -------
        Returns
        - df - the filtered dataframe
        """
        max_date = max(df["date_f"])
        if pd.isna(max_date):
            return df
        df = df.loc[df["date_f"] == max_date]
        return df

    def __save_selected_seqs(self):
        """save only the selected sequences into fasta according to the saved csv"""
        # load related files
        blast_result = self.__out_path / "results" / self.__get_input_filename()
        record_iter = SeqIO.parse(blast_result, "fasta")
        df_records_info = pd.read_csv(
            self.__in_path / "results" / self.__get_info_csv(), sep="\t"
        )

        blast_result_long_txt = self.__tmp_path / "blast_result_kept.txt"
        df = pd.read_csv(blast_result_long_txt, sep="\t", usecols=["subject_acc.ver"])
        keeping_list = list(df["subject_acc.ver"])

        # select and write
        name_error_log = self.__out_path / "name_error.txt"
        if name_error_log.is_file():
            name_error_log.unlink()

        keeping_records = []
        for record in record_iter:
            acc = record.description.split("|")[0].split(":")[0]
            if acc in keeping_list:
                description_list = record.description.split("|")
                accession = description_list[0].split(":")[0]
                organism = list(
                    df_records_info.loc[df_records_info["accession"] == accession][
                        "organism"
                    ]
                )[0]
                organism = organism.replace(" ", "_")

                description_list[1] = organism
                record.description = "|".join(description_list)
                record.id = record.description.split(" ")[0]
                record.name = record.id

                try:
                    record.description.encode("gbk")
                    keeping_records.append(record)
                except Exception:
                    f_err = open(name_error_log, "a")
                    msg = f"{accession}: 'gbk' can't encode description of {accession}"
                    f_err.write(msg)
                    f_err.close()

        self.keeping_records = keeping_records

        filtered_records = self.__out_path / "results" / "blast_results_filtered.fasta"
        SeqIO.write(keeping_records, filtered_records, "fasta")

        # write log file
        msg = "Most qualified sequence for each taxon is saved to 'blast_results_filtered.fasta'"
        print(f"{msg}")

    ## ===========================================================================================================
    ## ================================== for <func> control_extension ===========================================

    @staticmethod
    def __get_upper_taxonomic_unit(this_taxonomy, info_list):
        """get the upper taxonomic group of the given taxonomy, for example given Magnolia, return Magnoliaceae
        ----------
        Parameters
        - this_taxonomy - the taxonomy whose upper group is to be returned
        - info_list - the information list of taxonomy, in table blast_results_checked_seq_info.txt
        -------
        Returns
        - upper_taxonomy - the name of upper taxonomic group.
        """
        for info in info_list:
            groups = info.split("|")
            for i in range(1, len(groups)):
                if this_taxonomy == groups[-i]:
                    for j in range(i + 1, len(groups)):
                        if " " not in groups[-j]:
                            upper_taxonomy = info.split("|")[-j]
                            return upper_taxonomy

    def __split_by_genus(self):
        """split the fasta file according to genus of the records"""
        from functional import create_folder

        in_path = self.__in_path / "results" / "blast_results_checked.fasta"
        out_path = (
            self.__out_path / "tmp_files" / "extension_control" / "split_by_genus"
        )
        create_folder(out_path)

        taxonomy_df = pd.read_csv(
            self.__in_path / "results" / self.__get_info_csv(),
            usecols=["accession", "taxonomy"],
            sep="\t",
        )
        taxonomy_dict = dict(zip(taxonomy_df["accession"], taxonomy_df["taxonomy"]))
        record_iter = SeqIO.parse(in_path, "fasta")
        genus_dict = {}
        skipped = 0
        for record in record_iter:
            accession_number = record.description.split("|")[0].split(":")[0]
            if accession_number not in taxonomy_dict:
                skipped += 1
                continue
            genus = [
                unit
                for unit in taxonomy_dict[accession_number].split("|")
                if " " not in unit
            ][-1]
            genus_dict.setdefault(genus, [])
            genus_dict[genus].append(record)

        for genus, species_list in genus_dict.items():
            SeqIO.write(species_list, out_path / f"{genus}.fasta", "fasta")

        total = sum(len(v) for v in genus_dict.values())
        print(
            f"Split into {len(genus_dict)} genera, {total} sequences "
            f"({skipped} skipped due to missing taxonomy)."
        )

    def __split_by_length(self, length_ratio=0.6):
        """split the fastas (previously split by genus) according to relative length of the records
        ----------
        Parameters
        - length_ratio - records longer than this ratio will be decided as "longer" sequences
        """
        from functional import create_folder

        in_path = self.__in_path / "tmp_files" / "extension_control" / "split_by_genus"
        out_path = (
            self.__out_path / "tmp_files" / "extension_control" / "split_by_length"
        )
        create_folder(out_path)

        for file_path in in_path.iterdir():
            if not file_path.is_file():
                continue
            # file = file_path.name
            genus = file_path.stem

            length_list = []
            record_iter = SeqIO.parse(file_path, "fasta")
            for record in record_iter:
                length_list.append(len(record.seq))
            max_length = max(length_list)
            length_threshold = max_length * length_ratio

            longer_records = []
            shorter_records = []
            record_iter = SeqIO.parse(file_path, "fasta")
            for record in record_iter:
                length = len(record.seq)
                if length > length_threshold:
                    longer_records.append(record)
                else:
                    shorter_records.append(record)

            SeqIO.write(longer_records, out_path / f"{genus}_longer.fasta", "fasta")
            if len(shorter_records) > 0:
                SeqIO.write(
                    shorter_records, out_path / f"{genus}_shorter.fasta", "fasta"
                )

    def __split_large_subset(self, max_size=200):
        """split the fastas (previously split by genus and length) according to number of the records
        ----------
        Parameters
        - max_size - fasta contains more than [max_size] records will be split into smaller ones
        """
        from functional import create_folder

        self.__quality_control_max_size_subset = max_size
        in_path = self.__in_path / "tmp_files" / "extension_control" / "split_by_length"
        out_path = (
            self.__out_path
            / "tmp_files"
            / "extension_control"
            / f"split_max_{max_size}"
        )
        create_folder(out_path)

        for file_path in in_path.iterdir():
            if not file_path.is_file():
                continue
            records = list(SeqIO.parse(file_path, "fasta"))
            total_size = len(records)

            if total_size > max_size:
                num_subset = total_size // max_size + 1
                sub_size = int(total_size / num_subset)

                for i in range(num_subset):
                    sub_records = records[i * sub_size : (i + 1) * sub_size]
                    sub_filename = f"{file_path.stem}_{i}.fasta"
                    SeqIO.write(sub_records, out_path / sub_filename, "fasta")

            else:
                shutil.copyfile(file_path, out_path / file_path.name)

    def __align_subset(self, add_threshold=5):
        import subprocess

        """align the subsets
        ----------
        Parameters
        - add_threshold - files contain seqs less than this number will use --add (refer to another MSA)
        """

        in_path = self.__in_path / "tmp_files" / "extension_control" / "split_by_genus"
        out_path = self.__out_path / "tmp_files" / "extension_control" / "subset_MSA"
        create_folder(out_path)

        file_list = [
            f.name
            for f in in_path.iterdir()
            if f.is_file() and f.suffix in [".fasta", ".fas", ".fa"]
        ]
        if not file_list:
            return

        file_waiting_list = []
        for file in file_list:
            file_abs_path = in_path / file
            file_out_path = out_path / f"{Path(file).stem}_MSA.fasta"

            record_count = len(list(SeqIO.parse(file_abs_path, "fasta")))

            if record_count > add_threshold:
                print(f"Aligning {file} ({record_count} seqs, --auto) ...")
                temp_output_dir = out_path / f"temp_{Path(file).stem}"
                temp_output_dir.mkdir(parents=True, exist_ok=True)

                in_file_str = file_abs_path.as_posix()
                out_file = temp_output_dir / file
                out_file_str = out_file.as_posix()
                mafft_exe_str = Path(_get_mafft_exe()).as_posix()

                commandstr = f'"{mafft_exe_str}" --auto --thread -1 --reorder "{in_file_str}" > "{out_file_str}"'

                result = subprocess.run(
                    commandstr, shell=True, capture_output=True, text=True
                )

                if result.returncode != 0:
                    raise RuntimeError(f"MAFFT failed: {result.stderr}")

                if out_file.exists():
                    shutil.move(str(out_file), str(file_out_path))
                if temp_output_dir.exists():
                    shutil.rmtree(temp_output_dir)
                #print(f"Aligned {file}.")
            else:
                file_waiting_list.append(file)

        if not file_waiting_list:
            return

        df_taxonomy = pd.read_csv(
            self.__in_path / "results" / self.__get_info_csv(), sep="\t"
        )
        taxonomy_genus_and_above = list(
            set(list(map(lambda x: x[: x.rindex("|")], df_taxonomy["taxonomy"])))
        )

        def _aligned_path(file):
            return out_path / f"{Path(file).stem}_MSA.fasta"

        def _get_upper_unit(file):
            return self.__get_upper_taxonomic_unit(
                Path(file).stem.split("_")[0], taxonomy_genus_and_above
            )

        def _find_reference(file):
            """find a ready-made alignment to --add onto: same family first, then any"""
            upper_unit = _get_upper_unit(file)
            for ref_file in file_list:
                if (
                    ref_file != file
                    and _get_upper_unit(ref_file) == upper_unit
                    and _aligned_path(ref_file).exists()
                ):
                    return ref_file
            for ref_file in file_list:
                if ref_file != file and _aligned_path(ref_file).exists():
                    return ref_file
            return None

        # 轮次处理小属（--add）：同科参考尚未就绪时留到下一轮重试，
        # 从而打破小属之间互为参考的循环依赖
        pending = list(file_waiting_list)
        while pending:
            progressed = False
            still_pending = []
            for file in pending:
                reference = _find_reference(file)
                if reference is None:
                    still_pending.append(file)
                    continue

                if _get_upper_unit(reference) != _get_upper_unit(file):
                    warning_msg = (
                        f"In file {file}: there may be error in extension check "
                        "because no other genus from the same family can be used "
                        "as reference."
                    )
                    print(f"NOTE: {warning_msg}")

                print(
                    f"Aligning {file} (--add onto {Path(reference).stem}) ..."
                )
                file_abs_path = in_path / file
                file_out_path = _aligned_path(file)
                ref_aligned_path = _aligned_path(reference)

                temp_output_dir = out_path / f"temp_{Path(file).stem}"
                temp_output_dir.mkdir(parents=True, exist_ok=True)

                in_file_str = file_abs_path.as_posix()
                out_file = temp_output_dir / file
                out_file_str = out_file.as_posix()
                ref_aligned_str = ref_aligned_path.as_posix()
                mafft_exe_str = Path(_get_mafft_exe()).as_posix()

                commandstr = f'"{mafft_exe_str}" --quiet --auto --add "{ref_aligned_str}" --thread -1 --reorder "{in_file_str}" > "{out_file_str}"'

                result = subprocess.run(
                    commandstr, shell=True, capture_output=True, text=True
                )

                if result.returncode != 0:
                    raise RuntimeError(f"MAFFT --add failed: {result.stderr}")

                if out_file.exists():
                    shutil.move(str(out_file), str(file_out_path))
                if temp_output_dir.exists():
                    shutil.rmtree(temp_output_dir)
                #print(f"Aligned {file}.")
                progressed = True

            pending = still_pending
            if not progressed:
                for file in pending:
                    warning_msg = (
                        f"In file {file}: no reference alignment is available for "
                        "extension check (no other genus from the same family is "
                        "present). Skipped."
                    )
                    print(f"NOTE: {warning_msg}")
                break

    def __remove_erroneous_extension(self, gappyness_threshold=0.5):
        """remove extension if the extension part is too gappy in the MSA (so-called errorneous ones)
        ----------
        Parameters
        - gappyness_threshold - if extension with gappyness more than this number will be removed/trimmed"""
        from functional import create_folder

        print("Into removal.")
        record_ids = []

        in_path = self.__in_path / "tmp_files" / "extension_control" / "subset_MSA"
        tmp_path = self.__out_path / "tmp_files" / "extension_control"
        out_path = self.__out_path / "results"
        create_folder(tmp_path)

        blast_result_path = self.__in_path / "results" / "blast_results.txt"
        df_blast_result = pd.read_csv(
            blast_result_path, usecols=["subject_acc.ver", "s_start", "s_end"], sep="\t"
        )

        df_modification = pd.DataFrame(
            columns=[
                "subject_acc.ver",
                "new_start",
                "new_end",
                "s_new_start",
                "s_new_end",
            ]
        )
        for file_path in in_path.iterdir():
            if not file_path.is_file():
                continue
            print(f"Performing removal on {file_path.name}.")
            record_iter = SeqIO.parse(file_path, "fasta")

            for record in record_iter:
                accession_number = record.description.split(":")[0]
                info_line = df_blast_result.loc[
                    df_blast_result["subject_acc.ver"] == accession_number
                ]

                if info_line.empty:
                    print(
                        f"[ERROR] Accession {accession_number} not found in "
                        "blast_results.txt. Aborting extension control to avoid "
                        "silently dropping records. Check blast_results.txt integrity."
                    )
                    return

                s_start, s_end = info_line.iloc[0][["s_start", "s_end"]]
                s_start, s_end = min([s_start, s_end]), max([s_start, s_end])
                r_start, r_end = (
                    record.description.split("|")[0]
                    .split(":")[1]
                    .split("_")[0]
                    .split("-")
                )
                r_start, r_end = min([r_start, r_end]), max([r_start, r_end])
                s_start, s_end, r_start, r_end = list(
                    map(int, [s_start, s_end, r_start, r_end])
                )

                as_start = self.__nt_calculator.get_position_in_alignment(
                    record, max(s_start - (r_start - 1), 1), left_to_right=True
                )
                ar_start = self.__nt_calculator.get_position_in_alignment(
                    record, max(r_start - (r_start - 1), 1), left_to_right=True
                )
                as_end = self.__nt_calculator.get_position_in_alignment(
                    record, max(r_end - (s_end - 1), 1), left_to_right=False
                )
                ar_end = self.__nt_calculator.get_position_in_alignment(
                    record, max(r_end - (r_end - 1), 1), left_to_right=False
                )

                if ar_start == as_start:
                    gappyness_start = 0
                else:
                    gappyness_start = 1 - (s_start - r_start) / (as_start - ar_start)

                if ar_end == as_end:
                    gappyness_end = 0
                else:
                    gappyness_end = 1 - (r_end - s_end) / (as_end - ar_end)

                new_start, new_end = None, None
                if gappyness_start > gappyness_threshold:
                    new_start = s_start - r_start + 1
                    s_new_start = s_start
                if gappyness_end > gappyness_threshold:
                    new_end = s_end - r_start + 1
                    s_new_end = s_end
                if any([new_start, new_end]):
                    record_ids.append(accession_number)
                    if new_start is None:
                        new_start = 1
                        s_new_start = r_start
                    if new_end is None:
                        new_end = r_end - r_start + 1
                        s_new_end = r_end

                    position_modification = [
                        accession_number,
                        new_start,
                        new_end,
                        s_new_start,
                        s_new_end,
                    ]
                    df_modification.loc[len(df_modification.index)] = (
                        position_modification
                    )

        df_modification.to_csv(tmp_path / "modification.txt", index=False, sep="\t")

        blast_result_checked = (
            self.__in_path / "results" / "blast_results_checked.fasta"
        )
        existing_accession = []
        new_records = []
        records_to_trim = list(df_modification["subject_acc.ver"])
        record_iter = SeqIO.parse(blast_result_checked, "fasta")
        for record in record_iter:
            accession_number = record.description.split(":")[0]
            if accession_number in existing_accession:
                continue
            else:
                existing_accession.append(accession_number)

            if accession_number in records_to_trim:
                info_line = df_modification.loc[
                    df_modification["subject_acc.ver"] == accession_number
                ]
                start, end, s_start, s_end = info_line.iloc[0][
                    ["new_start", "new_end", "s_new_start", "s_new_end"]
                ]
                record.seq = record.seq[start - 1 : end]
                record.description = re.sub(
                    r"\d+-\d+", f"{s_start}-{s_end}", record.description, count=1
                )
                record.id = record.description.split(" ")[0]
                record.name = record.id
                new_records.append(record)
            else:
                new_records.append(record)

        print("[SUCCESS] Extension control finished.")
        new_records.sort(key=lambda x: x.description)
        SeqIO.write(new_records, out_path / "blast_results_controlled.fasta", "fasta")
        print(
            "[SUCCESS] Alignment control finished. See blast_results_controlled.fasta for details."
        )
