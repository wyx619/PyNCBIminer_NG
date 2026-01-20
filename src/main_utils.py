# *-* coding:utf-8 *-*
import sys
import threading
from pathlib import Path

from PySide6.QtCore import Qt, Signal, QObject, QDate
from qfluentwidgets import InfoBar, InfoBarPosition


def get_resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except AttributeError:
        base_path = str(Path(__file__).parent)
    return str(Path(base_path) / relative_path)


def get_writable_path(relative_path):
    return str(Path.cwd() / relative_path)


class BackendController(QObject):
    log_signal = Signal(str)
    infobar_signal = Signal(str, str)  # level, message
    count_signal = Signal(int)  # search results count

    def __init__(self):
        super().__init__()

    def emit_log(self, message, level="INFO"):
        self.log_signal.emit(f"[{level}] {message}\n")
        self.infobar_signal.emit(level, message)

    def save_settings(self, retrieval_interface, parent_window):
        # Use new_region_edit if it has text, otherwise use combo box
        new_region = retrieval_interface.new_region_edit.text().strip()
        if new_region:
            target_region = new_region
        else:
            target_region = retrieval_interface.combo_region.currentText()
        
        if target_region.strip() == "":
            InfoBar.warning(
                title="Warning", 
                content="Please input region name.", 
                parent=parent_window,
                position=InfoBarPosition.TOP,
                duration=5000
            )
            return

        # Determine save location: same as where it was loaded from
        blast_params_dir = Path(get_writable_path("blast_parameters"))
        default_params_dir = Path(get_resource_path("blast_parameters"))
        custom_params_file = blast_params_dir / Path(target_region + ".txt")
        default_params_file = default_params_dir / Path(target_region + ".txt")
        
        # Save to the same location it was loaded from
        if custom_params_file.exists():
            params_file = custom_params_file
            blast_params_dir.mkdir(parents=True, exist_ok=True)
        else:
            params_file = default_params_file

        key_annotations = retrieval_interface.key_anno.toPlainText().strip().replace("; ", "|")

        with open(params_file, "w") as fw:
            fw.write(f"target_region\t{target_region}\n")
            fw.write(
                f"entrez_qualifier\t{retrieval_interface.entrez_qualifier.toPlainText().strip()}\n"
            )
            fw.write(f"max_length\t{retrieval_interface.max_len.text().strip()}\n")
            fw.write(f"key_annotations\t{key_annotations.replace(';', '|')}\n")
            fw.write(
                f"exclude_sources\t{retrieval_interface.excl_source.toPlainText().strip().replace(chr(10), '|')}\n"
            )
            fw.write(f"expect_value\t{retrieval_interface.expect_val.text().strip()}\n")
            fw.write(f"gap_costs\t{retrieval_interface.gap_costs.text().strip()}\n")
            fw.write(f"word_size\t{retrieval_interface.word_size.text().strip()}\n")
            fw.write(f"nucl_reward\t{retrieval_interface.nucl_reward.text().strip()}\n")
            fw.write(
                f"nucl_penalty\t{retrieval_interface.nucl_penalty.text().strip()}\n"
            )
            if retrieval_interface.date_from.date.isValid():
                fw.write(
                    f"date_from\t{retrieval_interface.date_from.date.toString('yyyy/MM/dd')}\n"
                )
            if retrieval_interface.date_to.date.isValid():
                fw.write(
                    f"date_to\t{retrieval_interface.date_to.date.toString('yyyy/MM/dd')}\n"
                )

        initial_queries = retrieval_interface.init_queries.toPlainText().strip()
        
        # Save initial_queries to the same location as loaded from
        initial_queries_dir = Path(get_writable_path("initial_queries"))
        custom_queries_dir = initial_queries_dir / Path(target_region)
        default_queries_dir = Path(get_resource_path("initial_queries")) / Path(target_region)
        
        if custom_queries_dir.exists():
            queries_dir = custom_queries_dir
        else:
            queries_dir = default_queries_dir
        
        queries_dir.mkdir(parents=True, exist_ok=True)

        with open(queries_dir / Path(target_region + ".fasta"), "w") as fw:
            fw.write(initial_queries)

        if retrieval_interface.combo_region.findText(target_region) == -1:
            retrieval_interface.combo_region.addItem(target_region)

        retrieval_interface.combo_region.setCurrentText(target_region)
        retrieval_interface.new_region_edit.clear()  # Clear the new region input
        retrieval_interface.btn_save_settings.setEnabled(False)
        retrieval_interface.btn_set_region.setEnabled(True)
        InfoBar.success(
            title="Saved",
            content=f"Settings saved for {target_region}",
            parent=parent_window,
        )

    def my_esearch(self, retrieval_interface):
        from my_entrez import entrez_count, entrez_summary

        taxonomy = retrieval_interface.tax_edit.toPlainText().strip()
        email = retrieval_interface.email_edit.text().strip()
        qualifier = retrieval_interface.entrez_qualifier.toPlainText().strip()
        
        if taxonomy == "":
            self.emit_log("Please input your target groups.", "WARNING")
        if email == "":
            self.emit_log("Please input your email address.", "WARNING")
        if qualifier == "":
            self.emit_log("Please input your Entrez qualifier.", "WARNING")
        
        if taxonomy == "" or email == "" or qualifier == "":
            return
        
        organisms = [x for x in taxonomy.splitlines() if len(x) > 0]
        
        date_from_obj = retrieval_interface.date_from.date
        date_to_obj = retrieval_interface.date_to.date

        d_from = ""
        d_to = ""

        if not retrieval_interface.date_from_cleared:
            d_from = date_from_obj.toString("yyyy/MM/dd")
        if not retrieval_interface.date_to_cleared:
            d_to = date_to_obj.toString("yyyy/MM/dd")

        if d_from and not d_to:
            d_to = QDate.currentDate().toString("yyyy/MM/dd")
        elif not d_from and d_to:
            InfoBar.warning(
                title="Warning",
                content="Please select 'Date From' or clear 'Date To'",
                parent=retrieval_interface.window(),
                position=InfoBarPosition.TOP,
                duration=3000,
            )
            return

        self.emit_log("Starting Entrez Search...")

        if retrieval_interface.chk_summary.isChecked():
            target_region_list = [
                f.name for f in Path(get_resource_path("blast_parameters")).iterdir()
            ]
            target_region_list = [Path(x).stem for x in target_region_list]
            target_region_dict = {}
            for target_region in target_region_list:
                parameters_dict = {}
                with open(
                    Path(get_resource_path("blast_parameters"))
                    / Path(target_region + ".txt"),
                    "r",
                ) as fr:
                    parameters = fr.read().splitlines()
                    for parameter in parameters:
                        if parameter.strip() != "":
                            parameters_dict[parameter.split("\t")[0]] = str(
                                parameter.split("\t")[1]
                            )
                target_region_dict[target_region] = parameters_dict["entrez_qualifier"]

            thread = threading.Thread(
                target=entrez_summary,
                args=(email, organisms, target_region_dict, d_from, d_to),
            )
        else:
            def count_callback(count):
                self.count_signal.emit(count)
            
            thread = threading.Thread(
                target=entrez_count, args=(email, organisms, qualifier, d_from, d_to, count_callback)
            )

        thread.daemon = True
        thread.start()

    def submit_new_blast(self, retrieval_interface):
        taxonomy = retrieval_interface.tax_edit.toPlainText().strip()
        email = retrieval_interface.email_edit.text().strip()
        qualifier = retrieval_interface.entrez_qualifier.toPlainText().strip()
        wd = retrieval_interface.wd_edit.text().strip()
        
        if taxonomy == "":
            self.emit_log("Please input your target groups.", "WARNING")
        if email == "":
            self.emit_log("Please input your email address.", "WARNING")
        if qualifier == "":
            self.emit_log("Please input your Entrez qualifier.", "WARNING")
        if wd == "":
            self.emit_log("Please input your working directory path.", "WARNING")
        
        if taxonomy == "" or email == "" or qualifier == "" or wd == "":
            return
        
        self.emit_log("Submitting New BLAST...")

        if not wd or not Path(wd).exists():
            try:
                Path(wd).mkdir(parents=True, exist_ok=True)
            except Exception as e:
                self.emit_log(f"Error creating working directory: {e}", "ERROR")
                return

        try:
            pass  # max_len = int(retrieval_interface.max_len.text().strip())
        except ValueError as e:
            self.emit_log(f"Value Error: {e}", "ERROR")
            return

        (Path(wd) / "parameters" / "ref_seq").mkdir(parents=True, exist_ok=True)
        (Path(wd) / "parameters" / "ref_msa").mkdir(parents=True, exist_ok=True)
        (Path(wd) / "tmp_files").mkdir(exist_ok=True)
        (Path(wd) / "results").mkdir(exist_ok=True)

        self.emit_log("BLAST thread started (mock).")

    def load_previous_job(self, retrieval_interface, parent_window):
        """
        read BLAST parameters in blast_parameters.txt file
        connects with load_previous_job button in Sequence Retrieving module
        :return:
        """
        from iterated_blast import iterated_blast_main
        # check if working directory path is empty
        wd = retrieval_interface.wd_edit.text().strip()
        if wd == "":
            self.emit_log("Please input your working directory path.", "WARNING")
            return
        
        print_line("*")
        self.emit_log("Loading previous job...")
        
        # check if working directory exists
        if not Path(wd).exists():
            self.emit_log("Working directory does not exist, please submit new BLAST.", "WARNING")
            return
        if not (Path(wd) / "parameters").exists():
            self.emit_log("Can't find parameters directory, please submit new BLAST.", "WARNING")
            return
        if not (Path(wd) / "tmp_files").exists():
            self.emit_log("Can't find tmp_files directory, please submit new BLAST.", "WARNING")
            return
        if not (Path(wd) / "results").exists():
            self.emit_log("Can't find results directory, please submit new BLAST.", "WARNING")
            return

        # read BLAST parameters in blast_parameters.txt file
        parameters_files = [f.name for f in (Path(wd) / "parameters").iterdir()]
        if "blast_parameters.txt" not in parameters_files:
            self.emit_log("Can't find BLAST parameters, please submit new BLAST.", "WARNING")
            return
        if "initial_queries.fasta" not in parameters_files:
            self.emit_log("Can't find initial queries, please submit new BLAST.", "WARNING")
            return
        else:
            retrieval_interface.init_queries.clear()
            with open(
                Path(wd) / Path("parameters") / Path("initial_queries.fasta"), "r"
            ) as fr:
                seq = fr.read()
                retrieval_interface.init_queries.setPlainText(seq)

        parameters_dict = {}
        with open(
            Path(wd) / Path("parameters") / Path("blast_parameters.txt"), "r"
        ) as fr:
            parameters = fr.read().splitlines()
            for parameter in parameters:
                if parameter.strip() != "":
                    parameters_dict[parameter.split("\t")[0]] = str(
                        parameter.split("\t")[1]
                    )

        target_region = parameters_dict.get("target_region", "")
        taxonomy = parameters_dict.get("taxonomy", "")
        entrez_qualifier = parameters_dict.get("entrez_qualifier", "")
        date_from = parameters_dict.get("date_from", "")
        date_to = parameters_dict.get("date_to", "")
        entrez_email = parameters_dict.get("entrez_email", "")
        count = parameters_dict.get("entrez_count", "0")
        try:
            max_length = int(parameters_dict.get("max_length", "0"))
        except ValueError:
            max_length = 0
        key_annotations = parameters_dict.get("key_annotations", "")
        exclude_sources = parameters_dict.get("exclude_sources", "")
        expect_value = parameters_dict.get("expect_value", "")
        gap_costs = parameters_dict.get("gap_costs", "")
        word_size = parameters_dict.get("word_size", "")
        nucl_reward = parameters_dict.get("nucl_reward", "")
        nucl_penalty = parameters_dict.get("nucl_penalty", "")

        # show parameters in the Sequence Retrieving panel
        target_region_list = [
            f.name for f in Path(get_resource_path("blast_parameters")).iterdir()
        ]
        target_region_list = [Path(x).stem for x in target_region_list]
        if target_region in target_region_list:
            target_region_list.remove(target_region)
        target_region_list.insert(0, "")
        target_region_list.insert(0, target_region)
        retrieval_interface.combo_region.clear()
        retrieval_interface.combo_region.addItems(target_region_list)
        retrieval_interface.tax_edit.setPlainText(
            taxonomy.replace("|", "\n") if taxonomy else ""
        )
        retrieval_interface.entrez_qualifier.setPlainText(entrez_qualifier)

        if date_from:
            date_obj = QDate.fromString(date_from, "yyyy/MM/dd")
            if date_obj.isValid():
                retrieval_interface.date_from.setDate(date_obj)
        if date_to:
            date_obj = QDate.fromString(date_to, "yyyy/MM/dd")
            if date_obj.isValid():
                retrieval_interface.date_to.setDate(date_obj)

        retrieval_interface.email_edit.setText(entrez_email)
        retrieval_interface.max_len.setText(str(max_length))
        retrieval_interface.expect_val.setText(str(expect_value))
        retrieval_interface.gap_costs.setText(gap_costs)
        retrieval_interface.word_size.setText(str(word_size))
        retrieval_interface.nucl_reward.setText(str(nucl_reward))
        retrieval_interface.nucl_penalty.setText(str(nucl_penalty))
        retrieval_interface.key_anno.setPlainText(key_annotations.replace("|", "; "))
        retrieval_interface.excl_source.setPlainText(exclude_sources.replace("|", "\n"))

        organisms = taxonomy.split("|")
        organisms = [x for x in organisms if len(x) > 0]
        key_annotations_list = key_annotations.split("|")
        key_annotations_list = [x for x in key_annotations_list if len(x) > 0]
        exclude_sources_list = exclude_sources.split("|")
        exclude_sources_list = [x for x in exclude_sources_list if len(x) > 0]

        ref_seq_dir = Path(wd) / "parameters" / "ref_seq"
        if ref_seq_dir.exists() and any(ref_seq_dir.iterdir()):
            queries_file_list = [f.name for f in ref_seq_dir.iterdir()]
            round_list = []
            for queries_file in queries_file_list:
                round_list.append(int(Path(queries_file).stem.split("_")[-1]))
            round_list.sort()
            blast_round = round_list[-1]
        else:
            blast_round = 1
        ref_number = 5
        count = int(count)

        thread = threading.Thread(
            target=iterated_blast_main,
            args=(
                wd,
                organisms,
                count,
                expect_value,
                gap_costs,
                word_size,
                nucl_reward,
                nucl_penalty,
                max_length,
                key_annotations_list,
                exclude_sources_list,
                ref_number,
                date_from,
                date_to,
                entrez_email,
                blast_round,
            ),
        )
        thread.daemon = True
        thread.start()

        retrieval_interface.btn_submit_blast.setEnabled(False)
        retrieval_interface.btn_load_job.setEnabled(False)
        InfoBar.success(
            title="Success",
            content="Previous job loaded!",
            parent=parent_window,
            position=InfoBarPosition.TOP,
        )

    def set_marker_summary(self, retrieval_interface, state):
        is_checked = (
            (state == Qt.Checked) if isinstance(state, Qt.CheckState) else (state == 2)
        )

        retrieval_interface.entrez_qualifier.setEnabled(not is_checked)
        retrieval_interface.combo_region.setEnabled(not is_checked)
        retrieval_interface.btn_save_settings.setEnabled(not is_checked)
        if is_checked:
            retrieval_interface.entrez_qualifier.clear()
            retrieval_interface.combo_region.setCurrentIndex(0)

    def set_reduce_threshold(self, construction_interface, state):
        if isinstance(state, bool):
            is_checked = state
        else:
            is_checked = (
                (state == Qt.Checked)
                if isinstance(state, Qt.CheckState)
                else (state == 2)
            )
        construction_interface.len_thresh.setEnabled(is_checked)
        construction_interface.combo_consensus.setEnabled(is_checked)

    def select_tri_method(self, construction_interface):
        method = construction_interface.combo_trim_method.currentText()
        is_user = "user defined" in method
        construction_interface.trim_gt.setEnabled(is_user)
        construction_interface.trim_st.setEnabled(is_user)
        construction_interface.trim_ct.setEnabled(is_user)
        construction_interface.trim_con.setEnabled(is_user)

    def run_filtering(self, construction_interface):
        from my_filter import call_miner_filter

        in_path = construction_interface.filter_in.text().strip()
        out_path = construction_interface.filter_out.text().strip() or in_path

        if not in_path:
            self.emit_log("Please set input path", "WARNING")
            return
        if not Path(in_path).exists():
            self.emit_log(f"Input path does not exist: {in_path}", "WARNING")
            return

        try:
            len_thr = int(construction_interface.len_thresh.text().strip())
            cons = construction_interface.combo_consensus.currentText() == "True"
        except ValueError as e:
            self.emit_log(f"Value Error: {e}", "ERROR")
            return

        action = 0
        if (
            construction_interface.switch_ext.isChecked()
            and construction_interface.switch_reduce.isChecked()
        ):
            action = 3  # both
        elif construction_interface.switch_ext.isChecked():
            action = 1  # extension only
        elif construction_interface.switch_reduce.isChecked():
            action = 2  # reduce only

        if action == 0:
            self.emit_log("Please select an option", "WARNING")
            return

        self.emit_log("Running Filter...")
        
        def emit_callback(message, level="INFO"):
            self.emit_log(message, level)
        
        thread = threading.Thread(
            target=call_miner_filter, args=(in_path, out_path, action, cons, len_thr, emit_callback)
        )
        thread.daemon = True
        thread.start()

    def run_alignment(self, construction_interface):
        from call_mafft2 import mafft

        in_path = construction_interface.align_in.text().strip()
        out_path = construction_interface.align_out.text().strip()

        if not in_path:
            self.emit_log("Please set input path", "WARNING")
            return
        if not Path(in_path).exists():
            self.emit_log(f"Input path does not exist: {in_path}", "WARNING")
            return
        if not out_path:
            self.emit_log("Please set output path", "WARNING")
            return

        if not Path(out_path).exists():
            Path(out_path).mkdir(parents=True, exist_ok=True)

        algo = construction_interface.align_algo.currentText()
        try:
            thread_num = int(construction_interface.align_thread.text().strip())
        except ValueError:
            thread_num = -1
        reorder = construction_interface.align_reorder.currentText() == "True"

        self.emit_log(f"Running MAFFT... Output: {out_path}/msa_*.fasta")
        thread = threading.Thread(
            target=mafft,
            args=(in_path, out_path, "", "", algo, thread_num, reorder, "", False, ""),
        )
        thread.daemon = True
        thread.start()

    def run_trimming(self, construction_interface):
        self.check_dependencies()
        from call_trimal import trimal

        in_path = construction_interface.trim_in.text().strip()
        out_path = construction_interface.trim_out.text().strip()

        if not in_path:
            self.emit_log("Please set input path", "WARNING")
            return
        if not Path(in_path).exists():
            self.emit_log(f"Input path does not exist: {in_path}", "WARNING")
            return
        if not out_path:
            self.emit_log("Please set output path", "WARNING")
            return

        if not Path(out_path).exists():
            Path(out_path).mkdir(exist_ok=True)

        met = construction_interface.combo_trim_method.currentText().split(" ")[0]
        if met == "user":
            met = ""

        self.emit_log("Running trimAl...")
        thread = threading.Thread(
            target=trimal,
            args=(
                in_path,
                out_path,
                True,
                False,
                met,
                construction_interface.trim_gt.text(),
                construction_interface.trim_st.text(),
                construction_interface.trim_ct.text(),
                construction_interface.trim_con.text(),
                "",
                False,
                "",
            ),
        )
        thread.daemon = True
        thread.start()

    def run_concatenation(self, construction_interface):
        from my_concatenation import my_concatenation

        in_p = construction_interface.concat_in.text().strip()
        out_p = construction_interface.concat_out.text().strip()

        if not in_p:
            self.emit_log("Please set input path", "WARNING")
            return
        if not Path(in_p).exists():
            self.emit_log(f"Input path does not exist: {in_p}", "WARNING")
            return
        if not out_p:
            self.emit_log("Please set output path", "WARNING")
            return

        self.emit_log("Running Concatenation...")
        thread = threading.Thread(target=my_concatenation, args=(in_p, out_p))
        thread.daemon = True
        thread.start()

    def run_install_mafft(self):
        from install_dependencies import install_mafft
        self.emit_log("Installing MAFFT...")
        thread = threading.Thread(target=install_mafft)
        thread.daemon = True
        thread.start()

    def run_install_trimal(self):
        from install_dependencies import install_trimal
        self.emit_log("Installing trimAl...")
        thread = threading.Thread(target=install_trimal)
        thread.daemon = True
        thread.start()

    def show_about(self, parent_window):
        InfoBar.info(
            title="PyNCBIminer-NG",
            content="Author: Ruijing Cheng & Yuxuan Wang\nLicense: GPL V3",
            orient=Qt.Vertical,
            position=InfoBarPosition.BOTTOM_RIGHT,
            duration=5000,
            parent=parent_window,
        )

    def check_dependencies(self):
        pass


def print_line(character="#"):
    print(character * 50)


def get_query_accession(record):
    parts = record.description.split(" ")[0].split("|")[0].split(":")
    # assert len(parts) == 2
    return parts[0]
