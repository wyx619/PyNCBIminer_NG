# *-* coding:utf-8 *-*
# @Time:2022/5/6 15:14
# @Author: Ruijing Cheng
# @File:pyNCBIminer_00_main.py
# @Software:PyCharm


import os
import sys
import ctypes
from ui_main import Ui_MainWindow
from PySide6.QtWidgets import QApplication, QMessageBox, QFileDialog, QMainWindow
from PySide6.QtCore import QObject, Signal, QEventLoop, QTimer, Slot, SIGNAL, Qt, QPropertyAnimation, QEasingCurve
from PySide6.QtGui import QTextCursor, QGuiApplication, QIcon
from pathlib import Path
import threading

from tools import print_line
import warnings

warnings.filterwarnings('ignore')


def get_resource_path(relative_path):
    """
    获取资源文件的绝对路径，兼容开发环境和打包后的环境
    """
    try:
        # PyInstaller创建临时文件夹并将路径存储在_MEIPASS中
        base_path = sys._MEIPASS
    except AttributeError:
        # 如果不是打包环境，使用脚本所在目录
        base_path = os.path.dirname(os.path.abspath(__file__))
    
    return os.path.join(base_path, relative_path)


def get_writable_path(relative_path):
    """
    获取可写路径，优先使用工作目录，兼容开发环境和打包后的环境
    """
    return os.path.join(os.getcwd(), relative_path)


class EmittingStr(QObject):
    """
    define a signal of sending string
    """

    textWritten = Signal(str)

    def write(self, text):
        self.textWritten.emit(str(text))
        loop = QEventLoop()
        QTimer.singleShot(50, loop.quit)
        loop.exec_()

    def flush(self):
        pass


