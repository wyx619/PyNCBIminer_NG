# *-* coding:utf-8 *-*
import sys
import threading
from pathlib import Path

from PySide6.QtCore import Qt, Signal, QObject
from qfluentwidgets import (InfoBar, InfoBarPosition)


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

    def __init__(self):
        super().__init__()

    def emit_log(self, message):
        self.log_signal.emit(message)

    def save_settings(self, retrieval_interface, parent_window):
        target_region = retrieval_interface.combo_region.currentText()
        if target_region.strip() == "":
            InfoBar.warning(title="Error", content="Please input region name.", parent=parent_window)
            return

        blast_params_dir = Path(get_writable_path("blast_parameters"))
        blast_params_dir.mkdir(parents=True, exist_ok=True)
        
        key_annotations = retrieval_interface.key_anno.text().strip().replace("; ", "|")
        
        with open(blast_params_dir / Path(target_region + ".txt"), "w") as fw:
            fw.write(f"target_region\t{target_region}\n")
            fw.write(f"entrez_qualifier\t{retrieval_interface.entrez_qualifier.toPlainText().strip()}\n")
            fw.write(f"max_length\t{retrieval_interface.max_len.text().strip()}\n")
            fw.write(f"key_annotations\t{key_annotations.replace(';', '|')}\n")
            fw.write(f"exclude_sources\t{retrieval_interface.excl_source.toPlainText().strip().replace(chr(10), '|')}\n")
            fw.write(f"expect_value\t{retrieval_interface.expect_val.text().strip()}\n")
            fw.write(f"gap_costs\t{retrieval_interface.gap_costs.text().strip()}\n")
            fw.write(f"word_size\t{retrieval_interface.word_size.text().strip()}\n")
            fw.write(f"nucl_reward\t{retrieval_interface.nucl_reward.text().strip()}\n")
            fw.write(f"nucl_penalty\t{retrieval_interface.nucl_penalty.text().strip()}\n")

        initial_queries = retrieval_interface.init_queries.toPlainText().strip()
        initial_queries_dir = Path(get_writable_path("initial_queries"))
        initial_queries_dir.mkdir(parents=True, exist_ok=True)
        target_region_dir = initial_queries_dir / Path(target_region)
        target_region_dir.mkdir(parents=True, exist_ok=True)
        
        with open(target_region_dir / Path(target_region + ".fasta"), "w") as fw:
            fw.write(initial_queries)

        if retrieval_interface.combo_region.findText(target_region) == -1:
            retrieval_interface.combo_region.addItem(target_region)
            
        retrieval_interface.combo_region.setCurrentText(target_region)
        retrieval_interface.btn_save_settings.setEnabled(False)
        retrieval_interface.btn_set_region.setEnabled(True)
        InfoBar.success(title="Saved", content=f"Settings saved for {target_region}", parent=parent_window)

    def my_esearch(self, retrieval_interface):
        from my_entrez import entrez_count, entrez_summary
        
        taxonomy = retrieval_interface.tax_edit.toPlainText().strip()
        if taxonomy == "":
            self.emit_log("Please input your target groups.")
            return
        
        organisms = [x for x in taxonomy.splitlines() if len(x) > 0]
        email = retrieval_interface.email_edit.text().strip()
        d_from = retrieval_interface.date_from.text().strip()
        d_to = retrieval_interface.date_to.text().strip()
        qualifier = retrieval_interface.entrez_qualifier.toPlainText().strip()

        self.emit_log("Starting ESearch...")
        
        if retrieval_interface.chk_summary.isChecked():
            target_region_list = [f.name for f in Path(get_resource_path("blast_parameters")).iterdir()]
            target_region_list = [Path(x).stem for x in target_region_list]
            target_region_dict = {}
            
            thread = threading.Thread(target=entrez_summary, args=(email, organisms, target_region_dict, d_from, d_to))
        else:
            thread = threading.Thread(target=entrez_count, args=(email, organisms, qualifier, d_from, d_to))
            
        thread.daemon = True
        thread.start()

    def submit_new_blast(self, retrieval_interface):
        
        self.emit_log("Submitting New BLAST...")
        wd = retrieval_interface.wd_edit.text().strip()
        
        if not wd or not Path(wd).exists():
             try:
                 Path(wd).mkdir(parents=True, exist_ok=True)
             except Exception as e:
                 self.emit_log(f"Error creating working directory: {e}")
                 return

        try:
            pass#max_len = int(retrieval_interface.max_len.text().strip())
        except ValueError as e:
            self.emit_log(f"Value Error: {e}")
            return

        (Path(wd) / "parameters" / "ref_seq").mkdir(parents=True, exist_ok=True)
        (Path(wd) / "parameters" / "ref_msa").mkdir(parents=True, exist_ok=True)
        (Path(wd) / "tmp_files").mkdir(exist_ok=True)
        (Path(wd) / "results").mkdir(exist_ok=True)

        self.emit_log("BLAST thread started (mock).")

    def load_previous_job(self, retrieval_interface):
        self.emit_log("Loading previous job...")

    def set_marker_summary(self, retrieval_interface, state):
        is_checked = (state == Qt.Checked) if isinstance(state, Qt.CheckState) else (state == 2)
        
        retrieval_interface.entrez_qualifier.setEnabled(not is_checked)
        retrieval_interface.combo_region.setEnabled(not is_checked)
        retrieval_interface.btn_save_settings.setEnabled(not is_checked)
        if is_checked:
            retrieval_interface.entrez_qualifier.clear()
            retrieval_interface.combo_region.setCurrentIndex(0)

    def set_reduce_threshold(self, construction_interface, state):
        is_checked = (state == Qt.Checked) if isinstance(state, Qt.CheckState) else (state == 2)
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
        
        try:
            len_thr = int(construction_interface.len_thresh.text().strip())
            cons = construction_interface.combo_consensus.currentText() == "True"
        except ValueError as e:
            self.emit_log(f"Value Error: {e}")
            return

        action = 0
        if construction_interface.chk_ext.isChecked() and construction_interface.chk_reduce.isChecked(): 
            action = 3
        elif construction_interface.chk_ext.isChecked():
            action = 1
        elif construction_interface.chk_reduce.isChecked(): 
            action = 2
        
        if action == 0:
            self.emit_log("Please select an option")
            return

        self.emit_log("Running Filter...")
        thread = threading.Thread(target=call_miner_filter, args=(in_path, out_path, action, cons, len_thr, False))
        thread.daemon = True
        thread.start()

    def run_alignment(self, construction_interface):
        self.check_dependencies()
        from call_mafft2 import mafft
        
        in_path = construction_interface.align_in.text().strip()
        out_path = construction_interface.align_out.text().strip()
        if not Path(out_path).exists():
            Path(out_path).mkdir(exist_ok=True)
        
        algo = construction_interface.align_algo.currentText()
        thread_num = construction_interface.align_thread.text()
        reorder = construction_interface.align_reorder.currentText() == "True"
        
        self.emit_log("Running MAFFT...")
        thread = threading.Thread(target=mafft, args=(in_path, out_path, "", "", algo, thread_num, reorder, "", False, ""))
        thread.daemon = True
        thread.start()

    def run_trimming(self, construction_interface):
        self.check_dependencies()
        from call_trimal import trimal
        
        in_path = construction_interface.trim_in.text().strip()
        out_path = construction_interface.trim_out.text().strip()
        if not Path(out_path).exists():
            Path(out_path).mkdir(exist_ok=True)
        
        met = construction_interface.combo_trim_method.currentText().split(" ")[0]
        if met == "user": 
            met = ""
        
        self.emit_log("Running trimAl...")
        thread = threading.Thread(target=trimal, args=(in_path, out_path, True, False, met, 
                                                     construction_interface.trim_gt.text(), construction_interface.trim_st.text(), 
                                                     construction_interface.trim_ct.text(), construction_interface.trim_con.text(), 
                                                     "", False, ""))
        thread.daemon = True
        thread.start()

    def run_concatenation(self, construction_interface):
        from my_concatenation import my_concatenation
        
        in_p = construction_interface.concat_in.text()
        out_p = construction_interface.concat_out.text()
        
        self.emit_log("Running Concatenation...")
        thread = threading.Thread(target=my_concatenation, args=(in_p, out_p))
        thread.daemon = True
        thread.start()

    def run_install_mafft(self):
        self.emit_log("Install MAFFT triggered")

    def run_install_trimal(self):
        self.emit_log("Install trimAl triggered")

    def show_about(self, parent_window):
        InfoBar.info(
            title="PyNCBIminer v1.3",
            content="Author: Ruijing Cheng & Yuxuan Wang\nLicense: GPL V3",
            orient=Qt.Vertical,
            position=InfoBarPosition.BOTTOM_RIGHT,
            duration=5000,
            parent=parent_window
        )

    def check_dependencies(self):
        pass
