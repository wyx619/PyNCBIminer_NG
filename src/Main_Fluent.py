
import sys
from pathlib import Path

from PySide6.QtCore import (
    QDate,
    QEventLoop,
    QObject,
    Qt,
    QTimer,
    Signal,
    Slot,
)
from PySide6.QtGui import QIcon, QTextCursor
from PySide6.QtWidgets import (
    QApplication,
    QFileDialog,
    QHBoxLayout,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)
from qfluentwidgets import (
    BodyLabel,
    CardWidget,
    CheckBox,
    ColorPickerButton,
    ComboBox,
    DatePicker,
    ExpandSettingCard,
    FluentWindow,
    InfoBar,
    InfoBarPosition,
    LineEdit,
    NavigationItemPosition,
    PlainTextEdit,
    PrimaryPushButton,
    PushButton,
    RadioButton,
    SegmentedWidget,
    SettingCardGroup,
    SingleDirectionScrollArea,
    SubtitleLabel,
    SwitchButton,
    TextEdit,
    Theme,
    ToolTipFilter,
    ToolTipPosition,
    setTheme,
    setThemeColor,
)
from qfluentwidgets import (
    FluentIcon as FIF,
)

from main_utils import BackendController


def get_resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except AttributeError:
        base_path = str(Path(__file__).parent)
    return str(Path(base_path) / relative_path)


def get_writable_path(relative_path):
    return str(Path.cwd() / relative_path)


class EmittingStr(QObject):
    textWritten = Signal(str)

    def write(self, text):
        self.textWritten.emit(str(text))
        loop = QEventLoop()
        QTimer.singleShot(10, loop.quit)
        loop.exec()

    def flush(self):
        pass