class MainWindow(QMainWindow):
    """
    define the main window of graphical user interface
    """
    @Slot()
    def outputWritten(self, text):
        """
        define the slot to receive the signal of sending string
        """

        cursor = self.ui.message_box.textCursor()
        cursor.movePosition(QTextCursor.End)
        cursor.insertText(text)
        self.ui.message_box.setTextCursor(cursor)
        self.ui.message_box.ensureCursorVisible()

    def __init__(self):
        # # use uiloader
        # self.ui = QUiLoader().load('ui/PyNCBIminer_main10.ui')

        # use ui_main.py
        super(MainWindow, self).__init__()
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)

        # 设置 message_box 为只读模式（可以查看和复制，但不能修改）
        self.ui.message_box.setReadOnly(True)

        # 显示欢迎信息

        self.ui.message_box.appendPlainText("Welcome to PyNCBIminer!\n")


        # resize the window to a comfortable size that works on high-DPI screens
        app = QApplication.instance()
        app.setAttribute(Qt.AA_EnableHighDpiScaling)
        app.setAttribute(Qt.AA_UseHighDpiPixmaps)
        
        screen = QGuiApplication.primaryScreen()
        available_geometry = screen.availableGeometry()  # Get available screen space (excludes taskbar)
        
        # Set a fixed size that's comfortable on most screens
        # or use a percentage of available space with minimum limits
        min_width = 1200
        min_height = 800
        
        # Calculate size as percentage of available space but not smaller than minimums
        newW = max(min_width, int(available_geometry.width() * 0.6))
        newH = max(min_height, int(available_geometry.height() * 0.7))
        
        # Center the window
        newLeft = int((available_geometry.width() - newW) / 2) + available_geometry.left()
        newTop = int((available_geometry.height() - newH) / 3) + available_geometry.top()
        
        self.resize(newW, newH)  # Use self instead of self.ui since we're in MainWindow class
        self.move(newLeft, newTop)

        # connect menu with actions
        self.ui.actionAbout.triggered.connect(self.show_about)
        self.ui.actionExit.triggered.connect(self.close)
        self.ui.actionInstall_MAFFT.triggered.connect(self.run_install_mafft)
        self.ui.actionInstall_trimAl.triggered.connect(self.run_install_trimal)

        # connect buttons and functions
        # buttons in Sequence Retrieving module
        self.ui.set_target_region.clicked.connect(self.set_target_region)
        self.ui.esearch.clicked.connect(self.my_esearch)
        self.ui.submit_new_blast.clicked.connect(self.submit_new_blast)
        self.ui.load_previous_job.clicked.connect(self.load_previous_job)
        self.ui.view.clicked.connect(self.view_wd)

        self.ui.target_region.setEditable(True)
        self.ui.set_target_region.setEnabled(False)
        target_region_list = os.listdir(Path(get_resource_path("blast_parameters")))
        target_region_list = [Path(x).stem for x in target_region_list]
        self.ui.target_region.clear()
        self.ui.target_region.addItems([""] + target_region_list)
        self.ui.target_region.currentIndexChanged.connect(self.select_target_region)

        self.ui.save_settings.clicked.connect(self.save_settings)

        self.ui.marker_summary.stateChanged.connect(self.set_marker_summary)

        self.ui.len_threshold.setEnabled(False)
        self.ui.consensus_value.setEnabled(False)
        # self.ui.name_correction.setEnabled(False)
        self.ui.reduce_dataset.stateChanged.connect(self.set_reduce_threshold)
        self.ui.out_path1.setEnabled(False)
        self.ui.view_out_path1.setEnabled(False)

        self.ui.ali_alg.setEditable(False)

        # allow to do control extension, then reduce dataset
        self.ui.buttonGroup.setExclusive(False)

        self.ui.tri_met.setEditable(False)
        self.ui.tri_gt.setEnabled(False)
        self.ui.tri_st.setEnabled(False)
        self.ui.tri_ct.setEnabled(False)
        self.ui.tri_con.setEnabled(False)
        self.ui.tri_met.currentIndexChanged.connect(self.select_tri_method)

        # buttons in Supermatrix Construction module
        # filter sequences
        self.ui.view_in_path1.clicked.connect(self.view_in_path1)
        self.ui.view_out_path1.clicked.connect(self.view_out_path1)
        self.ui.run_filtering.clicked.connect(self.run_filtering2)
        # align sequences
        self.ui.view_in_path2.clicked.connect(self.view_in_path2)
        self.ui.view_out_path2.clicked.connect(self.view_out_path2)
        self.ui.run_alignment.clicked.connect(self.run_alignment)
        # trim alignments
        self.ui.view_in_path3.clicked.connect(self.view_in_path3)
        self.ui.view_out_path3.clicked.connect(self.view_out_path3)
        self.ui.run_trimming.clicked.connect(self.run_trimming)
        # concatenate alignments
        self.ui.view_in_path4.clicked.connect(self.view_in_path4)
        self.ui.view_out_path4.clicked.connect(self.view_out_path4)
        self.ui.run_concatenation.clicked.connect(self.run_concatenation)
        # # ML inference
        # self.ui.view_in_path5.clicked.connect(self.view_in_path5)
        # # self.ui.view_out_path5.clicked.connect(self.view_out_path5)
        # self.ui.view_partition_file.clicked.connect(self.view_partition_file)
        # self.ui.view_constrain_file.clicked.connect(self.view_constrain_file)
        #
        # self.ui.run_iqtree.clicked.connect(self.run_iqtree)

        # redirect the output messages to the message box
        sys.stdout = EmittingStr()
        self.ui.message_box.connect(sys.stdout, SIGNAL("textWritten(QString)"), self.outputWritten)
        sys.stderr = EmittingStr()
        self.ui.message_box.connect(sys.stderr, SIGNAL("textWritten(QString)"), self.outputWritten)

        # --------------------------------- Tools ---------------------------------
        self.mafft_checked = False
        self.trimal_checked = False

        # Set up fade-in animation
        self.setWindowOpacity(0.0)
        self.fade_in_animation = QPropertyAnimation(self, b"windowOpacity")
        self.fade_in_animation.setDuration(150)
        self.fade_in_animation.setStartValue(0.0)
        self.fade_in_animation.setEndValue(1.0)
        self.fade_in_animation.setEasingCurve(QEasingCurve.InOutQuad)
        
        # Use QTimer to start animation after window is shown
        QTimer.singleShot(50, self.fade_in_animation.start)
        
        # Check dependencies after window is shown (non-blocking)
        QTimer.singleShot(100, self.check_dependencies)

    def run_install_mafft(self):
        from install_dependencies import install_mafft
        self.ui.thread = threading.Thread(target=install_mafft)
        self.ui.thread.setDaemon(True)
        self.ui.thread.start()
        QMessageBox.about(self.ui, "Install MAFFT", "Installation started!")

    def run_install_trimal(self):
        from install_dependencies import install_trimal
        self.ui.thread = threading.Thread(target=install_trimal)
        self.ui.thread.setDaemon(True)
        self.ui.thread.start()
        QMessageBox.about(self.ui, "Install trimAl", "Installation started!")

    def check_dependencies(self):
        """
        Check if MAFFT and TrimAl are installed and update PATH if needed.
        This method uses caching to avoid repeated disk checks.
        """
        root_path = os.getcwd()
        
        if not self.mafft_checked:
            mafft_path = Path(root_path) / Path(r"./mafft/mafft-win")
            if os.path.exists(Path(root_path) / Path("./mafft/mafft-win/mafft.bat")):
                os.environ["PATH"] = os.environ["PATH"] + ";" + str(mafft_path)
                print('MAFFT found')
            else:
                print("Please check if MAFFT is installed. You can install it through the Tools menu.")
            self.mafft_checked = True
        
        if not self.trimal_checked:
            trimal_path = Path(root_path) / Path(r"./trimal/trimAl_Windows_x86-64")
            if os.path.exists(Path(root_path) / Path("./trimal/trimAl_Windows_x86-64/trimal.exe")):
                os.environ["PATH"] = os.environ["PATH"] + ";" + str(trimal_path)
                print('TrimAl found')
            else:
                print("Please check if TrimAl is installed. You can install it through the Tools menu.")
            self.trimal_checked = True

    def show_about(self):
        about_text = """
        <h2>PyNCBIminer</h2>
        <p>Version 1.3</p>
        <p>A powerful tool for sequence mining from NCBI database.</p>
        <p><b>Features:</b></p>
        <ul>
            <li>Automated BLAST search and sequence retrieval</li>
            <li>Sequence filtering and quality control</li>
            <li>Multiple sequence alignment with MAFFT</li>
            <li>Alignment trimming with trimAl</li>
            <li>Supermatrix construction</li>
        </ul>
        <p><b>Author:</b> Ruijing Cheng</p>
        <p><b>License:</b> GPL V3</p>
        <p><b>Useful Links:</b></p>
        <a href="https://www.ncbi.nlm.nih.gov/">NCBI Database</a><br>
        <a href="https://mafft.cbrc.jp/alignment/software/">MAFFT</a><br>
        <a href="http://trimal.cgenomics.org/">TrimAl</a><br>
        
        """
        QMessageBox.about(self.ui, "About", about_text)

    def closeEvent(self, event):
        """
        Override closeEvent to add fade-out animation before closing
        """
        if hasattr(self, '_is_closing') and self._is_closing:
            return
        
        self._is_closing = True
        self.fade_animation = QPropertyAnimation(self, b"windowOpacity")
        self.fade_animation.setDuration(150)
        self.fade_animation.setStartValue(1.0)
        self.fade_animation.setEndValue(0.0)
        self.fade_animation.setEasingCurve(QEasingCurve.InOutQuad)
        
        self.fade_animation.finished.connect(self.close_window)
        self.fade_animation.start()
        event.ignore()

    def close_window(self):
        """
        Actually close the window after fade-out animation
        """
        QMainWindow.close(self)

    # --------------------------------- Sequence Retrieving ---------------------------------
    def select_target_region(self):
        """

        :return:
        """
        target_region = self.ui.target_region.currentText()
        if target_region == "":
            self.ui.target_region.setEditable(True)
            self.ui.save_settings.setEnabled(True)
            self.ui.set_target_region.setEnabled(False)
        else:
            self.ui.target_region.setEditable(False)
            self.ui.save_settings.setEnabled(False)
            self.ui.set_target_region.setEnabled(True)

    def set_target_region(self):
        """
        set target region in the Sequence Retrieving module
        implemented markers includes: ITS, rbcL, matK, trnL-trnF, psbA-trnH, ndhF and rpoB
        automatically adds initial queries, BLAST parameters, key annotations and exclude sources
        :return: None
        """
        # todo: save parameters in separate files and allow users to save their settings.

        '''
        parameters = {
            "ITS": (
                    "ITS 1\ninternal transcribed spacer\nITS 2\ninternal transcribed spacers 1 and 2\n5.8S",  # key_annotations
                    "mitochondrion\nmitochondrial\nchloroplast\nplastid\nenvironmental sample\nenvironmental_sample",  # exclude_sources
                    "10",  # expect_value  # 0.001
                    "2 1",  # gap_costs
                    "7",  # word_size
                    "1",  # reward
                    "-1",  # penalty
                    '(("ITS 1" OR "ITS 2" OR "5.8S" OR "transcribed spacer" OR "ITS1" OR "ITS2" OR "5.8 S") ' \
                    'NOT "environmental sample" NOT "environmental_sample" NOT "EST."[Keyword] NOT "UNVERIFIED"[keyword])',  # entrez_qualifier, NOT "PREDICTED"[keyword]
                    "800"),  # max_length
            "rbcL": (
                "rbcL\nribulose-1,5-bisphosphate carboxylase\nribulose-bisphosphate carboxylase\nrubisco large subunit",
                # key_annotations
                "mitochondrion\nmitochondrial",  # exclude_sources
                "0.00001",  # expect_value
                "2 1",  # gap_costs
                "15",  # word_size
                "1",  # reward
                "-2",  # penalty
                '(("rbcL" OR "ribulose-1,5-bisphosphate carboxylase") NOT "environmental sample" NOT "environmental_sample")',
                # entrez_qualifier
                "1500"),  # max_length
            "matK": ("matK\nmaturase K",  # key_annotations
                     "mitochondrion\nmitochondrial",  # exclude_sources
                     "0.00001",  # expect_value
                     "2 1",  # gap_costs
                     "15",  # word_size
                     "1",  # reward
                     "-2",  # penalty
                     '(("matK" OR "maturase K") NOT "environmental sample" NOT "environmental_sample")',  # entrez_qualifier
                     "1600"),  # max_length
            "trnL-trnF": ("trnL-F\ntrnL\ntrnF\ntRNA-Leu\ntRNA-Phe",
                          "mitochondrion\nmitochondrial",
                          "0.001",  # expect_value
                          "2 1",  # gap_costs
                          "7",  # word_size
                          "1",  # reward
                          "-1",  # penalty
                          '("trnL-trnF" OR "trnL-F" OR ("trnL" AND "trnF") OR ("tRNA-Leu" AND "tRNA-Phe")) NOT "environmental sample" NOT "environmental_sample"',
                          "450"),
            "psbA-trnH": ("psbA-trnH\npsbA\ntrnH\nphotosystem II protein D1\ntRNA-His",
                          "mitochondrion\nmitochondrial",
                          "0.001",  # expect_value
                          "2 1",  # gap_costs
                          "7",  # word_size
                          "1",  # reward
                          "-1",  # penalty
                          '("psbA-trnH" OR ("psbA" AND "trnH") OR ("photosystem II protein D1" AND "tRNA-His")) NOT "environmental sample" NOT "environmental_sample"',
                          "420"),
            "ndhF": ("ndhF\nNADH dehydrogenase subunit F\nNADH dehydrogenase subunit 5",  # key_annotations
                     "mitochondrion\nmitochondrial",  # exclude_sources
                     "0.00001",  # expect_value
                     "2 1",  # gap_costs
                     "15",  # word_size
                     "1",  # reward
                     "-2",  # penalty
                     '(("ndhF" OR "NADH dehydrogenase subunit F" OR "NADH dehydrogenase subunit 5") NOT mitochondrion NOT mitochondrial)',
                     # entrez_qualifier
                     "2300"),  # max_length
            "rpoB": ("rpoB\nRNA polymerase beta subunit",  # key_annotations
                     "mitochondrion\nmitochondrial",  # exclude_sources
                     "0.00001",  # expect_value
                     "2 1",  # gap_costs
                     "15",  # word_size
                     "1",  # reward
                     "-2",  # penalty
                     '(("rpoB" OR "RNA polymerase beta subunit") NOT "environmental sample" NOT "environmental_sample")',
                     # entrez_qualifier
                     "3300")
        }'''

        target_region = self.ui.target_region.currentText()
        if target_region == "":
            return

        parameters_dict = {}
        # 先尝试从工作目录读取自定义设置
        blast_params_dir = Path(get_writable_path("blast_parameters"))
        custom_params_file = blast_params_dir / Path(target_region + ".txt")
        
        if custom_params_file.exists():
            # 使用自定义设置
            params_file = custom_params_file
        else:
            # 使用默认设置（资源目录）
            params_file = Path(get_resource_path("blast_parameters")) / Path(target_region + ".txt")
        
        with open(params_file, "r") as fr:
            parameters = fr.read().splitlines()
            for parameter in parameters:
                if parameter.strip() != "":
                    parameters_dict[parameter.split("\t")[0]] = str(parameter.split("\t")[1])

        target_region = parameters_dict["target_region"]
        entrez_qualifier = parameters_dict["entrez_qualifier"]
        max_length = parameters_dict["max_length"]
        key_annotations = parameters_dict["key_annotations"]
        exclude_sources = parameters_dict["exclude_sources"]
        expect_value = parameters_dict["expect_value"]
        gap_costs = parameters_dict["gap_costs"]
        word_size = parameters_dict["word_size"]
        nucl_reward = parameters_dict["nucl_reward"]
        nucl_penalty = parameters_dict["nucl_penalty"]

        self.ui.initial_queries.clear()
        # 先尝试从工作目录读取自定义查询序列
        initial_queries_dir = Path(get_writable_path("initial_queries"))
        custom_queries_dir = initial_queries_dir / Path(target_region)
        
        if custom_queries_dir.exists():
            # 使用自定义查询序列
            queries_dir = custom_queries_dir
        else:
            # 使用默认查询序列（资源目录）
            queries_dir = Path(get_resource_path("initial_queries")) / Path(target_region)
        
        for file in os.listdir(queries_dir):
            with open(queries_dir / Path(file), "r") as fr:
                seq = fr.read()
                self.ui.initial_queries.appendPlainText(seq + "\n")

        self.ui.entrez_qualifier.setPlainText(entrez_qualifier)
        self.ui.max_length.setText(max_length)
        self.ui.expect_value.setText(expect_value)
        self.ui.gap_costs.setText(gap_costs)
        self.ui.word_size.setText(word_size)
        self.ui.nucl_reward.setText(nucl_reward)
        self.ui.nucl_penalty.setText(nucl_penalty)
        self.ui.key_annotations.setText(key_annotations.replace("|", "\n"))
        self.ui.exclude_sources.setPlainText(exclude_sources.replace("|", "\n"))

        print("set target region: %s" % target_region)

    def save_settings(self):
        """

        :return:
        """
        target_region = self.ui.target_region.currentText()
        if target_region.strip() == "":
            print("Please input the target region name and parameters before saving.")
            return

        # this conflict will not happen
        # if os.path.exists(Path("parameters") / Path(target_region+".txt")):
        #     print("Setting for this target region already exists, do you want to replace it?")
        #     QMessageBox.about(self.ui, "Save settings", "Setting for this target region already exists, do you want to replace it?", QMessageBox.No)

        entrez_qualifier = self.ui.entrez_qualifier.toPlainText().strip()
        max_length = self.ui.max_length.text().strip()  # positive integer
        key_annotations = self.ui.key_annotations.text().strip()
        exclude_sources = self.ui.exclude_sources.toPlainText().strip()
        expect_value = self.ui.expect_value.text().strip()  # numeric
        gap_costs = self.ui.gap_costs.text().strip()  # two integer
        word_size = self.ui.word_size.text().strip()  # positive integer
        nucl_reward = self.ui.nucl_reward.text().strip()
        nucl_penalty = self.ui.nucl_penalty.text().strip()

        # 保存到工作目录（可写路径）
        blast_params_dir = Path(get_writable_path("blast_parameters"))
        blast_params_dir.mkdir(parents=True, exist_ok=True)
        
        with open(blast_params_dir / Path(target_region + ".txt"), "w") as fw:
            fw.write("target_region\t" + target_region + "\n")
            fw.write("entrez_qualifier\t" + entrez_qualifier + "\n")
            fw.write("max_length\t" + str(max_length) + "\n")
            fw.write("key_annotations\t" + key_annotations.replace("\n", "|") + "\n")
            fw.write("exclude_sources\t" + exclude_sources.replace("\n", "|") + "\n")
            fw.write("expect_value\t" + str(expect_value) + "\n")
            fw.write("gap_costs\t" + gap_costs + "\n")
            fw.write("word_size\t" + str(word_size) + "\n")
            fw.write("nucl_reward\t" + str(nucl_reward) + "\n")
            fw.write("nucl_penalty\t" + str(nucl_penalty) + "\n")

        initial_queries = self.ui.initial_queries.toPlainText().strip()
        initial_queries_dir = Path(get_writable_path("initial_queries"))
        initial_queries_dir.mkdir(parents=True, exist_ok=True)
        target_region_dir = initial_queries_dir / Path(target_region)
        target_region_dir.mkdir(parents=True, exist_ok=True)
        
        with open(target_region_dir / Path(target_region + ".fasta"), "w") as fw:
            fw.write(initial_queries)

        self.ui.target_region.addItems([target_region])
        self.ui.target_region.setEditable(False)
        self.ui.save_settings.setEnabled(False)
        self.ui.set_target_region.setEnabled(True)
        print("save settings: %s" % target_region)
        # todo: save initial queriess

    def view_wd(self):
        """
        view working directory in the Sequence Retrieving module
        :return: None
        """
        wd = QFileDialog.getExistingDirectory(self.ui, "select directory")
        self.ui.wd.setText(wd)

    def my_esearch(self):
        """
        connects the esearch button in the Sequence Retrieving module with my_esearch function
        :return: None
        """
        from my_entrez import entrez_count, entrez_summary
        
        print_line()
        taxonomy = self.ui.taxonomy.toPlainText().strip()
        if taxonomy == "":
            print("Please input your target groups.")
            return
        organisms = taxonomy.splitlines()
        organisms = [x for x in organisms if len(x) > 0]
        entrez_qualifier = self.ui.entrez_qualifier.toPlainText().strip()
        entrez_email = self.ui.entrez_email.text().strip()
        date_from = self.ui.date_from.text().strip()
        date_to = self.ui.date_to.text().strip()
        #print("Entrez email: %s" % entrez_email)
        if self.ui.marker_summary.isChecked():
            target_region_list = os.listdir(Path(get_resource_path("blast_parameters")))
            target_region_list = [Path(x).stem for x in target_region_list]
            target_region_dict = {}
            for target_region in target_region_list:
                parameters_dict = {}
                with open(Path(get_resource_path("blast_parameters")) / Path(target_region + ".txt"), "r") as fr:
                    parameters = fr.read().splitlines()
                    for parameter in parameters:
                        if parameter.strip() != "":
                            parameters_dict[parameter.split("\t")[0]] = str(parameter.split("\t")[1])
                target_region_dict[target_region] = parameters_dict["entrez_qualifier"]

            self.ui.thread = threading.Thread(target=entrez_summary, args=(entrez_email, organisms, target_region_dict, date_from, date_to))
            self.ui.thread.setDaemon(True)
            self.ui.thread.start()
        else:
            # entrez_query = format_entrez_query(organisms=organisms, entrez_qualifier=entrez_qualifier, date_from=date_from,
            #                                    date_to=date_to)
            self.ui.thread = threading.Thread(target=entrez_count, args=(entrez_email, organisms, entrez_qualifier, date_from, date_to))
            self.ui.thread.setDaemon(True)
            self.ui.thread.start()

    def submit_new_blast(self):
        """
        read the parameters in the Sequence Retrieving module
        connects the submit_new_blast button in the Sequence Retrieving module with multi_blast_main function
        :return:
        """
        from my_entrez import entrez_count
        from iterated_blast import iterated_blast_main
        
        print_line("*")
        print("Submitting New BLAST...")

        # read the current text of BLAST parameters in the Sequence Retrieving module
        target_region = self.ui.target_region.currentText()
        taxonomy = self.ui.taxonomy.toPlainText().strip()
        entrez_qualifier = self.ui.entrez_qualifier.toPlainText().strip()
        entrez_email = self.ui.entrez_email.text().strip()
        max_length = self.ui.max_length.text().strip()  # positive integer
        key_annotations = self.ui.key_annotations.text().strip()
        exclude_sources = self.ui.exclude_sources.toPlainText().strip()
        expect_value = self.ui.expect_value.text().strip()  # numeric
        gap_costs = self.ui.gap_costs.text().strip()  # two integer
        word_size = self.ui.word_size.text().strip()  # positive integer
        nucl_reward = self.ui.nucl_reward.text().strip()
        nucl_penalty = self.ui.nucl_penalty.text().strip()
        initial_queries = self.ui.initial_queries.toPlainText().strip()
        wd = self.ui.wd.text().strip()
        date_from = self.ui.date_from.text().strip()
        date_to = self.ui.date_to.text().strip()

        # check BLAST parameters
        # max_length, word_size: positive integer
        # expect_value: nonnegative number
        # nucl_reward: nonnegative integer
        # nucl_penalty: nonpositive integer
        # gap_costs: two positive integers separated by a space
        try:
            max_length = int(max_length)
        except ValueError:
            print("Invalid value for max_length: %s." % max_length)
            return
        else:
            if max_length < 0:
                print("max_length needs to be a positive integer")
                return

        try:
            word_size = int(word_size)
        except ValueError:
            print("Invalid value for word_size: %s." % word_size)
            print("Please visit https://ncbi.github.io/blast-cloud/dev/api.html for details about allowed values.")
            return
        else:
            if word_size < 0:
                print("word_size needs to be a positive integer")
                print("Please visit https://ncbi.github.io/blast-cloud/dev/api.html for details about allowed values.")
                return

        try:
            expect_value = float(expect_value)
        except ValueError:
            print("Invalid value for expect_value: %s." % expect_value)
            print("Please visit https://ncbi.github.io/blast-cloud/dev/api.html for details about allowed values.")
            return
        else:
            if expect_value < 0:
                print("expect_value needs to be a nonnegative number")
                print("Please visit https://ncbi.github.io/blast-cloud/dev/api.html for details about allowed values.")
                return

        try:
            nucl_reward = int(nucl_reward)
        except ValueError:
            print("Invalid value for nucl_reward: %s." % nucl_reward)
            print("Please visit https://ncbi.github.io/blast-cloud/dev/api.html for details about allowed values.")
            return
        else:
            if nucl_reward < 0:
                print("nucl_reward needs to be a nonnegative integer")
                print("Please visit https://ncbi.github.io/blast-cloud/dev/api.html for details about allowed values.")
                return

        try:
            nucl_penalty = int(nucl_penalty)
        except ValueError:
            print("Invalid value for nucl_penalty: %s." % nucl_penalty)
            print("Please visit https://ncbi.github.io/blast-cloud/dev/api.html for details about allowed values.")
            return
        else:
            if nucl_penalty > 0:
                print("nucl_penalty needs to be a nonpositive integer")
                print("Please visit https://ncbi.github.io/blast-cloud/dev/api.html for details about allowed values.")
                return

        try:
            gap_costs_list = gap_costs.split(" ")
            assert len(gap_costs_list) == 2
        except AssertionError:
            print("Invalid value for gap_costs: %s." % gap_costs)
            print("Please visit https://ncbi.github.io/blast-cloud/dev/api.html for details about allowed values.")
            return
        else:
            try:
                cost0 = int(gap_costs_list[0])
                cost1 = int(gap_costs_list[1])
            except ValueError:
                print("Invalid value for gap_costs: %s." % gap_costs)
                print("Please visit https://ncbi.github.io/blast-cloud/dev/api.html for details about allowed values.")
                return
            else:
                if cost0 < 0 or cost1 < 0:
                    print("gap_costs need to be two positive integers separated by a space")
                    print(
                        "Please visit https://ncbi.github.io/blast-cloud/dev/api.html for details about allowed values.")
                    return

        if not os.path.exists(Path(wd)):
            os.makedirs(Path(wd))
        if not os.path.exists(Path(wd) / Path("parameters")):
            os.makedirs(Path(wd) / Path("parameters"))
        if not os.path.exists(Path(wd) / Path("parameters") / Path("ref_seq")):
            os.makedirs(Path(wd) / Path("parameters") / Path("ref_seq"))
        if not os.path.exists(Path(wd) / Path("parameters") / Path("ref_msa")):
            os.makedirs(Path(wd) / Path("parameters") / Path("ref_msa"))
        if not os.path.exists(Path(wd) / Path("tmp_files")):
            os.makedirs(Path(wd) / Path("tmp_files"))
        if not os.path.exists(Path(wd) / Path("results")):
            os.makedirs(Path(wd) / Path("results"))

        organisms = taxonomy.splitlines()
        organisms = [x for x in organisms if len(x) > 0]
        count = entrez_count(entrez_email, organisms, entrez_qualifier, date_from, date_to)

        # save BLAST parameters in the blast_parameters.txt file
        with open(Path(wd) / Path("parameters") / Path("blast_parameters.txt"), "w") as fw:
            fw.write("target_region\t" + target_region + "\n")
            fw.write("taxonomy\t" + taxonomy.replace("\n", "|") + "\n")
            fw.write("entrez_qualifier\t" + entrez_qualifier + "\n")
            fw.write("date_from\t" + date_from + "\n")
            fw.write("date_to\t" + date_to + "\n")
            fw.write("entrez_email\t" + entrez_email + "\n")
            fw.write("entrez_count\t" + str(count) + "\n")
            fw.write("max_length\t" + str(max_length) + "\n")
            fw.write("key_annotations\t" + key_annotations.replace("\n", "|") + "\n")
            fw.write("exclude_sources\t" + exclude_sources.replace("\n", "|") + "\n")
            fw.write("expect_value\t" + str(expect_value) + "\n")
            fw.write("gap_costs\t" + gap_costs + "\n")
            fw.write("word_size\t" + str(word_size) + "\n")
            fw.write("nucl_reward\t" + str(nucl_reward) + "\n")
            fw.write("nucl_penalty\t" + str(nucl_penalty) + "\n")

        # print("BLAST parameters saved in parameters folder as blast_parameters.txt")
        if len(initial_queries) > 0:
            with open(Path(wd) / Path("parameters") / Path("initial_queries.fasta"), "w") as fw:
                fw.write(initial_queries)
        else:
            print("Please add initial queries!")
            return
        # todo: if only use one query, then no need to align

        key_annotations = key_annotations.splitlines()
        key_annotations = [x for x in key_annotations if len(x) > 0]
        exclude_sources = exclude_sources.splitlines()
        exclude_sources = [x for x in exclude_sources if len(x) > 0]

        ref_number = 5

        self.ui.thread = threading.Thread(target=iterated_blast_main, args=(wd, organisms, count,
                                                                            expect_value, gap_costs, word_size,
                                                                            nucl_reward, nucl_penalty, max_length,
                                                                            key_annotations, exclude_sources,
                                                                            ref_number,
                                                                            date_from, date_to, entrez_email))
        self.ui.thread.setDaemon(True)
        self.ui.thread.start()
        self.ui.submit_new_blast.setEnabled(False)
        self.ui.load_previous_job.setEnabled(False)
        QMessageBox.about(self.ui, "submit_new_blast", "New blast submitted!")

    def load_previous_job(self):
        """
        read BLAST parameters in the blast_parameters.txt file
        connects the load_previous_job button in the Sequence Retrieving module with multi_blast_main function
        :return:
        """
        from iterated_blast import iterated_blast_main
        
        print_line("*")
        print("Loading previous job...")

        # check if the working directory exists
        wd = self.ui.wd.text()
        if not os.path.exists(wd):
            print("Working directory does not exists, please submit new BLAST.")
            return
        if not os.path.exists(Path(wd) / Path("parameters")):
            print("Can't find parameters directory, please submit new BLAST.")
            return
        if not os.path.exists(Path(wd) / Path("tmp_files")):
            print("Can't find tmp_files directory, please submit new BLAST.")
            return
        if not os.path.exists(Path(wd) / Path("results")):
            print("Can't find results directory, please submit new BLAST.")
            return

        # read BLAST parameters in the blast_parameters.txt file
        parameters_files = os.listdir(Path(wd) / Path("parameters"))
        if "blast_parameters.txt" not in parameters_files:
            # todo: check BLAST parameters
            print("Can't find BLAST parameters, please submit new BLAST.")
            return
        if "initial_queries.fasta" not in parameters_files:
            print("Can't find initial queries, please submit new BLAST.")
            return
        else:
            self.ui.initial_queries.clear()
            with open(Path(wd) / Path("parameters") / Path("initial_queries.fasta"), "r") as fr:
                seq = fr.read()
                self.ui.initial_queries.appendPlainText(seq)

        parameters_dict = {}
        with open(Path(wd) / Path("parameters") / Path("blast_parameters.txt"), "r") as fr:
            parameters = fr.read().splitlines()
            for parameter in parameters:
                if parameter.strip() != "":
                    parameters_dict[parameter.split("\t")[0]] = str(parameter.split("\t")[1])

        target_region = parameters_dict["target_region"]
        taxonomy = parameters_dict["taxonomy"]
        entrez_qualifier = parameters_dict["entrez_qualifier"]
        date_from = parameters_dict["date_from"]
        date_to = parameters_dict["date_to"]
        entrez_email = parameters_dict["entrez_email"]
        count = parameters_dict["entrez_count"]
        max_length = int(parameters_dict["max_length"])
        key_annotations = parameters_dict["key_annotations"]
        exclude_sources = parameters_dict["exclude_sources"]
        expect_value = parameters_dict["expect_value"]
        gap_costs = parameters_dict["gap_costs"]
        word_size = parameters_dict["word_size"]
        nucl_reward = parameters_dict["nucl_reward"]
        nucl_penalty = parameters_dict["nucl_penalty"]

        # show parameters in the Sequence Retrieving panel
        # target_region_list = ["ITS", "rbcL", "matK", "trnL-trnF", "psbA-trnH", "ndhF", "rpoB"]
        target_region_list = os.listdir(Path(get_resource_path("blast_parameters")))
        target_region_list = [Path(x).stem for x in target_region_list]
        if target_region in target_region_list:
            target_region_list.remove(target_region)
        target_region_list.insert(0, "")
        target_region_list.insert(0, target_region)
        self.ui.target_region.clear()
        self.ui.target_region.addItems(target_region_list)
        self.ui.taxonomy.setPlainText(taxonomy.replace("|", "\n"))
        self.ui.entrez_qualifier.setPlainText(entrez_qualifier)
        self.ui.date_from.setText(date_from)
        self.ui.date_to.setText(date_to)
        self.ui.entrez_email.setText(entrez_email)
        self.ui.max_length.setText(str(max_length))
        self.ui.expect_value.setText(str(expect_value))
        self.ui.gap_costs.setText(gap_costs)
        self.ui.word_size.setText(str(word_size))
        self.ui.nucl_reward.setText(str(nucl_reward))
        self.ui.nucl_penalty.setText(str(nucl_penalty))
        self.ui.key_annotations.setText(key_annotations.replace("|", "\n"))
        self.ui.exclude_sources.setPlainText(exclude_sources.replace("|", "\n"))

        organisms = taxonomy.split("|")
        organisms = [x for x in organisms if len(x) > 0]
        key_annotations = key_annotations.split("|")
        key_annotations = [x for x in key_annotations if len(x) > 0]
        exclude_sources = exclude_sources.split("|")
        exclude_sources = [x for x in exclude_sources if len(x) > 0]

        # todo: show warnings when the size of queries file is zero
        queries_file_list = os.listdir(Path(wd) / Path("parameters") / Path("ref_seq"))
        if len(queries_file_list) > 0:
            round_list = []
            for queries_file in queries_file_list:
                round_list.append(int(Path(queries_file).stem.split("_")[-1]))
            round_list.sort()
            blast_round = round_list[-1]
        else:
            blast_round = 1
        ref_number = 5
        count = int(count)
        self.ui.thread = threading.Thread(target=iterated_blast_main, args=(wd, organisms, count,
                                                                            expect_value, gap_costs, word_size,
                                                                            nucl_reward, nucl_penalty, max_length,
                                                                            key_annotations, exclude_sources,
                                                                            ref_number,
                                                                            date_from, date_to, entrez_email,
                                                                            blast_round))
        self.ui.thread.setDaemon(True)
        self.ui.thread.start()
        self.ui.submit_new_blast.setEnabled(False)
        self.ui.load_previous_job.setEnabled(False)
        QMessageBox.about(self.ui, "load_previous_job", "Previous job loaded!")

    def stop_current_job(self):
        pass
        # todo: stop thread by raising exception
        # todo: release resources

    # -------------------------------- Supermatrix Construction ----------------------------------
    # view input path and output path of Sequence Filtering
    def view_in_path1(self):
        # if self.ui.buttonGroup.checkedButton().text() == "Remove exceptional records":
        #     path = QFileDialog.getOpenFileName(self.ui, "select file path", r"D:\\", "file type (*.fasta *.fas *.fa)")
        #     self.ui.in_path1.setText(path[0])
        # elif self.ui.buttonGroup.checkedButton().text() == "Combine species":
        #     path = QFileDialog.getOpenFileName(self.ui, "select file path", r"D:\\", "file type (*.fasta *.fas *.fa)")
        #     self.ui.in_path1.setText(path[0])
        # else:
        #     path = QFileDialog.getExistingDirectory(self.ui, "select file path", r"D:\\")
        #     self.ui.in_path1.setText(path)
        path = QFileDialog.getExistingDirectory(self.ui, "select file path", r"D:\\")
        self.ui.in_path1.setText(path)


    def view_out_path1(self):
        path = QFileDialog.getExistingDirectory(self.ui, "select file path", r"D:\\")
        self.ui.out_path1.setText(path)

    # view input path and output path of Sequence Alignment
    def view_in_path2(self):
        if self.ui.buttonGroup_2.checkedButton().text() == "input one file":
            path = QFileDialog.getOpenFileName(self.ui, "select file path", r"D:\\", "file type (*.fasta *.fas *.fa)")
            self.ui.in_path2.setText(path[0])
        else:
            path = QFileDialog.getExistingDirectory(self.ui, "select file path", r"D:\\")
            self.ui.in_path2.setText(path)

    def view_out_path2(self):
        path = QFileDialog.getExistingDirectory(self.ui, "select file path", r"D:\\")
        self.ui.out_path2.setText(path)

    # view input path and output path of Alignments Trimming
    def view_in_path3(self):
        if self.ui.buttonGroup_3.checkedButton().text() == "input one file":
            path = QFileDialog.getOpenFileName(self.ui, "select file path", r"D:\\", "file type (*.fasta *.fas *.fa)")
            self.ui.in_path3.setText(path[0])
        else:
            path = QFileDialog.getExistingDirectory(self.ui, "select file path", r"D:\\")
            self.ui.in_path3.setText(path)

    def view_out_path3(self):
        path = QFileDialog.getExistingDirectory(self.ui, "select file path", r"D:\\")
        self.ui.out_path3.setText(path)

    # view input path and output path of Alignments Concatenation
    def view_in_path4(self):
        path = QFileDialog.getExistingDirectory(self.ui, "select file path", r"D:\\")
        self.ui.in_path4.setText(path)

    def view_out_path4(self):
        path = QFileDialog.getExistingDirectory(self.ui, "select file path", r"D:\\")
        self.ui.out_path4.setText(path)

    def view_in_path5(self):
        path = QFileDialog.getOpenFileName(self.ui, "select file path", r"D:\\",
                                           "file type (*.fasta *.fas *.fa *.phylip *.phy)")
        self.ui.in_path5.setText(path[0])

    def set_marker_summary(self):
        """

        :return:
        """
        if self.ui.marker_summary.isChecked():
            self.ui.entrez_qualifier.clear()
            self.ui.entrez_qualifier.setEnabled(False)
            self.ui.target_region.setCurrentIndex(0)
            self.ui.target_region.setEnabled(False)
            self.ui.save_settings.setEnabled(False)

        else:
            self.ui.entrez_qualifier.setEnabled(True)
            self.ui.target_region.setEnabled(True)
            self.ui.save_settings.setEnabled(True)

    def set_reduce_threshold(self):
        """

        :return:
        """
        if self.ui.reduce_dataset.isChecked():
            self.ui.len_threshold.setEnabled(True)
            self.ui.consensus_value.setEnabled(True)
        else:
            self.ui.len_threshold.setEnabled(False)
            self.ui.consensus_value.setEnabled(False)

    def run_filtering2(self):
        from my_filter import call_miner_filter
        
        in_path1 = self.ui.in_path1.text().strip()
        # out_path1 = self.ui.out_path1.text().strip()
        out_path1 = in_path1
        len_threshold = int(self.ui.len_threshold.text().strip())
        consensus_value = eval(self.ui.consensus_value.currentText().strip())
        # print(consensus_value)
        name_correction = False

        if self.ui.control_extension.isChecked() and self.ui.reduce_dataset.isChecked():
            print("Control extension and reduce dataset...")
            action = 3
            self.ui.thread = threading.Thread(target=call_miner_filter,
                                              args=(in_path1, out_path1, action, consensus_value, len_threshold, name_correction))
            self.ui.thread.setDaemon(True)
            self.ui.thread.start()
        elif self.ui.control_extension.isChecked():
            print("Control extension...")
            action = 1  # call_miner_filter(in_path, out_path, action, len_shresh, max_num)
            self.ui.thread = threading.Thread(target=call_miner_filter,
                                              args=(in_path1, out_path1, action, len_threshold, name_correction))
            self.ui.thread.setDaemon(True)
            self.ui.thread.start()
        elif self.ui.reduce_dataset.isChecked():
            print("Reduce dataset...")
            action = 2
            self.ui.thread = threading.Thread(target=call_miner_filter,
                                              args=(in_path1, out_path1, action, len_threshold, name_correction))
            self.ui.thread.setDaemon(True)
            self.ui.thread.start()

        else:
            print("Please select one option.")                                                

    def run_alignment(self):
        """
        connects the running button of Sequence Alignment with the call_mafft function
        :return: None
        """
        self.check_dependencies()
        from call_mafft2 import mafft
        
        in_path2 = self.ui.in_path2.text().strip()
        out_path2 = self.ui.out_path2.text().strip()
        if not os.path.exists(out_path2):
            os.makedirs(out_path2)
        # ali_mod = eval(self.ui.ali_mod.currentText().strip())
        # ali_cmd = self.ui.ali_cmd.toPlainText().strip()
        # ali_add_cho = self.ui.ali_add_cho.currentText().strip()
        # ali_add_path = self.ui.ali_add_path.text().strip()
        ali_alg = self.ui.ali_alg.currentText().strip().split(" ")[0]  # algorithm, auto, add
        ali_thr = self.ui.ali_thr.text().strip()  # thread
        ali_reo = eval(self.ui.ali_reo.currentText().strip())  # reorder
        # ali_add_par = self.ui.ali_add_par.text().strip()
        ali_mod = False
        ali_cmd = ""
        ali_add_cho = ""
        ali_add_path = ""
        ali_add_par = ""

        """in_path, out_path = '', add_choice = '', add_path = '', algorithm = 'auto',
        thread = -1, reorder = True, additional_params = '',
        pure_command_mode = False, pure_command = ''"""
        self.ui.thread = threading.Thread(target=mafft, args=(in_path2, out_path2, ali_add_cho, ali_add_path,
                                                              ali_alg, ali_thr, ali_reo, ali_add_par, ali_mod, ali_cmd))
        print("Running alignment...")
        self.ui.thread.setDaemon(True)
        self.ui.thread.start()

        # print(yiyang.call_mafft.mafft(in_path=in_path2, out_path=out_path2, add_choice=ali_add_cho, add_path=ali_add_path,
        #                               algorithm=ali_alg, thread=ali_thr, reorder=ali_reo, additional_params=ali_add_par,
        #                               pure_command_mode=ali_mod, pure_command=ali_cmd))

    def select_tri_method(self):
        """

        :return:
        """
        tri_method = self.ui.tri_met.currentText()
        if tri_method == "user defined method (set thresholds of non gap, similarity, consistency...)":
            self.ui.tri_gt.setEnabled(True)
            self.ui.tri_st.setEnabled(True)
            self.ui.tri_ct.setEnabled(True)
            self.ui.tri_con.setEnabled(True)
        else:
            self.ui.tri_gt.clear()
            self.ui.tri_st.clear()
            self.ui.tri_ct.clear()
            self.ui.tri_con.clear()
            self.ui.tri_gt.setEnabled(False)
            self.ui.tri_st.setEnabled(False)
            self.ui.tri_ct.setEnabled(False)
            self.ui.tri_con.setEnabled(False)

    def run_trimming(self):
        """
        connects the running button of Alignments Trimming with the call_trimal function
        :return: None
        """
        self.check_dependencies()
        from call_trimal import trimal
        
        in_path3 = self.ui.in_path3.text().strip()
        out_path3 = self.ui.out_path3.text().strip()
        if not os.path.exists(out_path3):
            os.makedirs(out_path3)
        tri_met = self.ui.tri_met.currentText().strip().split(" ")[0]
        if tri_met == "user":
            tri_met = ""
        # tri_htm = eval(self.ui.tri_htm.currentText().strip())
        # tri_bpl = eval(self.ui.tri_bpl.currentText().strip())
        tri_htm = True
        tri_bpl = False
        tri_gt = self.ui.tri_gt.text().strip()
        tri_st = self.ui.tri_st.text().strip()
        tri_ct = self.ui.tri_ct.text().strip()
        tri_con = self.ui.tri_con.text().strip()
        # tri_add_par = self.ui.ali_add_par.text().strip()
        # tri_mod = eval(self.ui.tri_mod.currentText().strip())
        # tri_cmd = self.ui.tri_cmd.toPlainText().strip()
        tri_add_par = ""
        tri_mod = False
        tri_cmd = ""
        """
            in_path, out_path='',
           htmlout=True, bp_length=False,
           implement_methods='automated1', gt='', st='', ct='', cons='',
           additional_params='', pure_command_mode=False, pure_command=''
        """
        self.ui.thread = threading.Thread(target=trimal, args=(in_path3, out_path3,
                                                               tri_htm, tri_bpl, tri_met,
                                                               tri_gt, tri_st, tri_ct, tri_con,
                                                               tri_add_par, tri_mod, tri_cmd))
        print("Running trimming...")
        self.ui.thread.setDaemon(True)
        self.ui.thread.start()

        # print(yiyang.call_trimal.trimal(in_path=in_path3, out_path=out_path3,
        #                          htmlout=tri_htm, bp_length=tri_bpl, implement_methods=tri_met,
        #                          gt=tri_gt, st=tri_st, ct=tri_ct, cons=tri_con,
        #                          additional_params=tri_add_par, pure_command_mode=tri_mod, pure_command=tri_cmd))

    def run_concatenation(self):
        """
        connects the running button of Alignments Concatenation with the my_concatenation function
        :return: None
        """
        from my_concatenation import my_concatenation
        
        in_path4 = self.ui.in_path4.text().strip()
        out_path4 = self.ui.out_path4.text().strip()
        if not os.path.exists(out_path4):
            os.makedirs(out_path4)
        self.ui.thread = threading.Thread(target=my_concatenation, args=(in_path4, out_path4))
        print("Running concatenation...")
        self.ui.thread.setDaemon(True)
        self.ui.thread.start()


