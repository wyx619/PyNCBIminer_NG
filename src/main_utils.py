# *-* coding:utf-8 *-*
import threading
from pathlib import Path

from PySide6.QtCore import QDate, QObject, Qt, Signal
from qfluentwidgets import InfoBar, InfoBarPosition, MessageBox


def get_resource_path(relative_path):
    import sys
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
        self.blast_thread = None
        self.stop_flag = threading.Event()

    def run_pga(self, in_folder, ori_gb_folder, clade, ref_folder=None):
        from Chloroplast.call_pga import run_pga as call_pga

        call_pga(in_folder, ori_gb_folder, clade, ref_folder, emit_log=self.emit_log)

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
                duration=5000,
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

        key_annotations = (
            retrieval_interface.key_anno.toPlainText().strip().replace("; ", "|")
        )

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
        default_queries_dir = Path(get_resource_path("initial_queries")) / Path(
            target_region
        )

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
        marker_summary_mode = retrieval_interface.chk_summary.isChecked()

        if taxonomy == "":
            self.emit_log("Please input your target groups.", "WARNING")
        if email == "":
            self.emit_log("Please input your email address.", "WARNING")
        if qualifier == "" and not marker_summary_mode:
            self.emit_log("Please input your Entrez qualifier.", "WARNING")

        if (
            taxonomy == ""
            or email == ""
            or (qualifier == "" and not marker_summary_mode)
        ):
            return

        organisms = [x for x in taxonomy.splitlines() if len(x) > 0]

        date_from_obj = retrieval_interface.date_from.date
        date_to_obj = retrieval_interface.date_to.date

        d_from = ""
        d_to = ""

        if not retrieval_interface.date_from_cleared and date_from_obj.isValid():
            d_from = date_from_obj.toString("yyyy/MM/dd")
        if not retrieval_interface.date_to_cleared and date_to_obj.isValid():
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
                args=(
                    email,
                    organisms,
                    target_region_dict,
                    d_from,
                    d_to,
                    self.emit_log,
                ),
            )
        else:

            def count_callback(count):
                self.count_signal.emit(count)

            thread = threading.Thread(
                target=entrez_count,
                args=(email, organisms, qualifier, d_from, d_to, count_callback),
            )

        thread.daemon = True
        thread.start()

    def submit_new_blast(self, retrieval_interface, parent_window=None):
        from iterated_blast import iterated_blast_main
        from my_entrez import entrez_count

        print("=" * 50)
        self.emit_log("Submitting New BLAST...")

        # read the current text of BLAST parameters
        target_region = retrieval_interface.combo_region.currentText()
        taxonomy = retrieval_interface.tax_edit.toPlainText().strip()
        qualifier = retrieval_interface.entrez_qualifier.toPlainText().strip()
        email = retrieval_interface.email_edit.text().strip()
        max_length = retrieval_interface.max_len.text().strip()
        key_annotations = retrieval_interface.key_anno.toPlainText().strip()
        exclude_sources = retrieval_interface.excl_source.toPlainText().strip()
        expect_value = retrieval_interface.expect_val.text().strip()
        gap_costs = retrieval_interface.gap_costs.text().strip()
        word_size = retrieval_interface.word_size.text().strip()
        nucl_reward = retrieval_interface.nucl_reward.text().strip()
        nucl_penalty = retrieval_interface.nucl_penalty.text().strip()
        initial_queries = retrieval_interface.init_queries.toPlainText().strip()
        wd = retrieval_interface.wd_edit.text().strip()
        date_from_qdate = retrieval_interface.date_from.date
        date_to_qdate = retrieval_interface.date_to.date
        marker_summary_mode = retrieval_interface.chk_summary.isChecked()

        if not retrieval_interface.date_from_cleared and date_from_qdate.isValid():
            date_from = date_from_qdate.toString("yyyy/MM/dd")
        else:
            date_from = ""

        if not retrieval_interface.date_to_cleared and date_to_qdate.isValid():
            date_to = date_to_qdate.toString("yyyy/MM/dd")
        else:
            date_to = ""

        if date_from and not date_to:
            today = QDate.currentDate()
            date_to = today.toString("yyyy/MM/dd")

        # validation
        if taxonomy == "":
            self.emit_log("Please input your target groups.", "WARNING")
        if email == "":
            self.emit_log("Please input your email address.", "WARNING")
        if qualifier == "" and not marker_summary_mode:
            self.emit_log("Please input your Entrez qualifier.", "WARNING")
        if wd == "":
            self.emit_log("Please input your working directory path.", "WARNING")
        if not date_from and date_to:
            self.emit_log("Please set date_from when date_to is specified.", "WARNING")
        if (
            taxonomy == ""
            or email == ""
            or (qualifier == "" and not marker_summary_mode)
            or wd == ""
            or (not date_from and date_to)
        ):
            return

        # max_length: positive integer
        try:
            max_length = int(max_length)
            if max_length < 0:
                self.emit_log("max_length needs to be a positive integer.", "WARNING")
                return
        except ValueError:
            self.emit_log(f"Invalid value for max_length: {max_length}.", "WARNING")
            return

        # word_size: positive integer
        try:
            word_size = int(word_size)
            if word_size < 0:
                self.emit_log("word_size needs to be a positive integer.", "WARNING")
                return
        except ValueError:
            self.emit_log(f"Invalid value for word_size: {word_size}.", "WARNING")
            return

        # expect_value: nonnegative number
        try:
            expect_value = float(expect_value)
            if expect_value < 0:
                self.emit_log(
                    "expect_value needs to be a nonnegative number.", "WARNING"
                )
                return
        except ValueError:
            self.emit_log(f"Invalid value for expect_value: {expect_value}.", "WARNING")
            return

        # nucl_reward: nonnegative integer
        try:
            nucl_reward = int(nucl_reward)
            if nucl_reward < 0:
                self.emit_log(
                    "nucl_reward needs to be a nonnegative integer.", "WARNING"
                )
                return
        except ValueError:
            self.emit_log(f"Invalid value for nucl_reward: {nucl_reward}.", "WARNING")
            return

        # nucl_penalty: nonpositive integer
        try:
            nucl_penalty = int(nucl_penalty)
            if nucl_penalty > 0:
                self.emit_log(
                    "nucl_penalty needs to be a nonpositive integer.", "WARNING"
                )
                return
        except ValueError:
            self.emit_log(f"Invalid value for nucl_penalty: {nucl_penalty}.", "WARNING")
            return

        # gap_costs: two positive integers separated by a space
        try:
            gap_costs_list = gap_costs.split(" ")
            if len(gap_costs_list) != 2:
                raise ValueError()
            cost0 = int(gap_costs_list[0])
            cost1 = int(gap_costs_list[1])
            if cost0 < 0 or cost1 < 0:
                raise ValueError()
        except (ValueError, IndexError):
            self.emit_log(f"Invalid value for gap_costs: {gap_costs}.", "WARNING")
            return

        # initial_queries validation
        if len(initial_queries) == 0:
            self.emit_log("Please add initial queries!", "WARNING")
            return

        # create directories
        if not Path(wd).exists():
            Path(wd).mkdir(parents=True, exist_ok=True)
        (Path(wd) / "parameters").mkdir(parents=True, exist_ok=True)
        (Path(wd) / "parameters" / "ref_seq").mkdir(parents=True, exist_ok=True)
        (Path(wd) / "parameters" / "ref_msa").mkdir(parents=True, exist_ok=True)
        (Path(wd) / "tmp_files").mkdir(exist_ok=True)
        (Path(wd) / "results").mkdir(parents=True, exist_ok=True)

        # get entrez count
        organisms = taxonomy.splitlines()
        organisms = [x for x in organisms if len(x) > 0]
        count = entrez_count(email, organisms, qualifier, date_from, date_to)

        # save BLAST parameters
        with open(Path(wd) / "parameters" / "blast_parameters.txt", "w") as fw:
            fw.write("target_region\t" + target_region + "\n")
            fw.write("taxonomy\t" + taxonomy.replace("\n", "|") + "\n")
            fw.write("entrez_qualifier\t" + qualifier + "\n")
            fw.write("date_from\t" + date_from + "\n")
            fw.write("date_to\t" + date_to + "\n")
            fw.write("entrez_email\t" + email + "\n")
            fw.write("entrez_count\t" + str(count) + "\n")
            fw.write("max_length\t" + str(max_length) + "\n")
            fw.write(
                "key_annotations\t"
                + key_annotations.replace("\n", "|").replace(";", "|")
                + "\n"
            )
            fw.write("exclude_sources\t" + exclude_sources.replace("\n", "|") + "\n")
            fw.write("expect_value\t" + str(expect_value) + "\n")
            fw.write("gap_costs\t" + gap_costs + "\n")
            fw.write("word_size\t" + str(word_size) + "\n")
            fw.write("nucl_reward\t" + str(nucl_reward) + "\n")
            fw.write("nucl_penalty\t" + str(nucl_penalty) + "\n")

        # save initial queries
        with open(Path(wd) / "parameters" / "initial_queries.fasta", "w") as fw:
            fw.write(initial_queries)

        key_annotations_list = [
            x.strip()
            for x in key_annotations.replace(";", "|").replace(",", "|").split("|")
            if len(x.strip()) > 0
        ]
        exclude_sources_list = [x for x in exclude_sources.splitlines() if len(x) > 0]
        ref_number = 5

        # start BLAST thread
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
                email,
                qualifier,
                self.stop_flag,
            ),
        )
        self.blast_thread = thread
        self.stop_flag.clear()
        thread.daemon = True
        thread.start()

        retrieval_interface.btn_submit_blast.setEnabled(False)
        retrieval_interface.btn_load_job.setEnabled(False)
        retrieval_interface.btn_stop.setEnabled(True)

        if parent_window:
            InfoBar.success(
                title="Success",
                content="New blast submitted!",
                parent=parent_window,
                position=InfoBarPosition.TOP,
                duration=5000,
            )

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

        print("=" * 50)
        self.emit_log("Loading previous job...")

        # check if working directory exists
        if not Path(wd).exists():
            self.emit_log(
                "Working directory does not exist, please submit new BLAST.", "WARNING"
            )
            return
        if not (Path(wd) / "parameters").exists():
            self.emit_log(
                "Can't find parameters directory, please submit new BLAST.", "WARNING"
            )
            return
        if not (Path(wd) / "tmp_files").exists():
            self.emit_log(
                "Can't find tmp_files directory, please submit new BLAST.", "WARNING"
            )
            return
        if not (Path(wd) / "results").exists():
            self.emit_log(
                "Can't find results directory, please submit new BLAST.", "WARNING"
            )
            return

        # read BLAST parameters in blast_parameters.txt file
        parameters_files = [f.name for f in (Path(wd) / "parameters").iterdir()]
        if "blast_parameters.txt" not in parameters_files:
            self.emit_log(
                "Can't find BLAST parameters, please submit new BLAST.", "WARNING"
            )
            return
        if "initial_queries.fasta" not in parameters_files:
            self.emit_log(
                "Can't find initial queries, please submit new BLAST.", "WARNING"
            )
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

        date_from = retrieval_interface.date_from.date.toString("yyyy/MM/dd")
        date_to = retrieval_interface.date_to.date.toString("yyyy/MM/dd")

        organisms = taxonomy.split("|")
        organisms = [x for x in organisms if len(x) > 0]
        key_annotations_list = (
            key_annotations.replace(";", "|").replace(",", "|").split("|")
        )
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
                entrez_qualifier,
                blast_round,
                self.stop_flag,
            ),
        )
        self.blast_thread = thread
        self.stop_flag.clear()
        thread.daemon = True
        thread.start()

        retrieval_interface.btn_submit_blast.setEnabled(False)
        retrieval_interface.btn_load_job.setEnabled(False)
        retrieval_interface.btn_stop.setEnabled(True)
        InfoBar.success(
            title="Success",
            content="Previous job loaded!",
            parent=parent_window,
            position=InfoBarPosition.TOP,
        )

    def stop_blast(self, retrieval_interface):
        """Stop the BLAST process and reset UI state"""
        self.stop_flag.set()

        if self.blast_thread and self.blast_thread.is_alive():
            self.blast_thread = None

        retrieval_interface.btn_submit_blast.setEnabled(True)
        retrieval_interface.btn_load_job.setEnabled(True)
        retrieval_interface.btn_stop.setEnabled(False)

        self.emit_log("BLAST process stopped.", "WARNING")

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

    def set_reduce_threshold(self, retrieval_interface, state):
        if isinstance(state, bool):
            is_checked = state
        else:
            is_checked = (
                (state == Qt.Checked)
                if isinstance(state, Qt.CheckState)
                else (state == 2)
            )
        retrieval_interface.len_thresh.setEnabled(is_checked)
        retrieval_interface.chk_consensus.setEnabled(is_checked)

    def select_tri_method(self, construction_interface):
        method = construction_interface.combo_trim_method.currentText()
        is_user = "user defined" in method
        construction_interface.trim_gt.setEnabled(is_user)
        construction_interface.trim_st.setEnabled(is_user)
        construction_interface.trim_ct.setEnabled(False)
        construction_interface.trim_con.setEnabled(is_user)

    def run_filtering(self, retrieval_interface):
        from my_filter import call_miner_filter

        in_path = retrieval_interface.filter_in.text().strip()
        out_path = retrieval_interface.filter_out.text().strip() or in_path

        if not in_path:
            self.emit_log("Please set input path", "WARNING")
            return
        if not Path(in_path).exists():
            Path(in_path).mkdir(parents=True, exist_ok=True)
            self.emit_log(f"Created input directory: {in_path}", "INFO")

        if not Path(out_path).exists():
            Path(out_path).mkdir(parents=True, exist_ok=True)

        try:
            len_thr = int(retrieval_interface.len_thresh.text().strip())
            cons = retrieval_interface.chk_consensus.isChecked()
        except ValueError as e:
            self.emit_log(f"Value Error: {e}", "ERROR")
            return

        action = 0
        if (
            retrieval_interface.switch_ext.isChecked()
            and retrieval_interface.switch_reduce.isChecked()
        ):
            action = 3  # both
        elif retrieval_interface.switch_ext.isChecked():
            action = 1  # extension only
        elif retrieval_interface.switch_reduce.isChecked():
            action = 2  # reduce only

        if action == 0:
            self.emit_log("Please select an option", "WARNING")
            return

        self.emit_log("Running Filter...")

        def emit_callback(message, level="INFO"):
            self.emit_log(message, level)

        thread = threading.Thread(
            target=call_miner_filter,
            args=(in_path, out_path, action, cons, len_thr, emit_callback),
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
            Path(in_path).mkdir(parents=True, exist_ok=True)
            self.emit_log(f"Created input directory: {in_path}", "INFO")
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
        reorder = construction_interface.chk_reorder.isChecked()

        def emit_callback(message, level="INFO"):
            self.emit_log(message, level)

        self.emit_log("Running MAFFT...")

        def run_mafft_thread():
            try:
                _, total_time = mafft(
                    in_path,
                    str(out_path),
                    "",
                    "",
                    algo,
                    thread_num,
                    reorder,
                    "",
                    False,
                    "",
                    emit_callback,
                )
                if total_time is not None:
                    self.emit_log(
                        f"MAFFT completed in {total_time:.2f} seconds", "SUCCESS"
                    )

            finally:
                for file in Path(out_path).glob("*"):
                    if not file.name.startswith("msa"):
                        file.rename(Path(out_path) / f"msa_{file.name}")

        thread = threading.Thread(target=run_mafft_thread)
        thread.daemon = True
        thread.start()

    def run_trimming(self, construction_interface):

        from call_trimal import trim_start_end_optimized, trimal

        in_path = construction_interface.trim_in.text().strip()
        out_path = construction_interface.trim_out.text().strip()
        is_chloroplast = construction_interface.chk_chloroplast.isChecked()

        if not in_path:
            self.emit_log("Please set input path", "WARNING")
            return
        if not Path(in_path).exists():
            Path(in_path).mkdir(parents=True, exist_ok=True)
            self.emit_log(f"Created input directory: {in_path}", "INFO")
        if not out_path:
            if Path(in_path).is_file():
                out_path = str(Path(in_path).parent)
                self.emit_log(
                    f"Using input file's directory as output: {out_path}", "INFO"
                )
            else:
                out_path = in_path
                self.emit_log("Using input directory as output", "INFO")

        if not Path(out_path).exists():
            Path(out_path).mkdir(parents=True, exist_ok=True)

        met = construction_interface.combo_trim_method.currentText().split(" ")[0]
        if met == "user":
            met = ""

        gt_val = construction_interface.trim_gt.text()
        st_val = construction_interface.trim_st.text()
        ct_val = construction_interface.trim_ct.text()
        con_val = construction_interface.trim_con.text()

        def emit_callback(message, level="INFO"):
            self.emit_log(message, level)

        def run_trimming_thread():
            if is_chloroplast:
                self.emit_log("Running boundary trimming (Chloroplast Mode)...")
                try:
                    trim_start_end_optimized(
                        boundaries_threshold=0.025, in_path=in_path
                    )
                    self.emit_log("Boundary trimming completed", "SUCCESS")
                except Exception as e:
                    self.emit_log(f"Boundary trimming failed: {e}", "ERROR")
                    return

            self.emit_log("Running trimAl...")

            _, total_time = trimal(
                in_path,
                out_path,
                False,
                False,
                met,
                gt_val,
                st_val,
                ct_val,
                con_val,
                "",
                False,
                "",
                emit_callback,
            )
            if total_time is not None:
                self.emit_log(
                    f"trimAl completed in {total_time:.2f} seconds", "SUCCESS"
                )

        thread = threading.Thread(target=run_trimming_thread)
        thread.daemon = True
        thread.start()

    def run_concatenation(self, construction_interface):
        from functional import my_concatenation

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

        out_path_obj = Path(out_p)
        if out_path_obj.exists() and any(out_path_obj.iterdir()):
            self.emit_log(
                f"Output directory already exists and is not empty: {out_p}", "WARNING"
            )
            self.emit_log(
                "Please choose an empty directory or remove existing files first",
                "WARNING",
            )
            return

        if not out_path_obj.exists():
            out_path_obj.mkdir(parents=True, exist_ok=True)

        self.emit_log("Running Concatenation...")
        thread = threading.Thread(
            target=my_concatenation, args=(in_p, out_p, self.emit_log)
        )
        thread.daemon = True
        thread.start()

    def run_install_mafft(self):
        from install_dependencies import install_mafft

        self.emit_log("Installing MAFFT...")

        def install_thread():
            install_mafft(log_callback=lambda msg: self.emit_log(msg, "INFO"))

        thread = threading.Thread(target=install_thread)
        thread.daemon = True
        thread.start()

    def run_install_trimal(self):
        from install_dependencies import install_trimal

        self.emit_log("Installing trimAl...")

        def install_thread():
            install_trimal(log_callback=lambda msg: self.emit_log(msg, "INFO"))

        thread = threading.Thread(target=install_thread)
        thread.daemon = True
        thread.start()

    def run_install_pga(self):
        from install_dependencies import install_pga

        self.emit_log("Installing PGA...")

        def install_thread():
            install_pga(log_callback=lambda msg: self.emit_log(msg, "INFO"))

        thread = threading.Thread(target=install_thread)
        thread.daemon = True
        thread.start()

    def show_about(self, parent_window):
        from qfluentwidgets import FluentIcon as FIF

        title = "About"
        content = "Authors: Ruijing Cheng & Yuxuan Wang\n\nLicense: GPL V3"

        w = MessageBox(title, content, parent_window)
        w.setClosableOnMaskClicked(True)
        w.setDraggable(False)

        w.yesButton.setText("View Github Page")
        w.yesButton.setIcon(FIF.GITHUB)
        w.cancelButton.setText("Back")

        if w.exec():
            from PySide6.QtCore import QUrl
            from PySide6.QtGui import QDesktopServices

            QDesktopServices.openUrl(QUrl("https://github.com/wyx619/PyNCBIminer_NG"))

    def download_chloroplast_genomes(self, email, in_path, out_path):
        from pathlib import Path

        from Chloroplast.download_gb_file import download_gb_file

        in_path = Path(in_path)
        out_path = Path(out_path)

        out_path.mkdir(parents=True, exist_ok=True)
        existing_files = {p.stem for p in out_path.glob("*.gb")}

        with open(in_path, "r") as fr:
            accession_list = fr.read().splitlines()

        skipped = []
        to_download = []
        for acc in accession_list:
            acc_clean = acc.split(".")[0]
            if acc and acc_clean not in existing_files:
                to_download.append(acc)
            else:
                skipped.append(acc_clean)

        self.emit_log(
            f"Total: {len(accession_list)}, Already downloaded: {len(skipped)}, To download: {len(to_download)}"
        )

        if len(to_download) == 0:
            self.emit_log("All files already downloaded!", "SUCCESS")
            self.emit_log("Running quality check...")
            _, _, _, success, failed = download_gb_file(email, in_path, out_path, 10)
            if success > 0:
                self.emit_log(f"Quality check: Verified {success} files", "SUCCESS")
            return

        self.emit_log("Starting download...")

        def run():
            _, _, _, success, failed = download_gb_file(email, in_path, out_path, 10)
            self.emit_log(f"Downloaded: {success}, Failed: {failed}")
            if failed == 0:
                self.emit_log("All downloads completed successfully!", "SUCCESS")
            else:
                self.emit_log(
                    f"All downloads completed with {failed} failures", "WARNING"
                )

        thread = threading.Thread(target=run)
        thread.daemon = True
        thread.start()

    def quality_control(
        self, in_folder, out_folder, cds_threshold=80, ambig_threshold=0.2, threads=None
    ):
        from pathlib import Path

        from Chloroplast.quality_ctrl import generate_genome_report

        in_folder = Path(in_folder)
        out_folder = Path(out_folder)

        out_folder.mkdir(parents=True, exist_ok=True)

        def run_qc():
            error_count = generate_genome_report(
                in_folder_path=str(in_folder),
                out_folder_path=str(out_folder),
                cds_threshold=cds_threshold,
                ambig_threshold=ambig_threshold,
                threads=threads,
            )
            if error_count > 0:
                self.emit_log(
                    f"Quality control completed with {error_count} error(s)", "WARNING"
                )
            else:
                self.emit_log("Quality control completed successfully!", "SUCCESS")

        thread = threading.Thread(target=run_qc)
        thread.daemon = True
        thread.start()

    def run_get_cds(self, in_folder, out_folder, threads=3):
        from pathlib import Path

        from Chloroplast.get_cds import get_cds

        in_folder = Path(in_folder)
        out_folder = Path(out_folder)

        out_folder.mkdir(parents=True, exist_ok=True)

        def run_cds():
            try:
                get_cds(str(in_folder), str(out_folder), threads)
                self.emit_log("CDS extraction completed successfully!", "SUCCESS")
            except Exception as e:
                self.emit_log(f"CDS extraction failed: {e}", "WARNING")

        thread = threading.Thread(target=run_cds)
        thread.daemon = True
        thread.start()

    def run_filter_cds(
        self, in_folder, out_folder, ref_type, lower_bound, upper_bound, threads=3
    ):
        from pathlib import Path

        from Chloroplast.filter_seq import get_ref_dict, select_seq_by_len

        in_folder = Path(in_folder)
        out_folder = Path(out_folder)

        if not in_folder.exists():
            self.emit_log(f"Input directory does not exist: {in_folder}", "WARNING")
            return

        ref_dict = get_ref_dict(ref_type)
        if ref_dict is None:
            self.emit_log(f"Invalid reference type: {ref_type}", "WARNING")
            return

        out_folder.mkdir(parents=True, exist_ok=True)

        def run_filter():
            try:
                select_seq_by_len(
                    str(in_folder),
                    str(out_folder),
                    ref_dict,
                    lower_bound,
                    upper_bound,
                    threads,
                )
                self.emit_log("CDS filtering completed successfully!", "SUCCESS")
            except Exception as e:
                self.emit_log(f"CDS filtering failed: {e}", "WARNING")

        thread = threading.Thread(target=run_filter)
        thread.daemon = True
        thread.start()

    def run_select_cds(
        self, in_folder, out_folder, enable_tax_res=False, tax_file=None, threads=3
    ):
        from pathlib import Path

        from Chloroplast.select_seq_by_acc import make_tab, select_seq_by_acc

        in_folder = Path(in_folder)
        out_folder = Path(out_folder)

        if not in_folder.exists():
            self.emit_log(f"Input directory does not exist: {in_folder}", "WARNING")
            return

        length_csv = in_folder / "length.csv"
        if not length_csv.exists():
            self.emit_log(f"length.csv not found in {in_folder}", "WARNING")
            return

        out_folder.mkdir(parents=True, exist_ok=True)

        def run_select():
            try:
                file_organism_name = tax_file if enable_tax_res and tax_file else None
                df_organism = make_tab(str(in_folder), file_organism_name)
                if df_organism is not None:
                    select_seq_by_acc(
                        str(in_folder),
                        str(out_folder),
                        df_organism,
                        num_processes=threads,
                    )
                    self.emit_log("CDS selection completed successfully!", "SUCCESS")
                else:
                    self.emit_log("CDS selection skipped (no valid data)", "WARNING")
            except Exception as e:
                self.emit_log(f"CDS selection failed: {e}", "WARNING")

        thread = threading.Thread(target=run_select)
        thread.daemon = True
        thread.start()


def get_query_accession(record):
    parts = record.description.split(" ")[0].split("|")[0].split(":")
    # assert len(parts) == 2
    return parts[0]