class LogWidget(CardWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.vBoxLayout = QVBoxLayout(self)
        self.headerLabel = SubtitleLabel("Console Output", self)
        self.textEdit = TextEdit(self)
        self.textEdit.setReadOnly(True)
        self.textEdit.setPlaceholderText(
            "Welcome to PyNCBIminer-NG! Output will appear here..."
        )

        self.vBoxLayout.addWidget(self.headerLabel)
        self.vBoxLayout.addWidget(self.textEdit)

    def append_text(self, text):
        cursor = self.textEdit.textCursor()
        cursor.movePosition(QTextCursor.End)
        cursor.insertText(text)
        self.textEdit.setTextCursor(cursor)
        self.textEdit.ensureCursorVisible()


class RetrievalInterface(QWidget):
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        self.date_from_cleared = True
        self.date_to_cleared = True
        self.setObjectName("retrieval_interface")

        self.vBoxLayout = QVBoxLayout(self)
        self.pivot = SegmentedWidget(self)
        self.stackedWidget = QStackedWidget(self)

        self.page_retrieval = self.create_retrieval_page()
        self.page_filter = self.create_filtering_page()

        self.addSubInterface(self.page_retrieval, "retrieval", "Sequence Retrieval")
        self.addSubInterface(self.page_filter, "filter", "Sequence Filtering")

        self.vBoxLayout.addWidget(self.pivot)
        self.vBoxLayout.addWidget(self.stackedWidget)
        self.vBoxLayout.setContentsMargins(30, 25, 30, 15)

        self.stackedWidget.setCurrentWidget(self.page_retrieval)
        self.pivot.setCurrentItem("retrieval")
        self.pivot.currentItemChanged.connect(
            lambda k: self.stackedWidget.setCurrentWidget(self.findChild(QWidget, k))
        )

    def addSubInterface(self, widget: QWidget, objectName, text):
        widget.setObjectName(objectName)
        self.stackedWidget.addWidget(widget)
        self.pivot.addItem(routeKey=objectName, text=text)

    def create_retrieval_page(self):
        w = SingleDirectionScrollArea()
        w.setWidgetResizable(True)
        view = QWidget()
        vBoxLayout = QVBoxLayout(view)
        vBoxLayout.setContentsMargins(5, 20, 25, 20)
        vBoxLayout.setSpacing(20)

        wd_group = SettingCardGroup("Working Directory", view)
        wd_card = CardWidget(view)
        wd_card.setFixedHeight(60)
        wd_layout = QHBoxLayout(wd_card)
        wd_layout.setContentsMargins(15, 10, 15, 10)
        self.wd_edit = LineEdit(wd_card)
        self.wd_edit.setPlaceholderText("Absolute path of working directory")
        self.btn_wd_view = PushButton("Browse", wd_card)
        self.btn_wd_view.setIcon(FIF.FOLDER)
        wd_layout.addWidget(BodyLabel("Path:"))
        wd_layout.addWidget(self.wd_edit)
        wd_layout.addWidget(self.btn_wd_view)
        wd_group.addSettingCard(wd_card)
        vBoxLayout.addWidget(wd_group)

        basic_group = SettingCardGroup("Basic BLAST Parameters", view)

        tax_card = CardWidget(view)
        tax_card.setFixedHeight(150)
        tax_layout = QVBoxLayout(tax_card)
        tax_layout.setContentsMargins(15, 10, 15, 15)
        tax_layout.addWidget(BodyLabel("Target Taxa:"))
        self.tax_edit = PlainTextEdit(tax_card)
        self.tax_edit.setPlaceholderText("Enter taxon names (one per line)")
        self.tax_edit.setFixedHeight(100)
        tax_layout.addWidget(self.tax_edit)
        basic_group.addSettingCard(tax_card)

        region_card = CardWidget(view)
        region_card.setFixedHeight(80)
        reg_layout = QHBoxLayout(region_card)
        reg_layout.setContentsMargins(15, 10, 15, 10)
        self.combo_region = ComboBox(region_card)
        self.combo_region.setMaxVisibleItems(6)

        blast_params_dir = Path(get_writable_path("blast_parameters"))
        default_params_dir = Path(get_resource_path("blast_parameters"))

        marker_set = set()
        marker_set.add("")

        if blast_params_dir.exists():
            for f in blast_params_dir.iterdir():
                if f.is_file() and f.suffix == ".txt":
                    marker_set.add(f.stem)

        if default_params_dir.exists():
            for f in default_params_dir.iterdir():
                if f.is_file() and f.suffix == ".txt":
                    marker_set.add(f.stem)

        markers = sorted(marker_set, key=lambda x: (x != "", x))
        self.combo_region.addItems(markers)

        self.new_region_edit = LineEdit(region_card)
        self.new_region_edit.setPlaceholderText("Enter new region name")
        self.new_region_edit.setEnabled(False)
        self.new_region_edit.setFixedWidth(180)

        self.btn_set_region = PrimaryPushButton("Set Region", region_card)
        self.btn_save_settings = PushButton("Save Settings", region_card)
        reg_layout.addWidget(BodyLabel("Target Region:"))
        reg_layout.addWidget(self.combo_region)
        reg_layout.addWidget(self.new_region_edit)
        reg_layout.addWidget(self.btn_set_region)
        reg_layout.addWidget(self.btn_save_settings)
        basic_group.addSettingCard(region_card)

        entrez_card = CardWidget(view)
        entrez_card.setFixedHeight(160)
        ent_layout = QHBoxLayout(entrez_card)
        ent_layout.setContentsMargins(15, 10, 15, 10)
        ent_layout.setSpacing(20)

        left_col = QVBoxLayout()
        left_col.setContentsMargins(0, 0, 0, 0)
        left_col.setSpacing(6)
        left_col.addWidget(BodyLabel("Entrez Qualifier:"))
        self.entrez_qualifier = PlainTextEdit(entrez_card)
        self.entrez_qualifier.setPlaceholderText(
            "Constraint on BLAST search (Entrez Qualifier)"
        )
        left_col.addWidget(self.entrez_qualifier, 1)
        ent_layout.addLayout(left_col, 1)

        right_col = QVBoxLayout()
        right_col.setContentsMargins(0, 0, 0, 0)
        right_col.setSpacing(8)
        right_col.addStretch(1)

        label_w = 80
        lbl_email = BodyLabel("Email:")
        lbl_email.setFixedWidth(label_w)
        lbl_from = BodyLabel("Date From:")
        lbl_from.setFixedWidth(label_w)
        lbl_to = BodyLabel("Date To:")
        lbl_to.setFixedWidth(label_w)

        row_email = QHBoxLayout()
        self.email_edit = LineEdit(entrez_card)
        self.email_edit.setPlaceholderText("Your Email")
        row_email.addWidget(lbl_email)
        row_email.addWidget(self.email_edit, 1)
        right_col.addLayout(row_email)

        row_from = QHBoxLayout()
        self.date_from = DatePicker(entrez_card)
        self.date_from.setDate(QDate())
        self.date_from_cleared = True
        self.date_from.dateChanged.connect(self.on_date_from_changed)
        self.btn_clear_from = PushButton("Reset", entrez_card)
        self.btn_clear_from.clicked.connect(self.clear_date_from)
        row_from.addWidget(lbl_from)
        row_from.addWidget(self.date_from, 1)
        row_from.addWidget(self.btn_clear_from)
        right_col.addLayout(row_from)

        row_to = QHBoxLayout()
        self.date_to = DatePicker(entrez_card)
        self.date_to.setDate(QDate())
        self.date_to_cleared = True
        self.date_to.dateChanged.connect(self.on_date_to_changed)
        self.btn_clear_to = PushButton("Reset", entrez_card)
        self.btn_clear_to.clicked.connect(self.clear_date_to)
        row_to.addWidget(lbl_to)
        row_to.addWidget(self.date_to, 1)
        row_to.addWidget(self.btn_clear_to)
        right_col.addLayout(row_to)
        right_col.addStretch(1)

        ent_layout.addLayout(right_col, 1)

        basic_group.addSettingCard(entrez_card)

        action_card = CardWidget(view)
        action_card.setFixedHeight(80)
        act_layout = QHBoxLayout(action_card)
        act_layout.setContentsMargins(15, 10, 15, 10)
        self.chk_summary = CheckBox("Summarize widely used marker", action_card)
        self.chk_summary.setToolTip(
            "If checked, Entrez search will count records for commonly used\n"
            "DNA barcode markers (e.g., rbcL, matK, ITS, trnH-psbA, etc.)\n"
            "across the specified taxonomy and date range."
        )
        self.btn_esearch = PrimaryPushButton("Entrez Search", action_card)
        self.btn_esearch.setIcon(FIF.SEARCH)
        act_layout.addWidget(self.chk_summary)
        act_layout.addStretch(1)
        act_layout.addWidget(self.btn_esearch)
        basic_group.addSettingCard(action_card)

        vBoxLayout.addWidget(basic_group)

        adv_group = ExpandSettingCard(
            FIF.SETTING, "Advanced BLAST Parameters", "Click to expand configuration"
        )
        adv_group.setExpand(True)
        adv_view = QWidget()
        adv_layout = QVBoxLayout(adv_view)

        adv_layout.addWidget(BodyLabel("Initial Queries (Fasta):"))
        self.init_queries = PlainTextEdit()
        self.init_queries.setPlaceholderText("Paste sequences in fasta format here")
        self.init_queries.setFixedHeight(200)
        adv_layout.addWidget(self.init_queries)

        grid_layout = QHBoxLayout()
        col1 = QVBoxLayout()
        col2 = QVBoxLayout()

        self.key_anno = PlainTextEdit()
        self.key_anno.setPlaceholderText("Separated by semicolons")
        self.key_anno.setFixedHeight(60)
        col1.addWidget(BodyLabel("Key Annotations:"))
        col1.addWidget(self.key_anno)

        self.excl_source = PlainTextEdit()
        self.excl_source.setPlaceholderText("One keyword per line")
        self.excl_source.setFixedHeight(265)
        col1.addWidget(BodyLabel("Exclude Sources:"))
        col1.addWidget(self.excl_source)
        col1.addStretch(2)

        self.max_len = LineEdit()
        self.max_len.setPlaceholderText("Integer")
        self.word_size = LineEdit()
        self.word_size.setPlaceholderText("Positive integer")
        self.gap_costs = LineEdit()
        self.gap_costs.setPlaceholderText(
            "two positive integers separated  such as '11 1' "
        )
        self.expect_val = LineEdit()
        self.expect_val.setPlaceholderText("Nonnegative number")
        self.nucl_reward = LineEdit()
        self.nucl_reward.setPlaceholderText("Nonnegative number")
        self.nucl_penalty = LineEdit()
        self.nucl_penalty.setPlaceholderText("Nonpositive integer")

        col2.addWidget(BodyLabel("Max Length:"))
        col2.addWidget(self.max_len)
        col2.addWidget(BodyLabel("Word Size:"))
        col2.addWidget(self.word_size)
        col2.addWidget(BodyLabel("Gap Costs:"))
        col2.addWidget(self.gap_costs)
        col2.addWidget(BodyLabel("Expect Value:"))
        col2.addWidget(self.expect_val)
        col2.addWidget(BodyLabel("Nucl Reward:"))
        col2.addWidget(self.nucl_reward)
        col2.addWidget(BodyLabel("Nucl Penalty:"))
        col2.addWidget(self.nucl_penalty)
        col2.addStretch(1)

        grid_layout.addLayout(col1, 1)
        grid_layout.addSpacing(10)
        grid_layout.addLayout(col2, 1)
        adv_layout.addLayout(grid_layout)

        adv_group.viewLayout.addWidget(adv_view)
        vBoxLayout.addWidget(adv_group)

        self.btn_submit_blast = PrimaryPushButton("Submit New BLAST", view)
        self.btn_submit_blast.setIcon(FIF.PLAY)
        self.btn_load_job = PushButton("Load Previous Job", view)
        self.btn_load_job.setIcon(FIF.HISTORY)
        self.btn_stop = PushButton("Stop", view)
        self.btn_stop.setIcon(FIF.CLOSE)
        self.btn_stop.setEnabled(False)

        btn_row = QHBoxLayout()
        btn_row.addWidget(self.btn_submit_blast)
        btn_row.addWidget(self.btn_load_job)
        vBoxLayout.addLayout(btn_row)

        self.chk_summary.stateChanged.connect(
            lambda state: (
                self.btn_submit_blast.setDisabled(state != 0),
                self.btn_load_job.setDisabled(state != 0),
                self.btn_stop.setDisabled(state != 0),
            )
        )

        stop_row = QHBoxLayout()
        stop_row.addWidget(self.btn_stop)
        vBoxLayout.addLayout(stop_row)

        vBoxLayout.addStretch(1)

        w.setWidget(view)
        w.setObjectName("retrieval_page")
        w.setStyleSheet("QScrollArea {border: none; background:transparent}")
        view.setStyleSheet("QWidget {background:transparent}")

        self.btn_wd_view.clicked.connect(self.select_wd)

        return w

    def create_filtering_page(self):
        w = QWidget()
        layout = QVBoxLayout(w)
        layout.setContentsMargins(5, 20, 5, 20)

        grp = SettingCardGroup("Filtering Parameters", w)

        card_opts = CardWidget()
        card_opts.setFixedHeight(260)
        l_opts = QVBoxLayout(card_opts)
        l_opts.setContentsMargins(15, 10, 15, 10)

        row1 = QHBoxLayout()
        self.switch_ext = SwitchButton(card_opts)
        self.switch_ext.setChecked(True)
        lbl_ext = BodyLabel("Extended Segments Refinement:")

        lbl_ext.setToolTip(
            "Trims potentially non-homologous regions introduced by sequence extension.\n"
            "1) Split by genus; \n"
            "2) Align longer seqs with MAFFT, then add shorter via --addfragments;\n"
            "3) Merge genera with <5 seqs into the largest genus of same family;\n"
            "4) Delete extensions where gaps exceed 50%."
        )
        row1.addWidget(lbl_ext)
        row1.addWidget(self.switch_ext)
        row1.addStretch()
        l_opts.addLayout(row1)
        self.switch_ext.setFixedHeight(35)
        row2 = QHBoxLayout()
        self.switch_reduce = SwitchButton(card_opts)
        self.switch_reduce.setChecked(False)
        self.switch_reduce.checkedChanged.connect(self.on_switch_reduce_changed)
        lbl_select = BodyLabel("Species-level Sequence Selection:")
        lbl_select.setToolTip(
            "Select one representative sequence per species.\n"
            "Method 1 (Abnormality Index): compares each sequence to the species consensus;\n"
            "Method 2: balances sequence length and BLAST bit-score;\n"
            "Preference: voucher → published → most recent → length + BLAST rank."
        )
        row2.addWidget(lbl_select)
        row2.addWidget(self.switch_reduce)
        row2.addStretch(1)

        #row2.addSpacing(40)
        self.chk_consensus = CheckBox("Abnormal Index:", card_opts)
        self.chk_consensus.setToolTip(
            "Calculates consensus sequence per species via MAFFT alignment,\n"
            "then scores each sequence by pairwise identity (PI) against the consensus.\n"
            "Low-PI (potentially misidentified / misannotated) sequences are deprioritized."
        )
        self.chk_consensus.setChecked(True)
        self.chk_consensus.setEnabled(False)
        row2.addWidget(self.chk_consensus)
        row2.addStretch(1)
        #row2.addSpacing(40)
        lbl_len = BodyLabel("Length Threshold:")
        lbl_len.setToolTip(
            "Minimum non-ambiguous (A/T/C/G) base count for a sequence to be retained.\n"
            "Sequences shorter than this value are removed before species-level selection."
        )
        row2.addWidget(lbl_len)
        self.len_thresh = LineEdit()
        self.len_thresh.setText("100")
        self.len_thresh.setEnabled(False)
        self.len_thresh.setMinimumWidth(80)
        row2.addWidget(self.len_thresh)
        l_opts.addLayout(row2)

        row_tnrs = QHBoxLayout()
        lbl_tnrs = BodyLabel("Taxonomic Name Resolution:")
        lbl_tnrs.setToolTip(
            "Enable online scientific-name standardization via TNRS API\n"
            "before species-level selection. Unmatched names keep original values."
        )
        row_tnrs.addWidget(lbl_tnrs)
        self.filter_tnrs_switch = SwitchButton(card_opts)
        self.filter_tnrs_switch.setChecked(False)
        self.filter_tnrs_switch.setEnabled(False)
        self.filter_tnrs_switch.checkedChanged.connect(self.on_filter_tnrs_switch_changed)
        row_tnrs.addWidget(self.filter_tnrs_switch)
        row_tnrs.addStretch(1)

        lbl_filter_tnrs_src = BodyLabel("Source:")
        lbl_filter_tnrs_src.setToolTip(
            "TNRS data sources for name resolution.\n"
            "wcvp: World Checklist of Vascular Plants (Kew);\n"
            "wfo: World Flora Online. At least one required."
        )
        row_tnrs.addWidget(lbl_filter_tnrs_src)
        self.filter_tnrs_wfo = CheckBox("wfo", card_opts)
        self.filter_tnrs_wfo.setChecked(False)
        self.filter_tnrs_wfo.setEnabled(False)
        self.filter_tnrs_wcvp = CheckBox("wcvp", card_opts)
        self.filter_tnrs_wcvp.setChecked(True)
        self.filter_tnrs_wcvp.setEnabled(False)
        row_tnrs.addWidget(self.filter_tnrs_wfo)
        row_tnrs.addWidget(self.filter_tnrs_wcvp)
        row_tnrs.addStretch(1)

        lbl_filter_tnrs_acc = BodyLabel("Accuracy:")
        lbl_filter_tnrs_acc.setToolTip(
            "Minimum matching accuracy (0 < value <= 1).\n"
            "Higher values require stricter name matches. Default 0.9."
        )
        row_tnrs.addWidget(lbl_filter_tnrs_acc)
        self.filter_tnrs_accuracy = LineEdit()
        self.filter_tnrs_accuracy.setText("0.9")
        self.filter_tnrs_accuracy.setMinimumWidth(80)
        self.filter_tnrs_accuracy.setEnabled(False)
        row_tnrs.addWidget(self.filter_tnrs_accuracy)
        #row_tnrs.addStretch(1)
        l_opts.addLayout(row_tnrs)

        row3 = QHBoxLayout()
        self.filter_in = LineEdit()
        self.filter_in.setPlaceholderText(
            "One working directory"
        )
        btn_in = PushButton("Browse")
        btn_in.setIcon(FIF.FOLDER)
        btn_in.clicked.connect(lambda: self.browse_dir(self.filter_in))
        lbl_in = BodyLabel("Input Directory:")
        lbl_in.setFixedWidth(150)
        row3.addWidget(lbl_in)
        row3.addWidget(self.filter_in, 1)
        row3.addWidget(btn_in)
        l_opts.addLayout(row3)

        row4 = QHBoxLayout()
        self.filter_out = LineEdit()
        self.filter_out.setPlaceholderText("The same as input path by default")
        btn_out = PushButton("Browse")
        btn_out.setIcon(FIF.FOLDER)
        btn_out.clicked.connect(lambda: self.browse_dir(self.filter_out))
        lbl_out = BodyLabel("Output Directory:")
        lbl_out.setFixedWidth(150)
        row4.addWidget(lbl_out)
        row4.addWidget(self.filter_out, 1)
        row4.addWidget(btn_out)
        l_opts.addLayout(row4)

        grp.addSettingCard(card_opts)

        self.btn_run_filter = PrimaryPushButton("Run Filtering")
        self.btn_run_filter.setIcon(FIF.PLAY)

        layout.addWidget(grp)
        layout.addWidget(self.btn_run_filter)
        layout.addStretch(1)
        return w

    def on_switch_reduce_changed(self, checked):
        self.len_thresh.setEnabled(checked)
        self.chk_consensus.setEnabled(checked)
        self.filter_tnrs_switch.setEnabled(checked)
        if not checked:
            self.filter_tnrs_switch.setChecked(False)
            self.filter_tnrs_wfo.setEnabled(False)
            self.filter_tnrs_wcvp.setEnabled(False)
            self.filter_tnrs_accuracy.setEnabled(False)

    def on_filter_tnrs_switch_changed(self, checked):
        self.filter_tnrs_wfo.setEnabled(checked)
        self.filter_tnrs_wcvp.setEnabled(checked)
        self.filter_tnrs_accuracy.setEnabled(checked)

    def browse_dir(self, line_edit):
        path = QFileDialog.getExistingDirectory(self, "Select Directory")
        if path:
            line_edit.setText(path)

    def select_wd(self):
        path = QFileDialog.getExistingDirectory(self, "Select Working Directory")
        if path:
            self.wd_edit.setText(path)

    def clear_date_from(self):
        self.date_from.reset()
        self.date_from._date = QDate()
        self.date_from_cleared = True

    def clear_date_to(self):
        self.date_to.reset()
        self.date_to._date = QDate()
        self.date_to_cleared = True

    def on_date_from_changed(self, date):
        if date.isValid():
            self.date_from_cleared = False

    def on_date_to_changed(self, date):
        if date.isValid():
            self.date_to_cleared = False


class ConstructionInterface(QWidget):
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        self.setObjectName("construction_interface")

        self.vBoxLayout = QVBoxLayout(self)
        self.pivot = SegmentedWidget(self)
        self.stackedWidget = QStackedWidget(self)

        self.page_replace = self.create_replacement_page()
        self.page_align = self.create_alignment_page()
        self.page_trim = self.create_trimming_page()
        self.page_concat = self.create_concat_page()

        self.addSubInterface(self.page_replace, "replace", "Replacement")
        self.addSubInterface(self.page_align, "align", "Alignment")
        self.addSubInterface(self.page_trim, "trim", "Trimming")
        self.addSubInterface(self.page_concat, "concat", "Concatenation")

        self.vBoxLayout.addWidget(self.pivot)
        self.vBoxLayout.addWidget(self.stackedWidget)
        self.vBoxLayout.setContentsMargins(30, 25, 30, 15)

        self.stackedWidget.setCurrentWidget(self.page_align)
        self.pivot.setCurrentItem("align")
        self.pivot.currentItemChanged.connect(
            lambda k: self.stackedWidget.setCurrentWidget(self.findChild(QWidget, k))
        )

    def addSubInterface(self, widget: QWidget, objectName, text):
        widget.setObjectName(objectName)
        self.stackedWidget.addWidget(widget)
        self.pivot.addItem(routeKey=objectName, text=text)

    def create_replacement_page(self):
        w = QWidget()
        layout = QVBoxLayout(w)
        layout.setContentsMargins(5, 20, 5, 20)

        grp = SettingCardGroup("Replacement", w)
        card = CardWidget()
        card.setFixedHeight(180)
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(15, 10, 15, 10)
        card_layout.setSpacing(10)

        label_w = 190
        lbl_cp = BodyLabel("Gene from Chloroplasts:")
        lbl_cp.setFixedWidth(label_w)
        lbl_frag = BodyLabel("Gene from DNAseqs:")
        lbl_frag.setFixedWidth(label_w)
        lbl_out = BodyLabel("Output Directory:")
        lbl_out.setFixedWidth(label_w)

        self.replace_cp_file = LineEdit()
        self.replace_cp_file.setPlaceholderText("Select a fa/fas/fasta file")
        btn_cp = PushButton("Browse")
        btn_cp.setIcon(FIF.FOLDER)
        btn_cp.clicked.connect(self.browse_replace_cp_file)

        self.replace_frag_file = LineEdit()
        self.replace_frag_file.setPlaceholderText("Select a fa/fas/fasta file")
        btn_frag = PushButton("Browse")
        btn_frag.setIcon(FIF.FOLDER)
        btn_frag.clicked.connect(self.browse_replace_frag_file)

        self.replace_out = LineEdit()
        self.replace_out.setPlaceholderText(
            "one folder to save the replacement results, create a new one if does not exists"
        )
        btn_out = PushButton("Browse")
        btn_out.setIcon(FIF.FOLDER)
        btn_out.clicked.connect(lambda: self.browse_dir(self.replace_out))

        self.replace_cp_file.textChanged.connect(self.on_replace_cp_file_changed)

        h1 = QHBoxLayout()
        h1.addWidget(lbl_cp)
        h1.addWidget(self.replace_cp_file, 1)
        h1.addWidget(btn_cp)

        h2 = QHBoxLayout()
        h2.addWidget(lbl_frag)
        h2.addWidget(self.replace_frag_file, 1)
        h2.addWidget(btn_frag)

        h3 = QHBoxLayout()
        h3.addWidget(lbl_out)
        h3.addWidget(self.replace_out, 1)
        h3.addWidget(btn_out)

        card_layout.addLayout(h1)
        card_layout.addLayout(h2)
        card_layout.addLayout(h3)
        grp.addSettingCard(card)

        self.btn_run_replace = PrimaryPushButton("Run Replacement")
        self.btn_run_replace.setIcon(FIF.PLAY)

        layout.addWidget(grp)
        layout.addWidget(self.btn_run_replace)
        layout.addStretch(1)
        return w

    def create_alignment_page(self):
        w = QWidget()
        layout = QVBoxLayout(w)
        layout.setContentsMargins(5, 20, 5, 20)

        grp = SettingCardGroup("Sequence Alignment (MAFFT)", w)

        card_opts = CardWidget()
        card_opts.setFixedHeight(220)
        l_opts = QVBoxLayout(card_opts)
        l_opts.setContentsMargins(15, 10, 15, 10)

        self.rb_align_single = RadioButton("Input one file")
        self.rb_align_multi = RadioButton("Input multiple files")
        self.rb_align_single.setChecked(True)
        self.switch_reorder = SwitchButton()
        self.switch_reorder.setChecked(True)
        row_rb = QHBoxLayout()
        row_rb.addWidget(self.rb_align_single)
        row_rb.addStretch()
        row_rb.addWidget(self.rb_align_multi)
        row_rb.addStretch()
        row_rb.addWidget(BodyLabel("Reorder:"))
        row_rb.addWidget(self.switch_reorder)
        #row_rb.addStretch()
        l_opts.addLayout(row_rb)

        self.align_in = LineEdit()
        self.align_in.setPlaceholderText("Input file or directory")
        btn_in = PushButton("Browse")
        btn_in.setIcon(FIF.FOLDER)
        btn_in.clicked.connect(
            lambda: self.browse_file_or_dir(
                self.align_in, self.rb_align_single.isChecked()
            )
        )

        self.align_out = LineEdit()
        self.align_out.setPlaceholderText(
            "one folder to save the aligned fasta files, create a new one if does not exists"
        )
        btn_out = PushButton("Browse")
        btn_out.setIcon(FIF.FOLDER)
        btn_out.clicked.connect(lambda: self.browse_dir(self.align_out))

        h1 = QHBoxLayout()
        lbl_aln_in = BodyLabel("Input:")
        lbl_aln_in.setFixedWidth(60)
        h1.addWidget(lbl_aln_in)
        h1.addWidget(self.align_in)
        h1.addWidget(btn_in)
        h2 = QHBoxLayout()
        lbl_aln_out = BodyLabel("Output:")
        lbl_aln_out.setFixedWidth(60)
        h2.addWidget(lbl_aln_out)
        h2.addWidget(self.align_out)
        h2.addWidget(btn_out)
        l_opts.addLayout(h1)
        l_opts.addLayout(h2)

        self.align_thread = LineEdit()

        self.align_thread.setText("-1")
        self.align_thread.setFixedWidth(100)
        self.align_algo = ComboBox()
        self.align_algo.addItems(
            [
                "auto (depends on datasize)",
                "add (use long sequences as backbone to align sequences)",
            ]
        )
        row_param = QHBoxLayout()
        #row_param.addWidget(BodyLabel("Threads:"))

        lbl_threads = BodyLabel("Threads:")
        lbl_threads.setFixedWidth(60)
        row_param.addWidget(lbl_threads)
        row_param.addWidget(self.align_thread)
        row_param.addSpacing(20)
        row_param.addWidget(BodyLabel("Strategy:"))
        row_param.addWidget(self.align_algo, 1)
        #row_param.addStretch()
        l_opts.addLayout(row_param)

        grp.addSettingCard(card_opts)

        self.btn_run_align = PrimaryPushButton("Run Alignment")
        self.btn_run_align.setIcon(FIF.PLAY)

        layout.addWidget(grp)
        layout.addWidget(self.btn_run_align)
        layout.addStretch(1)
        return w

    def create_trimming_page(self):
        w = QWidget()
        layout = QVBoxLayout(w)
        layout.setContentsMargins(5, 20, 5, 20)

        grp = SettingCardGroup("Alignment Trimming (trimAl)", w)

        card_opts = CardWidget()
        card_opts.setFixedHeight(340)
        l_opts = QVBoxLayout(card_opts)
        l_opts.setContentsMargins(15, 20, 15, 20)
        self.rb_trim_single = RadioButton("Input one file")
        self.rb_trim_multi = RadioButton("Input multiple files")
        self.chk_chloroplast = SwitchButton()
        self.chk_chloroplast.setChecked(False)
        self.chk_chloroplast.checkedChanged.connect(self.on_chloroplast_mode_changed)
        lbl_chloro = BodyLabel("Chloroplast Mode:")
        lbl_chloro.setToolTip(
            "For chloroplast multi-gene alignments where uneven annotation\n"
            "boundaries cause ragged gap-rich ends. When enabled, trimAl first\n"
            "strips boundary gaps at both ends of each alignment\n"
            "(gap frequency threshold = 0.025), then applies the selected\n"
            "trimAl method. When disabled, trimAl runs directly without\n"
            "boundary pre-processing."
        )
        self.rb_trim_single.setChecked(True)
        row_rb = QHBoxLayout()
        row_rb.addWidget(self.rb_trim_single)
        row_rb.addStretch(1)
        row_rb.addWidget(self.rb_trim_multi)
        row_rb.addStretch(1)
        row_rb.addWidget(lbl_chloro)
        row_rb.addWidget(self.chk_chloroplast)
        l_opts.addLayout(row_rb)
        l_opts.addSpacing(10)

        self.trim_in = LineEdit()
        self.trim_in.setPlaceholderText(
            "the path of one fasta file or the folder path that contains multiple fasta files"
        )
        btn_in = PushButton("Browse")
        btn_in.setIcon(FIF.FOLDER)
        btn_in.clicked.connect(
            lambda: self.browse_file_or_dir(
                self.trim_in, self.rb_trim_single.isChecked()
            )
        )
        self.trim_out = LineEdit()
        self.trim_out.setPlaceholderText(
            "one folder to save the trimmed fasta files, create a new one if does not exists"
        )
        btn_out = PushButton("Browse")
        btn_out.setIcon(FIF.FOLDER)
        btn_out.clicked.connect(lambda: self.browse_dir(self.trim_out))

        h1 = QHBoxLayout()
        lbl_trim_in = BodyLabel("Input:")
        lbl_trim_in.setFixedWidth(60)
        h1.addWidget(lbl_trim_in)
        h1.addWidget(self.trim_in)
        h1.addWidget(btn_in)
        h2 = QHBoxLayout()
        lbl_trim_out = BodyLabel("Output:")
        lbl_trim_out.setFixedWidth(60)
        h2.addWidget(lbl_trim_out)
        h2.addWidget(self.trim_out)
        h2.addWidget(btn_out)
        l_opts.addLayout(h1)
        l_opts.addSpacing(10)
        l_opts.addLayout(h2)
        l_opts.addSpacing(10)

        self.combo_trim_method = ComboBox()

        self.combo_trim_method.addItems(
            [
                "automated1 (heuristic selection based on similarity statistics)",
                "gappyout (uses information based on gaps' distribution)",
                'strict (automatic selection on "strict" mode)',
                'strictplus (automatic selection on "strictplus" mode)',
                "user defined method (set thresholds of non gap, similarity, consistency...)",
            ]
        )
        row_method = QHBoxLayout()
        row_method.addWidget(BodyLabel("Trimming Method:"))
        row_method.addWidget(self.combo_trim_method, 1)
        row_method.addStretch()
        l_opts.addLayout(row_method)
        l_opts.addSpacing(10)

        grid = QHBoxLayout()
        self.trim_gt = LineEdit()
        self.trim_gt.setPlaceholderText(
            "1 - (fraction of sequences with a gap allowed)"
        )
        self.trim_st = LineEdit()
        self.trim_st.setPlaceholderText("Minimum average similarity allowed")
        self.trim_ct = LineEdit()
        self.trim_ct.setPlaceholderText("Minimum consistency value allowed")
        self.trim_con = LineEdit()
        self.trim_con.setPlaceholderText(
            "Minimum percentage of the positions in the original alignment to conserve"
        )

        c1 = QVBoxLayout()
        c1.addWidget(BodyLabel("Non-gap Threshold (0-1):"))
        c1.addWidget(self.trim_gt)
        c1.addWidget(BodyLabel("Similarity Threshold (0-1):"))
        c1.addWidget(self.trim_st)

        c2 = QVBoxLayout()
        c2.addWidget(BodyLabel("Consistency Threshold (0-1):"))
        c2.addWidget(self.trim_ct)
        c2.addWidget(BodyLabel("Min % Conserve (0-100):"))
        c2.addWidget(self.trim_con)

        grid.addLayout(c1)
        grid.addLayout(c2)
        l_opts.addLayout(grid)
        grp.addSettingCard(card_opts)

        self.btn_run_trim = PrimaryPushButton("Run Trimming")
        self.btn_run_trim.setIcon(FIF.PLAY)

        layout.addWidget(grp)
        layout.addWidget(self.btn_run_trim)
        layout.addStretch(1)
        return w

    def create_concat_page(self):
        w = QWidget()
        layout = QVBoxLayout(w)
        layout.setContentsMargins(5, 20, 5, 20)

        grp = SettingCardGroup("Concatenation", w)
        card = CardWidget()
        card.setFixedHeight(150)
        concat_layout = QVBoxLayout(card)
        concat_layout.setContentsMargins(15, 10, 15, 10)

        self.concat_in = LineEdit()
        self.concat_in.setPlaceholderText(
            "the folder path that contains multiple trimmed fasta files"
        )
        btn_in = PushButton("Browse")
        btn_in.setIcon(FIF.FOLDER)
        btn_in.clicked.connect(lambda: self.browse_dir(self.concat_in))

        self.concat_out = LineEdit()
        self.concat_out.setPlaceholderText(
            "one folder to save the concatenation results, create a new one if does not exists"
        )
        btn_out = PushButton("Browse")
        btn_out.setIcon(FIF.FOLDER)
        btn_out.clicked.connect(lambda: self.browse_dir(self.concat_out))

        h1 = QHBoxLayout()
        lbl_concat_in = BodyLabel("Input Directory:")
        lbl_concat_in.setFixedWidth(120)
        h1.addWidget(lbl_concat_in)
        h1.addWidget(self.concat_in)
        h1.addWidget(btn_in)

        h2 = QHBoxLayout()
        lbl_concat_out = BodyLabel("Output Directory:")
        lbl_concat_out.setFixedWidth(120)
        h2.addWidget(lbl_concat_out)
        h2.addWidget(self.concat_out)
        h2.addWidget(btn_out)

        concat_layout.addLayout(h1)
        concat_layout.addLayout(h2)
        grp.addSettingCard(card)

        self.btn_run_concat = PrimaryPushButton("Run Concatenation")
        self.btn_run_concat.setIcon(FIF.PLAY)

        layout.addWidget(grp)
        layout.addWidget(self.btn_run_concat)
        layout.addStretch(1)
        return w

    def on_chloroplast_mode_changed(self, checked):
        self.rb_trim_single.setEnabled(not checked)
        if checked:
            self.rb_trim_multi.setChecked(True)

    def browse_dir(self, line_edit):
        path = QFileDialog.getExistingDirectory(self, "Select Directory")
        if path:
            line_edit.setText(path)

    def browse_file_or_dir(self, line_edit, is_single):
        if is_single:
            path, _ = QFileDialog.getOpenFileName(self, "Select File")
        else:
            path = QFileDialog.getExistingDirectory(self, "Select Directory")
        if path:
            line_edit.setText(path)

    def browse_fasta_file(self, line_edit):
        path, _ = QFileDialog.getOpenFileName(
            self,
            "Select FASTA File",
            "",
            "FASTA Files (*.fa *.fas *.fasta);;All Files (*)",
        )
        if path:
            line_edit.setText(path)

    def browse_replace_cp_file(self):
        self.browse_fasta_file(self.replace_cp_file)

    def browse_replace_frag_file(self):
        self.browse_fasta_file(self.replace_frag_file)

    def on_replace_cp_file_changed(self, text):
        path = Path(text.strip())
        if text.strip() and path.suffix.lower() in {".fa", ".fas", ".fasta"}:
            self.replace_out.setText(str(path.parent))


class ChloroplastMinerInterface(QWidget):
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        self.setObjectName("chloroplast_miner_interface")

        self.vBoxLayout = QVBoxLayout(self)
        self.pivot = SegmentedWidget(self)
        self.stackedWidget = QStackedWidget(self)

        self.page_search = self.create_search_page()
        self.page_extract = self.create_extract_page()
        self.page_cds = self.create_cds_page()

        self.addSubInterface(self.page_search, "search", "Search && Download")
        self.addSubInterface(
            self.page_extract, "extract", "Extract Info && Quality Control"
        )
        self.addSubInterface(self.page_cds, "cds", "Get && Process CDS")

        self.vBoxLayout.addWidget(self.pivot)
        self.vBoxLayout.addWidget(self.stackedWidget)
        self.vBoxLayout.setContentsMargins(30, 25, 30, 15)

        self.stackedWidget.setCurrentWidget(self.page_search)
        self.pivot.setCurrentItem("search")
        self.pivot.currentItemChanged.connect(self.on_chloroplast_page_changed)

    def on_chloroplast_page_changed(self, key):
        self.stackedWidget.setCurrentWidget(self.findChild(QWidget, key))
        if key == "extract":
            self.update_qc_input_default()

    def update_qc_input_default(self):
        if hasattr(self, "chloro_qc_in") and hasattr(self, "prefilter_out_edit"):
            prefilter_out = self.prefilter_out_edit.text().strip()
            if prefilter_out and not self.chloro_qc_in.text().strip():
                self.chloro_qc_in.setText(prefilter_out)

    def addSubInterface(self, widget: QWidget, objectName, text):
        widget.setObjectName(objectName)
        self.stackedWidget.addWidget(widget)
        self.pivot.addItem(routeKey=objectName, text=text)

    def create_search_page(self):
        w = SingleDirectionScrollArea()
        w.setWidgetResizable(True)
        view = QWidget()
        layout = QVBoxLayout(view)
        layout.setContentsMargins(5, 20, 5, 20)
        layout.setSpacing(6)

        grp_search_dl = SettingCardGroup("Search & Download", view)
        grp_search_dl.titleLabel.setToolTip(
            "Search NCBI for plastid genomes by taxon names and batch download GenBank files.\n"
            "Query: taxon[Organism] AND (plastid OR chloroplast) AND SLEN range,\n"
            "excluding mitochondrion/chromosome titles. Optionally filter by date range."
        )
        grp_search_dl.titleLabel.installEventFilter(
            ToolTipFilter(grp_search_dl.titleLabel, showDelay=300, position=ToolTipPosition.BOTTOM_LEFT)
        )

        card = CardWidget()
        card.setFixedHeight(200)
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(15, 10, 15, 10)

        content_row = QHBoxLayout()
        content_row.setContentsMargins(0, 0, 0, 0)
        content_row.setSpacing(20)

        # --- Left: Target Taxa ---
        left_col = QVBoxLayout()
        left_col.setContentsMargins(0, 0, 0, 0)
        left_col.setSpacing(6)
        left_col.addWidget(BodyLabel("Target Taxa:"))
        self.chloro_tax_edit = PlainTextEdit(card)
        self.chloro_tax_edit.setPlaceholderText("Enter taxon names (one per line)")
        left_col.addWidget(self.chloro_tax_edit, 1)
        content_row.addLayout(left_col, 1)

        # --- Right: Dates + Email + Download Dir ---
        right_col = QVBoxLayout()
        right_col.setContentsMargins(0, 0, 0, 0)
        right_col.setSpacing(8)

        label_w = 100

        lbl_from = BodyLabel("Date From:")
        lbl_from.setFixedWidth(label_w)
        row_from = QHBoxLayout()
        self.chloro_date_from = DatePicker(card)
        self.chloro_date_from.setDate(QDate())
        self.chloro_date_from_cleared = True
        self.chloro_date_from.dateChanged.connect(self.on_chloro_date_from_changed)
        self.chloro_btn_clear_from = PushButton("Reset", card)
        self.chloro_btn_clear_from.clicked.connect(self.clear_chloro_date_from)
        row_from.addWidget(lbl_from)
        row_from.addWidget(self.chloro_date_from, 1)
        row_from.addWidget(self.chloro_btn_clear_from)
        right_col.addLayout(row_from)

        lbl_to = BodyLabel("Date To:")
        lbl_to.setFixedWidth(label_w)
        row_to = QHBoxLayout()
        self.chloro_date_to = DatePicker(card)
        self.chloro_date_to.setDate(QDate())
        self.chloro_date_to_cleared = True
        self.chloro_date_to.dateChanged.connect(self.on_chloro_date_to_changed)
        self.chloro_btn_clear_to = PushButton("Reset", card)
        self.chloro_btn_clear_to.clicked.connect(self.clear_chloro_date_to)
        row_to.addWidget(lbl_to)
        row_to.addWidget(self.chloro_date_to, 1)
        row_to.addWidget(self.chloro_btn_clear_to)
        right_col.addLayout(row_to)

        lbl_email = BodyLabel("Email:")
        lbl_email.setFixedWidth(label_w)
        row_email = QHBoxLayout()
        self.chloro_email_edit = LineEdit(card)
        self.chloro_email_edit.setPlaceholderText("Your Email")
        row_email.addWidget(lbl_email)
        row_email.addWidget(self.chloro_email_edit, 1)
        right_col.addLayout(row_email)

        lbl_dl = BodyLabel("Download Dir:")
        lbl_dl.setFixedWidth(label_w)
        row_dl = QHBoxLayout()
        self.chloro_download_dir_edit = LineEdit(card)
        self.chloro_download_dir_edit.setPlaceholderText("Download Directory Path")
        btn_chloro_download_dir = PushButton("Browse")
        btn_chloro_download_dir.setIcon(FIF.FOLDER)
        btn_chloro_download_dir.clicked.connect(
            lambda: self.browse_folder(self.chloro_download_dir_edit)
        )
        row_dl.addWidget(lbl_dl)
        row_dl.addWidget(self.chloro_download_dir_edit, 1)
        row_dl.addWidget(btn_chloro_download_dir)
        right_col.addLayout(row_dl)

        content_row.addLayout(right_col, 1)
        card_layout.addLayout(content_row, 1)

        grp_search_dl.addSettingCard(card)
        layout.addWidget(grp_search_dl)

        btn_row = QHBoxLayout()
        self.btn_chloro_search = PrimaryPushButton("Search", view)
        self.btn_chloro_search.setIcon(FIF.SEARCH)
        self.btn_chloro_search.clicked.connect(self.on_chloro_search)
        self.btn_chloro_download = PrimaryPushButton("Download", view)
        self.btn_chloro_download.setIcon(FIF.DOWNLOAD)
        self.btn_chloro_download.clicked.connect(self.on_chloro_download)
        btn_row.addWidget(self.btn_chloro_search)
        btn_row.addSpacing(10)
        btn_row.addWidget(self.btn_chloro_download)
        layout.addLayout(btn_row)
        layout.addSpacing(14)

        grp_prefilter = SettingCardGroup("Pre-filter", view)
        grp_prefilter.titleLabel.setToolTip(
            "Remove redundant genomes before downstream analysis.\n"
            "Optionally merge at species level and retain only the top N\n"
            "longest genomes per taxon to reduce redundancy."
        )
        grp_prefilter.titleLabel.installEventFilter(
            ToolTipFilter(grp_prefilter.titleLabel, showDelay=300, position=ToolTipPosition.BOTTOM_LEFT)
        )

        card_prefilter = CardWidget()
        card_prefilter.setFixedHeight(100)
        main_row = QHBoxLayout(card_prefilter)
        main_row.setContentsMargins(15, 10, 15, 10)
        main_row.setSpacing(20)

        # --- Left column: input / output directories ---
        left_col = QVBoxLayout()
        left_col.setContentsMargins(0, 0, 0, 0)
        left_col.setSpacing(8)

        self.prefilter_in_edit = LineEdit()
        self.prefilter_in_edit.setPlaceholderText("Input directory with downloaded GeneBank files")
        btn_prefilter_in = PushButton("Browse")
        btn_prefilter_in.setIcon(FIF.FOLDER)
        btn_prefilter_in.clicked.connect(lambda: self.browse_folder(self.prefilter_in_edit))

        h_pf_in = QHBoxLayout()
        lbl_pf_in = BodyLabel("Input Directory:")
        lbl_pf_in.setFixedWidth(130)
        h_pf_in.addWidget(lbl_pf_in)
        h_pf_in.addWidget(self.prefilter_in_edit)
        h_pf_in.addWidget(btn_prefilter_in)
        left_col.addLayout(h_pf_in)

        self.chloro_download_dir_edit.textChanged.connect(
            lambda text: self.prefilter_in_edit.setText(text)
        )

        self.prefilter_out_edit = LineEdit()
        self.prefilter_out_edit.setPlaceholderText("Output directory for filtered GeneBank files")
        btn_prefilter_out = PushButton("Browse")
        btn_prefilter_out.setIcon(FIF.FOLDER)
        btn_prefilter_out.clicked.connect(lambda: self.browse_folder(self.prefilter_out_edit))

        h_pf_out = QHBoxLayout()
        lbl_pf_out = BodyLabel("Output Directory:")
        lbl_pf_out.setFixedWidth(130)
        h_pf_out.addWidget(lbl_pf_out)
        h_pf_out.addWidget(self.prefilter_out_edit)
        h_pf_out.addWidget(btn_prefilter_out)
        left_col.addLayout(h_pf_out)

        main_row.addLayout(left_col, 2)

        # --- Right column: options ---
        right_col = QVBoxLayout()
        right_col.setContentsMargins(0, 0, 0, 0)
        right_col.setSpacing(16)

        right_col.addStretch()

        row_species = QHBoxLayout()
        lbl_species_merge = BodyLabel("Species Level Merge:")
        lbl_species_merge.setToolTip(
            "When enabled, group records by species (not just genus)\n"
            "before selecting representative genomes."
        )
        row_species.addWidget(lbl_species_merge)
        row_species.addStretch()
        self.prefilter_species_switch = SwitchButton()
        self.prefilter_species_switch.setChecked(True)
        row_species.addWidget(self.prefilter_species_switch)
        right_col.addLayout(row_species)

        row_keep = QHBoxLayout()
        self.prefilter_keep_label = BodyLabel("Records Per Taxon:")
        self.prefilter_keep_label.setToolTip(
            "Maximum number of genomes to retain per taxon.\n"
            "Longest sequences are kept; the rest are discarded. Default 3."
        )
        row_keep.addWidget(self.prefilter_keep_label)
        row_keep.addStretch()
        self.prefilter_keep_edit = LineEdit()
        self.prefilter_keep_edit.setText("3")
        row_keep.addWidget(self.prefilter_keep_edit)
        right_col.addLayout(row_keep)

        self.prefilter_species_switch.checkedChanged.connect(
            lambda checked: (
                self.prefilter_keep_label.setEnabled(checked),
                self.prefilter_keep_edit.setEnabled(checked),
            )
        )

        right_col.addStretch()
        main_row.addLayout(right_col, 1)

        grp_prefilter.addSettingCard(card_prefilter)
        layout.addWidget(grp_prefilter)

        self.btn_chloro_prefilter = PrimaryPushButton("Run Pre-filter", view)
        self.btn_chloro_prefilter.setIcon(FIF.FILTER)
        self.btn_chloro_prefilter.clicked.connect(self.on_chloro_prefilter)
        layout.addWidget(self.btn_chloro_prefilter)
        layout.addStretch(1)

        w.setWidget(view)
        w.setObjectName("search_page")
        w.setStyleSheet("QScrollArea {border: none; background:transparent}")
        view.setStyleSheet("QWidget {background:transparent}")
        return w

    def create_extract_page(self):
        w = QWidget()
        layout = QVBoxLayout(w)
        layout.setContentsMargins(5, 20, 5, 20)

        grp = SettingCardGroup("Extract Info & Quality Control", w)
        grp.titleLabel.setToolTip(
            "Extract genome metadata and flag problematic genomes.\n"
            "Genomes with too few CDS features or excessive ambiguous bases (N)\n"
            "are exported as FASTA for reannotation via PGA."
        )
        grp.titleLabel.installEventFilter(
            ToolTipFilter(grp.titleLabel, showDelay=300, position=ToolTipPosition.BOTTOM_LEFT)
        )

        card = CardWidget()
        card.setFixedHeight(160)
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(15, 10, 15, 10)

        h_input = QHBoxLayout()
        self.chloro_qc_in = LineEdit()
        self.chloro_qc_in.setPlaceholderText("Input directory containing pre-filtered GenBank files")
        btn_chloro_qc_in = PushButton("Browse")
        btn_chloro_qc_in.setIcon(FIF.FOLDER)
        btn_chloro_qc_in.clicked.connect(lambda: self.browse_folder(self.chloro_qc_in))
        lbl_qc_in = BodyLabel("Input Directory:")
        lbl_qc_in.setFixedWidth(130)
        h_input.addWidget(lbl_qc_in)
        h_input.addWidget(self.chloro_qc_in)
        h_input.addWidget(btn_chloro_qc_in)
        card_layout.addLayout(h_input)

        h_output = QHBoxLayout()
        self.chloro_qc_out = LineEdit()
        self.chloro_qc_out.setPlaceholderText(
            "Output directory for problematic genome FASTA files"
        )
        self.chloro_qc_out.textChanged.connect(self.on_chloro_qc_out_changed)
        btn_chloro_qc_out = PushButton("Browse")
        btn_chloro_qc_out.setIcon(FIF.FOLDER)
        btn_chloro_qc_out.clicked.connect(
            lambda: self.browse_folder(self.chloro_qc_out)
        )
        lbl_qc_out = BodyLabel("Output Directory:")
        lbl_qc_out.setFixedWidth(130)
        h_output.addWidget(lbl_qc_out)
        h_output.addWidget(self.chloro_qc_out)
        h_output.addWidget(btn_chloro_qc_out)
        card_layout.addLayout(h_output)

        self.chloro_cds_thresh = LineEdit()
        self.chloro_cds_thresh.setText("75")
        self.chloro_ambig_thresh = LineEdit()
        self.chloro_ambig_thresh.setText("0.1")

        h_threshold = QHBoxLayout()
        lbl_cds_thresh = BodyLabel("CDS Threshold:")
        lbl_cds_thresh.setFixedWidth(130)
        lbl_cds_thresh.setToolTip(
            "Minimum number of CDS features required.\n"
            "Genomes with fewer CDS are flagged as problematic. Default 75."
        )
        h_threshold.addWidget(lbl_cds_thresh)
        h_threshold.addWidget(self.chloro_cds_thresh)
        h_threshold.addStretch()
        lbl_ambig_thresh = BodyLabel("Ambiguity Threshold:")
        lbl_ambig_thresh.setToolTip(
            "Maximum allowed fraction of ambiguous bases (N).\n"
            "Genomes exceeding this ratio are flagged. Default 0.1 (10%)."
        )
        h_threshold.addWidget(lbl_ambig_thresh)
        h_threshold.addWidget(self.chloro_ambig_thresh)
        card_layout.addLayout(h_threshold)

        grp.addSettingCard(card)

        layout.addWidget(grp)

        self.btn_chloro_qc_extract = PrimaryPushButton("Extract and QC", w)
        self.btn_chloro_qc_extract.setIcon(FIF.PLAY)
        self.btn_chloro_qc_extract.clicked.connect(self.on_chloro_qc_extract)
        layout.addWidget(self.btn_chloro_qc_extract)

        grp_pga = SettingCardGroup("Plastid Genome Annotator", w)
        grp_pga.titleLabel.setToolTip(
            "Reannotate problematic genomes using PGA (Plastid Genome Annotator).\n"
            "Select a clade-specific reference set or provide a custom directory\n"
            "of reference GenBank files for homology-based annotation."
        )
        grp_pga.titleLabel.installEventFilter(
            ToolTipFilter(grp_pga.titleLabel, showDelay=300, position=ToolTipPosition.BOTTOM_LEFT)
        )

        card_pga = CardWidget()
        card_pga.setFixedHeight(130)
        card_pga_layout = QVBoxLayout(card_pga)
        card_pga_layout.setContentsMargins(15, 10, 15, 10)

        h_pga_input = QHBoxLayout()
        self.chloro_pga_in = LineEdit()
        self.chloro_pga_in.setPlaceholderText(
            "Input directory containing problematic genome FASTA files"
        )
        btn_chloro_pga_in = PushButton("Browse")
        btn_chloro_pga_in.setIcon(FIF.FOLDER)
        btn_chloro_pga_in.clicked.connect(
            lambda: self.browse_folder(self.chloro_pga_in)
        )
        lbl_pga_in = BodyLabel("Input Directory:")
        lbl_pga_in.setFixedWidth(130)
        h_pga_input.addWidget(lbl_pga_in)
        h_pga_input.addWidget(self.chloro_pga_in)
        h_pga_input.addWidget(btn_chloro_pga_in)
        card_pga_layout.addLayout(h_pga_input)

        h_pga_ref = QHBoxLayout()
        self.chloro_pga_clade = ComboBox()
        self.chloro_pga_clade.addItems(["Angiosperms", "Gymnosperms", "User defined"])
        self.chloro_pga_clade.currentTextChanged.connect(
            self.on_chloro_pga_clade_changed
        )

        self.chloro_pga_ref = LineEdit()
        self.chloro_pga_ref.setPlaceholderText("Reference genome directory")
        self.chloro_pga_ref.setEnabled(False)
        self.btn_chloro_pga_ref = PushButton("Browse")
        self.btn_chloro_pga_ref.setIcon(FIF.FOLDER)
        self.btn_chloro_pga_ref.setEnabled(False)
        self.btn_chloro_pga_ref.clicked.connect(
            lambda: self.browse_folder(self.chloro_pga_ref)
        )
        lbl_pga_clade = BodyLabel("Clades:")
        lbl_pga_clade.setToolTip(
            "Reference annotation set for PGA.\n"
            "Angiosperms / Gymnosperms use built-in references;\n"
            "User defined requires a custom reference genome directory."
        )

        lbl_pga_ref = BodyLabel("Reference Genome:")
        lbl_pga_ref.setToolTip(
            "Directory of reference GenBank files for PGA.\n"
            "Only enabled when Clades is set to User defined."
        )
        h_pga_ref.addWidget(lbl_pga_clade)
        h_pga_ref.addWidget(self.chloro_pga_clade)
        #h_pga_ref.addStretch()
        h_pga_ref.addWidget(lbl_pga_ref)
        h_pga_ref.addWidget(self.chloro_pga_ref)
        h_pga_ref.addWidget(self.btn_chloro_pga_ref)
        card_pga_layout.addLayout(h_pga_ref)

        grp_pga.addSettingCard(card_pga)

        layout.addWidget(grp_pga)

        self.btn_chloro_pga = PrimaryPushButton("Reannotate", w)
        self.btn_chloro_pga.setIcon(FIF.PLAY)
        self.btn_chloro_pga.clicked.connect(self.on_chloro_pga)
        layout.addWidget(self.btn_chloro_pga)
        layout.addStretch(1)
        return w

    def create_cds_page(self):
        w = SingleDirectionScrollArea()
        w.setWidgetResizable(True)
        self.cds_view = QWidget()
        self.cds_view.setObjectName("cds_view")
        layout = QVBoxLayout(self.cds_view)
        layout.setContentsMargins(5, 20, 5, 20)
        layout.setSpacing(6)

        grp_gf = SettingCardGroup("Get & Filter CDS", self.cds_view)
        grp_gf.titleLabel.setToolTip(
            "Extract plastid CDS/rRNA from GenBank files and filter by reference length.\n"
            "1) Map features to the standard ~80-gene plastid set;\n"
            "2) Discard sequences outside [Lower Bound, Upper Bound] x reference length;\n"
            "3) Write filtered FASTA files and length.csv for downstream selection."
        )
        grp_gf.titleLabel.installEventFilter(
            ToolTipFilter(grp_gf.titleLabel, showDelay=300, position=ToolTipPosition.BOTTOM_LEFT)
        )

        card_gf = CardWidget()
        card_gf.setFixedHeight(165)
        card_gf_layout = QVBoxLayout(card_gf)
        card_gf_layout.setContentsMargins(15, 10, 15, 10)

        h_gf_input = QHBoxLayout()
        self.cds_gf_in = LineEdit()
        self.cds_gf_in.setPlaceholderText(
            "Input directory containing filtered GenBank files"
        )
        self.chloro_qc_in.textChanged.connect(
            lambda text: self.cds_gf_in.setText(text) if text else None
        )
        btn_cds_gf_in = PushButton("Browse")
        btn_cds_gf_in.setIcon(FIF.FOLDER)
        btn_cds_gf_in.clicked.connect(lambda: self.browse_folder(self.cds_gf_in))
        lbl_gf_in = BodyLabel("Input Directory:")
        lbl_gf_in.setFixedWidth(130)
        h_gf_input.addWidget(lbl_gf_in)
        h_gf_input.addWidget(self.cds_gf_in)
        h_gf_input.addWidget(btn_cds_gf_in)
        card_gf_layout.addLayout(h_gf_input)

        h_gf_output = QHBoxLayout()
        self.cds_gf_out = LineEdit()
        self.cds_gf_out.setPlaceholderText(
            "Output directory for filtered CDS files"
        )
        self.cds_gf_out.textChanged.connect(self.on_cds_gf_out_changed)
        btn_cds_gf_out = PushButton("Browse")
        btn_cds_gf_out.setIcon(FIF.FOLDER)
        btn_cds_gf_out.clicked.connect(
            lambda: self.browse_folder(self.cds_gf_out, self.cds_select_in)
        )
        lbl_gf_out = BodyLabel("Output Directory:")
        lbl_gf_out.setFixedWidth(130)
        h_gf_output.addWidget(lbl_gf_out)
        h_gf_output.addWidget(self.cds_gf_out)
        h_gf_output.addWidget(btn_cds_gf_out)
        card_gf_layout.addLayout(h_gf_output)

        h_gf_params = QHBoxLayout()
        self.cds_gf_ref = ComboBox()
        self.cds_gf_ref.addItems(["Angiosperms", "Gymnosperms"])
        self.cds_gf_ref.setCurrentIndex(0)
        self.cds_gf_lb = LineEdit()
        self.cds_gf_lb.setText("0.5")
        self.cds_gf_ub = LineEdit()
        self.cds_gf_ub.setText("2.0")

        lbl_gf_ref = BodyLabel("Reference:")
        lbl_gf_ref.setToolTip(
            "Reference plastid gene length table used for filtering.\n"
            "Angiosperms: typical flowering-plant CDS lengths;\n"
            "Gymnosperms: typical gymnosperm CDS lengths.\n"
            "Genes absent from the reference table are not length-filtered."
        )
        lbl_gf_lb = BodyLabel("Lower Bound:")
        lbl_gf_lb.setToolTip(
            "Minimum length as a fraction of the reference gene length.\n"
            "Default 0.5 retains sequences >= 50% of the reference length.\n"
            "Sequences shorter than this threshold are discarded."
        )
        lbl_gf_ub = BodyLabel("Upper Bound:")
        lbl_gf_ub.setToolTip(
            "Maximum length as a fraction of the reference gene length.\n"
            "Default 2.0 retains sequences <= 200% of the reference length.\n"
            "Sequences longer than this threshold are discarded."
        )
        h_gf_params.addWidget(lbl_gf_ref)
        h_gf_params.addWidget(self.cds_gf_ref)
        h_gf_params.addStretch(1)
        h_gf_params.addWidget(lbl_gf_lb)
        h_gf_params.addWidget(self.cds_gf_lb)
        h_gf_params.addStretch(1)
        h_gf_params.addWidget(lbl_gf_ub)
        h_gf_params.addWidget(self.cds_gf_ub)
        card_gf_layout.addLayout(h_gf_params)

        grp_gf.addSettingCard(card_gf)
        layout.addWidget(grp_gf)

        self.btn_cds_gf = PrimaryPushButton("Get & Filter CDS", self.cds_view)
        self.btn_cds_gf.setIcon(FIF.FILTER)
        self.btn_cds_gf.clicked.connect(self.on_cds_get_filter)
        layout.addWidget(self.btn_cds_gf)
        layout.addSpacing(14)

        grp_select = SettingCardGroup("Species-level CDS Selection", self.cds_view)
        grp_select.titleLabel.setToolTip(
            "Select one representative plastid genome per species.\n"
            "For each species, keep the accession with the longest total CDS length;\n"
            "optionally standardize organism names via CSV (inner join; unmatched excluded).\n"
            "Output headers are rewritten as accession|species_name."
        )
        grp_select.titleLabel.installEventFilter(
            ToolTipFilter(grp_select.titleLabel, showDelay=300, position=ToolTipPosition.BOTTOM_LEFT)
        )

        card_select = CardWidget()
        card_select.setFixedHeight(160)
        card_select_layout = QVBoxLayout(card_select)
        card_select_layout.setContentsMargins(15, 10, 15, 10)

        h_select_input = QHBoxLayout()
        self.cds_select_in = LineEdit()
        self.cds_select_in.setPlaceholderText(
            "Input directory containing filtered CDS files"
        )
        btn_cds_select_in = PushButton("Browse")
        btn_cds_select_in.setIcon(FIF.FOLDER)
        btn_cds_select_in.clicked.connect(
            lambda: self.browse_folder(self.cds_select_in)
        )
        lbl_select_in = BodyLabel("Input Directory:")
        lbl_select_in.setFixedWidth(130)
        h_select_input.addWidget(lbl_select_in)
        h_select_input.addWidget(self.cds_select_in)
        h_select_input.addWidget(btn_cds_select_in)
        card_select_layout.addLayout(h_select_input)

        h_select_output = QHBoxLayout()
        self.cds_select_out = LineEdit()
        self.cds_select_out.setPlaceholderText(
            "Output directory for selected CDS files"
        )
        self.cds_select_out.textChanged.connect(self.on_cds_select_out_changed)
        btn_cds_select_out = PushButton("Browse")
        btn_cds_select_out.setIcon(FIF.FOLDER)
        btn_cds_select_out.clicked.connect(
            lambda: self.browse_folder(self.cds_select_out)
        )
        lbl_select_out = BodyLabel("Output Directory:")
        lbl_select_out.setFixedWidth(130)
        h_select_output.addWidget(lbl_select_out)
        h_select_output.addWidget(self.cds_select_out)
        h_select_output.addWidget(btn_cds_select_out)
        card_select_layout.addLayout(h_select_output)

        h_select_tax = QHBoxLayout()
        lbl_select_tax = BodyLabel("Taxonomic Name Resolution:")
        lbl_select_tax.setToolTip(
            "Enable online scientific-name standardization via TNRS API\n"
            "before species-level selection. Unmatched species are excluded."
        )
        h_select_tax.addWidget(lbl_select_tax)
        self.cds_select_tax_switch = SwitchButton()
        self.cds_select_tax_switch.setChecked(False)
        h_select_tax.addWidget(self.cds_select_tax_switch)
        h_select_tax.addStretch(1)

        lbl_tnrs_src = BodyLabel("Source:")
        lbl_tnrs_src.setToolTip(
            "TNRS data sources for name resolution.\n"
            "wcvp: World Checklist of Vascular Plants (Kew);\n"
            "wfo: World Flora Online. At least one required."
        )
        h_select_tax.addWidget(lbl_tnrs_src)
        self.cds_tnrs_wfo = CheckBox("wfo")
        self.cds_tnrs_wfo.setChecked(False)
        self.cds_tnrs_wfo.setEnabled(False)
        self.cds_tnrs_wcvp = CheckBox("wcvp")
        self.cds_tnrs_wcvp.setChecked(True)
        self.cds_tnrs_wcvp.setEnabled(False)
        h_select_tax.addWidget(self.cds_tnrs_wfo)
        h_select_tax.addWidget(self.cds_tnrs_wcvp)
        h_select_tax.addStretch(1)

        lbl_tnrs_acc = BodyLabel("Accuracy:")
        lbl_tnrs_acc.setToolTip(
            "Minimum matching accuracy (0 < value <= 1).\n"
            "Higher values require stricter name matches. Default 0.9."
        )
        h_select_tax.addWidget(lbl_tnrs_acc)
        self.cds_tnrs_accuracy = LineEdit()
        self.cds_tnrs_accuracy.setText("0.9")
        self.cds_tnrs_accuracy.setMinimumWidth(120)
        self.cds_tnrs_accuracy.setEnabled(False)
        h_select_tax.addWidget(self.cds_tnrs_accuracy)
        #h_select_tax.addStretch(1)
        card_select_layout.addLayout(h_select_tax)

        def _on_tax_switch(checked):
            self.cds_tnrs_wfo.setEnabled(checked)
            self.cds_tnrs_wcvp.setEnabled(checked)
            self.cds_tnrs_accuracy.setEnabled(checked)

        self.cds_select_tax_switch.checkedChanged.connect(_on_tax_switch)

        grp_select.addSettingCard(card_select)
        layout.addWidget(grp_select)

        self.btn_cds_select = PrimaryPushButton("Species-level CDS Selection", self.cds_view)
        self.btn_cds_select.setIcon(FIF.TAG)
        self.btn_cds_select.clicked.connect(self.on_cds_select_extract)
        layout.addWidget(self.btn_cds_select)

        layout.addStretch(1)

        w.setWidget(self.cds_view)
        w.setObjectName("cds_page")
        w.setStyleSheet("QScrollArea {border: none; background:transparent}")
        self.cds_view.setStyleSheet("QWidget {background:transparent}")

        return w

    def browse_file(self, line_edit):
        path, _ = QFileDialog.getOpenFileName(self, "Select File")
        if path:
            line_edit.setText(path)

    def browse_csv_file(self, line_edit):
        path, _ = QFileDialog.getOpenFileName(self, "Select CSV File", "", "CSV Files (*.csv)")
        if path:
            line_edit.setText(path)

    def browse_folder(self, line_edit, follow_target=None):
        path = QFileDialog.getExistingDirectory(self, "Select Directory")
        if path:
            line_edit.setText(path)
            if follow_target:
                follow_target.setText(path)

    def on_chloro_search(self):
        text = self.chloro_tax_edit.toPlainText().strip()
        email = self.chloro_email_edit.text().strip()
        out_path = self.chloro_download_dir_edit.text().strip()

        if not text:
            self.main_window.backend.emit_log(
                "Please input at least one taxon", "WARNING"
            )
            return
        if not email:
            self.main_window.backend.emit_log(
                "Please enter your email", "WARNING"
            )
            return
        if not out_path:
            self.main_window.backend.emit_log(
                "Please select a download directory", "WARNING"
            )
            return

        date_from_obj = self.chloro_date_from.date
        date_to_obj = self.chloro_date_to.date

        has_from = not self.chloro_date_from_cleared and date_from_obj.isValid()
        has_to = not self.chloro_date_to_cleared and date_to_obj.isValid()

        if has_from and not has_to:
            self.chloro_date_to.setDate(QDate.currentDate())
            date_to_obj = self.chloro_date_to.date
            has_to = date_to_obj.isValid()
            self.main_window.backend.emit_log(
                "Date To not set, automatically set to today", "INFO"
            )
        elif not has_from and has_to:
            self.main_window.backend.emit_log(
                "Please select both Date From and Date To, or leave both empty",
                "WARNING",
            )
            return

        taxa = [line.strip() for line in text.split("\n") if line.strip()]
        d_from = date_from_obj.toString("yyyy/MM/dd") if has_from else ""
        d_to = date_to_obj.toString("yyyy/MM/dd") if has_to else ""

        self.main_window.backend.emit_log("Search started...", "INFO")
        self.main_window.backend.search_chloroplast(email, taxa, d_from, d_to, out_path)

    def on_chloro_download(self):
        email = self.chloro_email_edit.text().strip()
        out_path = self.chloro_download_dir_edit.text().strip()

        if not email:
            self.main_window.backend.emit_log(
                "Please enter your email", "WARNING"
            )
            return
        if not out_path:
            self.main_window.backend.emit_log(
                "Please select a download directory", "WARNING"
            )
            return

        index_file = Path(out_path) / "accession_index.txt"
        if not index_file.exists():
            self.main_window.backend.emit_log(
                "No accession index found. Please run Search first.", "WARNING"
            )
            return

        self.main_window.backend.emit_log("Download started...", "INFO")
        self.main_window.backend.download_chloroplast_genomes(
            email, str(index_file), out_path
        )

    def on_chloro_prefilter(self):
        in_folder = self.prefilter_in_edit.text().strip()
        out_folder = self.prefilter_out_edit.text().strip()

        if not in_folder or not out_folder:
            self.main_window.backend.emit_log(
                "Please select both input and output directories for pre-filter",
                "WARNING",
            )
            return

        species_level = self.prefilter_species_switch.isChecked()

        try:
            keep_latest = int(self.prefilter_keep_edit.text().strip())
            if keep_latest < 1:
                raise ValueError
        except ValueError:
            self.main_window.backend.emit_log(
                "Keep per taxon must be a positive integer", "WARNING"
            )
            return

        self.main_window.backend.emit_log("Pre-filter started...", "INFO")
        self.main_window.backend.run_prefilter(
            in_folder, out_folder, keep_latest=keep_latest, species_level=species_level
        )

    def on_chloro_date_from_changed(self, date):
        if date.isValid():
            self.chloro_date_from_cleared = False

    def on_chloro_date_to_changed(self, date):
        if date.isValid():
            self.chloro_date_to_cleared = False

    def clear_chloro_date_from(self):
        self.chloro_date_from.reset()
        self.chloro_date_from._date = QDate()
        self.chloro_date_from_cleared = True

    def clear_chloro_date_to(self):
        self.chloro_date_to.reset()
        self.chloro_date_to._date = QDate()
        self.chloro_date_to_cleared = True

    def on_chloro_qc_extract(self):
        in_folder = self.chloro_qc_in.text().strip()
        out_folder = self.chloro_qc_out.text().strip()

        if not in_folder :
            self.main_window.backend.emit_log(
                "Please select an input directory", "WARNING"
            )
            return
        
        if not out_folder:
            self.main_window.backend.emit_log(
                "Please select an output directory", "WARNING"
            )
            return

        cds_threshold = 75
        try:
            cds_threshold = int(self.chloro_cds_thresh.text().strip())
            if cds_threshold < 0:
                self.main_window.backend.emit_log(
                    "CDS threshold must be a positive integer", "WARNING"
                )
                return
        except ValueError:
            self.main_window.backend.emit_log("Invalid CDS threshold value", "WARNING")
            return

        ambig_threshold = 0.1
        try:
            ambig_threshold = float(self.chloro_ambig_thresh.text().strip())
            if ambig_threshold < 0 or ambig_threshold > 1:
                self.main_window.backend.emit_log(
                    "Ambiguity threshold must be between 0 and 1", "WARNING"
                )
                return
        except ValueError:
            self.main_window.backend.emit_log(
                "Invalid ambiguity threshold value", "WARNING"
            )
            return

        self.main_window.backend.emit_log("Quality control started...", "INFO")
        self.main_window.backend.quality_control(
            in_folder, out_folder, cds_threshold, ambig_threshold
        )

    def on_cds_get_filter(self):
        in_folder = self.cds_gf_in.text().strip()
        out_folder = self.cds_gf_out.text().strip()

        if not in_folder or not out_folder:
            self.main_window.backend.emit_log(
                "Please select both input and output directories", "WARNING"
            )
            return

        ref_text = self.cds_gf_ref.currentText()
        ref_type = "Ang" if ref_text == "Angiosperms" else "Gym"

        try:
            lower_bound = float(self.cds_gf_lb.text().strip())
            if lower_bound <= 0:
                self.main_window.backend.emit_log(
                    "Lower bound must be a positive number", "WARNING"
                )
                return
        except ValueError:
            self.main_window.backend.emit_log("Invalid lower bound value", "WARNING")
            return

        try:
            upper_bound = float(self.cds_gf_ub.text().strip())
            if upper_bound <= 0:
                self.main_window.backend.emit_log(
                    "Upper bound must be a positive number", "WARNING"
                )
                return
        except ValueError:
            self.main_window.backend.emit_log("Invalid upper bound value", "WARNING")
            return

        if lower_bound >= upper_bound:
            self.main_window.backend.emit_log(
                "Lower bound must be less than upper bound", "WARNING"
            )
            return

        self.main_window.backend.emit_log("CDS extraction & filtering started...", "INFO")
        self.main_window.backend.run_get_and_filter_cds(
            in_folder, out_folder, ref_type, lower_bound, upper_bound
        )

    def on_cds_select_extract(self):
        in_folder = self.cds_select_in.text().strip()
        out_folder = self.cds_select_out.text().strip()

        if not in_folder or not out_folder:
            self.main_window.backend.emit_log(
                "Please select both input and output directories", "WARNING"
            )
            return

        enable_tax_res = self.cds_select_tax_switch.isChecked()
        tnrs_sources = None
        tnrs_accuracy = None

        if enable_tax_res:
            sources = []
            if self.cds_tnrs_wfo.isChecked():
                sources.append("wfo")
            if self.cds_tnrs_wcvp.isChecked():
                sources.append("wcvp")
            if not sources:
                self.main_window.backend.emit_log(
                    "Please select at least one TNRS source", "WARNING"
                )
                return
            tnrs_sources = ",".join(sources)

            try:
                tnrs_accuracy = float(self.cds_tnrs_accuracy.text().strip())
                if not (0 < tnrs_accuracy <= 1):
                    self.main_window.backend.emit_log(
                        "Accuracy must be > 0 and <= 1", "WARNING"
                    )
                    return
            except ValueError:
                self.main_window.backend.emit_log(
                    "Invalid accuracy value", "WARNING"
                )
                return

        self.main_window.backend.emit_log("CDS selection started...", "INFO")
        self.main_window.backend.run_select_cds(
            in_folder, out_folder, enable_tax_res, tnrs_sources, tnrs_accuracy
        )

    def on_cds_gf_out_changed(self, text):
        if text:
            self.cds_select_in.setText(text)

    def on_cds_select_out_changed(self, text):
        pass

    def on_chloro_qc_out_changed(self, text):
        if text:
            self.chloro_pga_in.setText(text)

    def on_chloro_pga_clade_changed(self, text):
        if text == "User defined":
            self.chloro_pga_ref.setEnabled(True)
            self.btn_chloro_pga_ref.setEnabled(True)
        else:
            self.chloro_pga_ref.setEnabled(False)
            self.btn_chloro_pga_ref.setEnabled(False)
            self.chloro_pga_ref.clear()

    def on_chloro_pga(self):
        in_folder = self.chloro_pga_in.text().strip()
        ori_gb_folder = self.chloro_qc_in.text().strip()
        clade = self.chloro_pga_clade.currentText()
        ref_folder = self.chloro_pga_ref.text().strip()

        if not in_folder:
            self.main_window.backend.emit_log(
                "Please select input directory", "WARNING"
            )
            return

        if not ori_gb_folder:
            self.main_window.backend.emit_log(
                "Please select input directory of Extract & QC", "WARNING"
            )
            return

        if clade == "User defined" and not ref_folder:
            self.main_window.backend.emit_log(
                "Please select reference genome directory", "WARNING"
            )
            return

        self.main_window.backend.emit_log(
            "Plastid Genome Annotation started...", "INFO"
        )
        self.main_window.backend.run_pga(in_folder, ori_gb_folder, clade, ref_folder)


class DependenciesInterface(QWidget):
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        self.setObjectName("dependencies_interface")

        w = QWidget()
        layout = QVBoxLayout(w)
        layout.setContentsMargins(30, 30, 30, 30)

        grp = SettingCardGroup("Dependencies", w)

        card_install = CardWidget()
        card_install.setFixedHeight(80)
        h_install = QHBoxLayout(card_install)
        h_install.setContentsMargins(15, 10, 15, 10)
        h_install.setSpacing(30)

        btn_mafft = PrimaryPushButton("Install MAFFT", card_install)
        btn_mafft.clicked.connect(main_window.run_install_mafft)
        h_install.addWidget(btn_mafft, 1)

        btn_trim = PrimaryPushButton("Install trimAl", card_install)
        btn_trim.clicked.connect(main_window.run_install_trimal)
        h_install.addWidget(btn_trim, 1)

        btn_pga = PrimaryPushButton("Install PGA", card_install)
        btn_pga.clicked.connect(main_window.run_install_pga)
        h_install.addWidget(btn_pga, 1)

        grp.addSettingCard(card_install)
        layout.addWidget(grp)

        layout.addSpacing(20)

        app_settings_grp = SettingCardGroup("Themes", w)

        card_theme = CardWidget()
        card_theme.setFixedHeight(80)
        h_theme = QHBoxLayout(card_theme)
        h_theme.setContentsMargins(15, 10, 15, 10)
        h_theme.setSpacing(30)

        theme_container = QWidget(card_theme)
        theme_layout = QHBoxLayout(theme_container)
        theme_layout.setContentsMargins(0, 0, 0, 0)
        theme_layout.addWidget(BodyLabel("Theme:"))
        self.combo_theme = ComboBox(card_theme)
        self.combo_theme.addItems(["Light", "Dark", "Auto"])
        self.combo_theme.setCurrentIndex(1)
        self.combo_theme.currentIndexChanged.connect(main_window.change_theme)
        theme_layout.addWidget(self.combo_theme)
        h_theme.addWidget(theme_container, 1)

        color_container = QWidget(card_theme)
        color_layout = QHBoxLayout(color_container)
        color_layout.setContentsMargins(0, 0, 0, 0)
        color_layout.addWidget(BodyLabel("Color:"))
        self.color_picker = ColorPickerButton(
            parent=card_theme, title="Color", color="#9fbfff"
        )
        self.color_picker.colorChanged.connect(lambda c: setThemeColor(c, save=True))
        color_layout.addWidget(self.color_picker)
        h_theme.addWidget(color_container, 1)

        app_settings_grp.addSettingCard(card_theme)
        layout.addWidget(app_settings_grp)

        layout.addSpacing(20)

        about_grp = SettingCardGroup("About", w)
        card_about = CardWidget()
        card_about.setFixedHeight(80)
        h_about = QHBoxLayout(card_about)
        h_about.setContentsMargins(15, 10, 15, 10)
        h_about.setSpacing(20)

        h_about.addWidget(BodyLabel("Developed by Ruijing Cheng & Yuxuan Wang under GPL v3 License"), 1)
        #h_about.addWidget(BodyLabel("License: GPL V3"), 1)

        btn_github = PrimaryPushButton("View Github Page", card_about)
        btn_github.setIcon(FIF.GITHUB)
        btn_github.clicked.connect(main_window.open_github_page)
        h_about.addWidget(btn_github, 1)

        about_grp.addSettingCard(card_about)
        layout.addWidget(about_grp)

        layout.addStretch(1)

        main_vbox = QVBoxLayout(self)
        main_vbox.setContentsMargins(0, 0, 0, 0)
        main_vbox.addWidget(w)


class MainWindow(FluentWindow):
    @Slot(str)
    def outputWritten(self, text):
        self.log_widget.append_text(text)

    @Slot(str, str)
    def show_infobar(self, level, message):
        if level == "ERROR":
            InfoBar.error(
                title=level,
                content=message,
                parent=self,
                position=InfoBarPosition.TOP,
                duration=5000,
            )
        elif level == "WARNING":
            InfoBar.warning(
                title=level,
                content=message,
                parent=self,
                position=InfoBarPosition.TOP,
                duration=5000,
            )
        elif level == "SUCCESS":
            InfoBar.success(
                title=level,
                content=message,
                parent=self,
                position=InfoBarPosition.TOP,
                duration=5000,
            )
        else:
            InfoBar.info(
                title=level,
                content=message,
                parent=self,
                position=InfoBarPosition.TOP,
                duration=5000,
            )

    @Slot(int)
    def handle_count(self, count):
        message = f"Entrez search results count: {count}\n"
        self.log_widget.append_text(f"[INFO] {message}")
        InfoBar.success(
            title="SUCCESS",
            content=message,
            parent=self,
            position=InfoBarPosition.TOP,
            duration=5000,
        )

    def __init__(self):
        super().__init__()
        self.setWindowTitle("PyNCBIminer-NG")
        self.setWindowIcon(QIcon(get_resource_path("icons/app_icon.ico")))
        self.navigationInterface.setExpandWidth(180)

        self.setMinimumWidth(850)
        #self.setMinimumHeight(70)

        self.resize(1100, 750)
        screen = QApplication.primaryScreen()
        screen_geometry = screen.availableGeometry()
        x = (screen_geometry.width() - self.width()) // 2
        y = (screen_geometry.height() - self.height()) // 2
        self.move(x, y)

        setThemeColor("#6eadff", save=False)

        self.backend = BackendController()
        self.backend.log_signal.connect(self.outputWritten)
        self.backend.infobar_signal.connect(self.show_infobar)
        self.backend.count_signal.connect(self.handle_count)

        self.retrieval_interface = RetrievalInterface(self)
        self.construction_interface = ConstructionInterface(self)
        self.chloroplast_miner_interface = ChloroplastMinerInterface(self)
        self.dependencies_interface = DependenciesInterface(self)

        self.addSubInterface(self.retrieval_interface, FIF.LIBRARY, "DNAseqs")
        self.addSubInterface(
            self.chloroplast_miner_interface, FIF.LEAF, "Chloroplast"
        )
        self.addSubInterface(
            self.construction_interface, FIF.APPLICATION, "Supermatrix"
        )
        self.addSubInterface(
            self.dependencies_interface, FIF.SETTING, "Settings"
        )

        self.console_interface = QWidget()
        self.console_interface.setObjectName("console_interface")
        console_layout = QVBoxLayout(self.console_interface)
        self.log_widget = LogWidget()
        console_layout.addWidget(self.log_widget)
        self.addSubInterface(
            self.console_interface,
            FIF.COMMAND_PROMPT,
            "Console",
            NavigationItemPosition.BOTTOM,
        )

        sys.stdout = EmittingStr()
        sys.stdout.textWritten.connect(self.outputWritten)
        sys.stderr = EmittingStr()
        sys.stderr.textWritten.connect(self.outputWritten)

        self.connect_logic()

        self.mafft_checked = False
        self.trimal_checked = False

    def closeEvent(self, event):
        event.accept()

    def connect_logic(self):
        ri = self.retrieval_interface
        ri.combo_region.currentIndexChanged.connect(self.on_region_combo_changed)
        ri.combo_region.currentIndexChanged.connect(self.select_target_region)
        ri.new_region_edit.textChanged.connect(self.on_new_region_changed)
        ri.btn_set_region.clicked.connect(self.set_target_region)
        ri.btn_save_settings.clicked.connect(self.save_settings)
        ri.btn_esearch.clicked.connect(self.my_esearch)
        ri.btn_submit_blast.clicked.connect(self.submit_new_blast)
        ri.btn_load_job.clicked.connect(self.load_previous_job)
        ri.btn_stop.clicked.connect(self.stop_blast)
        ri.chk_summary.stateChanged.connect(self.set_marker_summary)

        ri.btn_run_filter.clicked.connect(self.run_filtering)

        ci = self.construction_interface
        ci.combo_trim_method.currentIndexChanged.connect(self.select_tri_method)

        ci.btn_run_replace.clicked.connect(self.run_replacement)
        ci.btn_run_align.clicked.connect(self.run_alignment)
        ci.btn_run_trim.clicked.connect(self.run_trimming)
        ci.btn_run_concat.clicked.connect(self.run_concatenation)

        ri.btn_set_region.setEnabled(False)
        ri.new_region_edit.setEnabled(True)
        self.set_marker_summary(0)
        self.select_tri_method()

    def on_region_combo_changed(self):
        ri = self.retrieval_interface
        target_region = ri.combo_region.currentText()
        ri.new_region_edit.setEnabled(target_region == "")
        if target_region != "":
            ri.new_region_edit.clear()

    def on_new_region_changed(self):
        ri = self.retrieval_interface
        if ri.new_region_edit.text().strip():
            ri.combo_region.setCurrentIndex(0)

    def select_target_region(self):
        ri = self.retrieval_interface
        target_region = ri.combo_region.currentText()
        if target_region == "":
            ri.btn_save_settings.setEnabled(True)
            ri.btn_set_region.setEnabled(False)
        else:
            ri.btn_save_settings.setEnabled(False)
            ri.btn_set_region.setEnabled(True)

    def set_target_region(self):
        ri = self.retrieval_interface
        new_region = ri.new_region_edit.text().strip()
        if new_region:
            target_region = new_region
        else:
            target_region = ri.combo_region.currentText()

        if target_region == "":
            return

        parameters_dict = {}
        blast_params_dir = Path(get_writable_path("blast_parameters"))
        custom_params_file = blast_params_dir / Path(target_region + ".txt")

        if custom_params_file.exists():
            params_file = custom_params_file
        else:
            params_file = Path(get_resource_path("blast_parameters")) / Path(
                target_region + ".txt"
            )

        with open(params_file, "r") as fr:
            parameters = fr.read().splitlines()
            for i, parameter in enumerate(parameters, 1):
                if parameter.strip() == "":
                    continue
                parts = parameter.split("\t")
                if len(parts) >= 2:
                    parameters_dict[parts[0]] = str(parts[1])
                else:
                    self.backend.emit_log(
                        f"Line {i} invalid format: {parameter[:20]}...", "WARNING"
                    )

        ri.init_queries.clear()
        initial_queries_dir = Path(get_writable_path("initial_queries"))
        custom_queries_dir = initial_queries_dir / Path(target_region)

        if custom_queries_dir.exists():
            queries_dir = custom_queries_dir
        else:
            queries_dir = Path(get_resource_path("initial_queries")) / Path(
                target_region
            )

        if queries_dir.exists():
            for file in [f.name for f in Path(queries_dir).iterdir() if f.is_file()]:
                with open(queries_dir / Path(file), "r") as fr:
                    ri.init_queries.appendPlainText(fr.read() + "\n")

        ri.entrez_qualifier.setPlainText(parameters_dict.get("entrez_qualifier", ""))
        ri.max_len.setText(parameters_dict.get("max_length", ""))
        ri.expect_val.setText(parameters_dict.get("expect_value", ""))
        ri.gap_costs.setText(parameters_dict.get("gap_costs", ""))
        ri.word_size.setText(parameters_dict.get("word_size", ""))
        ri.nucl_reward.setText(parameters_dict.get("nucl_reward", ""))
        ri.nucl_penalty.setText(parameters_dict.get("nucl_penalty", ""))
        ri.key_anno.setPlainText(
            parameters_dict.get("key_annotations", "").replace("|", "; ")
        )
        ri.excl_source.setPlainText(
            parameters_dict.get("exclude_sources", "").replace("|", "\n")
        )

        print(f"Set target region: {target_region}")
        InfoBar.success(
            title="Success",
            content=f"Loaded parameters for {target_region}",
            parent=self,
            position=InfoBarPosition.TOP,
            duration=5000,
        )

    def save_settings(self):
        self.backend.save_settings(self.retrieval_interface, self)

    def my_esearch(self):
        self.backend.my_esearch(self.retrieval_interface)

    def submit_new_blast(self):
        self.backend.submit_new_blast(self.retrieval_interface, self)

    def load_previous_job(self):
        self.backend.load_previous_job(self.retrieval_interface, self)

    def stop_blast(self):
        self.backend.stop_blast(self.retrieval_interface)

    def set_marker_summary(self, state):
        self.backend.set_marker_summary(self.retrieval_interface, state)

    def set_reduce_threshold(self, state):
        self.backend.set_reduce_threshold(self.retrieval_interface, state)

    def select_tri_method(self):
        self.backend.select_tri_method(self.construction_interface)

    def run_filtering(self):
        self.backend.run_filtering(self.retrieval_interface)
    def run_replacement(self):
        self.backend.run_replacement(self.construction_interface)

    def run_alignment(self):
        self.backend.run_alignment(self.construction_interface)

    def run_trimming(self):
        self.backend.run_trimming(self.construction_interface)

    def run_concatenation(self):
        self.backend.run_concatenation(self.construction_interface)

    def run_install_mafft(self):
        self.backend.run_install_mafft()

    def run_install_trimal(self):
        self.backend.run_install_trimal()

    def run_install_pga(self):
        self.backend.run_install_pga()

    def change_theme(self, index):
        if index == 0:
            setTheme(Theme.LIGHT)
        elif index == 1:
            setTheme(Theme.DARK)
        elif index == 2:
            setTheme(Theme.AUTO)

    def open_github_page(self):
        from PySide6.QtCore import QUrl
        from PySide6.QtGui import QDesktopServices

        QDesktopServices.openUrl(QUrl("https://github.com/wyx619/PyNCBIminer_NG"))

if __name__ == "__main__":
    import ctypes
    ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID('PyNCBIminer-NG')

    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )
    app = QApplication(sys.argv)

    app.setApplicationName("PyNCBIminer-NG")
    app.setOrganizationName("Sichuan University")
    app.setApplicationDisplayName("PyNCBIminer-NG")
    setTheme(Theme.DARK)

    w = MainWindow()
    w.show()
    sys.exit(app.exec())