def main():
    app = QApplication([])
    
    app.setAttribute(Qt.AA_EnableHighDpiScaling)
    app.setAttribute(Qt.AA_UseHighDpiPixmaps)
    
    app.setApplicationName("PyNCBIminer")
    app.setOrganizationName("PyNCBIminer")
    app.setApplicationDisplayName("PyNCBIminer")
    
    icon_path = get_resource_path(os.path.join("icons", "app_icon.ico"))
    if os.path.exists(icon_path):
        app.setWindowIcon(QIcon(icon_path))
    
    main_window = MainWindow()
    
    if os.path.exists(icon_path):
        main_window.setWindowIcon(QIcon(icon_path))
    
    main_window.show()
    
    if sys.platform == 'win32':
        try:
            app_user_model_id = "PyNCBIminer.PyNCBIminer.1.2.12"
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(app_user_model_id)
        except:  # noqa: E722
            pass
    
    sys.exit(app.exec_())


if __name__ == "__main__":
   # todo: print cannot show?
    # (_OLD_VIRTUAL_PATH)
    # root_path = os.path.abspath(os.path.dirname(__file__))  # running dir
    main()
    #
    # # use uiload
    # app = QApplication([])
    # main_window = MainWindow()
    # main_window.ui.show()
    # sys.exit(app.exec_())




