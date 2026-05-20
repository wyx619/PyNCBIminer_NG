# *-* coding:utf-8 *-*
import sys
from pathlib import Path

from PySide6.QtCore import (
    QDate,
    QEasingCurve,
    QEventLoop,
    QObject,
    QPropertyAnimation,
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

try:
    from qframelesswindow.utils import getSystemAccentColor

    HAS_SYSTEM_ACCENT = True
except ImportError:
    HAS_SYSTEM_ACCENT = False

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
    setTheme,
    setThemeColor,
    themeColor,
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

        basic_group = SettingCardGroup("Basic Settings", view)

        tax_card = CardWidget(view)
        tax_card.setFixedHeight(150)
        tax_layout = QVBoxLayout(tax_card)
        tax_layout.setContentsMargins(15, 10, 15, 15)
        tax_layout.addWidget(BodyLabel("Target Groups (Taxonomy):"))
        self.tax_edit = PlainTextEdit(tax_card)
        self.tax_edit.setPlaceholderText("One taxon per line")
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
        entrez_card.setFixedHeight(230)
        ent_layout = QVBoxLayout(entrez_card)
        ent_layout.setContentsMargins(15, 10, 15, 10)

        row1 = QHBoxLayout()
        self.entrez_qualifier = PlainTextEdit(entrez_card)
        ent_layout.addWidget(BodyLabel("Entrez Qualifier:"))
        self.entrez_qualifier.setPlaceholderText(
            "Constraint on BLAST search (Entrez Qualifier)"
        )
        self.entrez_qualifier.setFixedHeight(100)
        row1.addWidget(self.entrez_qualifier)
        ent_layout.addLayout(row1)

        row2 = QHBoxLayout()
        self.email_edit = LineEdit(entrez_card)
        self.email_edit.setPlaceholderText("User's Email")
        row2.addWidget(BodyLabel("Email:"))
        row2.addWidget(self.email_edit)
        ent_layout.addLayout(row2)

        row3 = QHBoxLayout()
        self.date_from = DatePicker(entrez_card)
        self.date_from.setDate(QDate())
        self.date_from_cleared = True
        self.date_from.dateChanged.connect(self.on_date_from_changed)
        self.btn_clear_from = PushButton("Reset", entrez_card)

        self.btn_clear_from.clicked.connect(self.clear_date_from)
        row3.addWidget(BodyLabel("Date From:"))
        row3.addWidget(self.date_from)
        row3.addWidget(self.btn_clear_from)
        row3.addStretch()

        self.date_to = DatePicker(entrez_card)
        self.date_to.setDate(QDate())
        self.date_to_cleared = True
        self.date_to.dateChanged.connect(self.on_date_to_changed)
        self.btn_clear_to = PushButton("Reset", entrez_card)

        self.btn_clear_to.clicked.connect(self.clear_date_to)
        row3.addWidget(BodyLabel("Date To:"))
        row3.addWidget(self.date_to)
        row3.addWidget(self.btn_clear_to)
        ent_layout.addLayout(row3)

        basic_group.addSettingCard(entrez_card)

        action_card = CardWidget(view)
        action_card.setFixedHeight(80)
        act_layout = QHBoxLayout(action_card)
        act_layout.setContentsMargins(15, 10, 15, 10)
        self.chk_summary = CheckBox("Summarize widely used marker", action_card)
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

        grp = SettingCardGroup("Sequence Filtering", w)

        card_opts = CardWidget()
        card_opts.setFixedHeight(220)
        l_opts = QVBoxLayout(card_opts)
        l_opts.setContentsMargins(15, 10, 15, 10)

        row1 = QHBoxLayout()
        self.switch_ext = SwitchButton(card_opts)
        self.switch_ext.setChecked(False)
        row1.addWidget(BodyLabel("Extended segments refinement"))
        row1.addWidget(self.switch_ext)
        row1.addStretch()
        l_opts.addLayout(row1)

        row2 = QHBoxLayout()
        self.switch_reduce = SwitchButton(card_opts)
        self.switch_reduce.setChecked(False)
        self.switch_reduce.checkedChanged.connect(self.on_switch_reduce_changed)
        row2.addWidget(BodyLabel("Species-level sequence selection"))
        row2.addWidget(self.switch_reduce)
        row2.addSpacing(40)
        row2.addWidget(BodyLabel("Length Threshold:"))
        self.len_thresh = LineEdit()
        self.len_thresh.setText("100")
        self.len_thresh.setEnabled(False)
        # self.len_thresh.setFixedWidth(240)
        row2.addWidget(self.len_thresh)
        row2.addSpacing(40)
        self.chk_consensus = CheckBox("Calculate Consensus", card_opts)
        self.chk_consensus.setChecked(True)
        self.chk_consensus.setEnabled(False)
        row2.addWidget(self.chk_consensus)
        l_opts.addLayout(row2)

        row3 = QHBoxLayout()
        self.filter_in = LineEdit()
        self.filter_in.setPlaceholderText(
            "One working directory"
        )
        btn_in = PushButton("Browse")
        btn_in.setIcon(FIF.FOLDER)
        btn_in.clicked.connect(lambda: self.browse_dir(self.filter_in))
        row3.addWidget(BodyLabel("Input Path:"))
        row3.addWidget(self.filter_in, 1)
        row3.addWidget(btn_in)
        l_opts.addLayout(row3)

        row4 = QHBoxLayout()
        self.filter_out = LineEdit()
        self.filter_out.setPlaceholderText("The same as input path by default")
        btn_out = PushButton("Browse")
        btn_out.setIcon(FIF.FOLDER)
        btn_out.clicked.connect(lambda: self.browse_dir(self.filter_out))
        row4.addWidget(BodyLabel("Output Path:"))
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

    def browse_dir(self, line_edit):
        path = QFileDialog.getExistingDirectory(self, "Select Directory")
        if path:
            line_edit.setText(path)

    def select_wd(self):
        path = QFileDialog.getExistingDirectory(self, "Select Working Directory")
        if path:
            self.wd_edit.setText(path)

    def clear_date_from(self):
        self.date_from.setDate(QDate())
        self.date_from_cleared = True

    def clear_date_to(self):
        self.date_to.setDate(QDate())
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

        self.page_align = self.create_alignment_page()
        self.page_trim = self.create_trimming_page()
        self.page_concat = self.create_concat_page()

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
        row_rb = QHBoxLayout()
        row_rb.addWidget(self.rb_align_single)
        row_rb.addWidget(self.rb_align_multi)
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
        h1.addWidget(BodyLabel("Input:"))
        h1.addWidget(self.align_in)
        h1.addWidget(btn_in)
        h2 = QHBoxLayout()
        h2.addWidget(BodyLabel("Output:"))
        h2.addWidget(self.align_out)
        h2.addWidget(btn_out)
        l_opts.addLayout(h1)
        l_opts.addLayout(h2)

        self.align_thread = LineEdit()
        self.align_thread.setText("-1")
        self.align_thread.setFixedWidth(80)
        self.align_algo = ComboBox()
        self.align_algo.addItems(
            [
                "auto(depends on datasize)",
                "add(use long sequences as backbone to align fragment sequences)",
            ]
        )
        self.chk_reorder = CheckBox("Reorder", card_opts)
        self.chk_reorder.setChecked(True)

        row_param = QHBoxLayout()
        row_param.addWidget(BodyLabel("Threads:"))
        row_param.addWidget(self.align_thread)
        row_param.addSpacing(10)
        row_param.addWidget(BodyLabel("Strategy:"))
        row_param.addWidget(self.align_algo, 1)
        row_param.addSpacing(10)
        row_param.addWidget(self.chk_reorder)
        row_param.addStretch()
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
        self.chk_chloroplast = CheckBox("Chloroplast Mode")
        self.chk_chloroplast.setChecked(False)
        self.chk_chloroplast.stateChanged.connect(self.on_chloroplast_mode_changed)
        self.rb_trim_single.setChecked(True)
        row_rb = QHBoxLayout()
        row_rb.addWidget(self.rb_trim_single)
        row_rb.addStretch(1)
        row_rb.addWidget(self.rb_trim_multi)
        row_rb.addStretch(1)
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
        h1.addWidget(BodyLabel("Input:"))
        h1.addWidget(self.trim_in)
        h1.addWidget(btn_in)
        h2 = QHBoxLayout()
        h2.addWidget(BodyLabel("Output:"))
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
            "the folder path that contains multiple fasta files"
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
        h1.addWidget(BodyLabel("Input Folder:"))
        h1.addWidget(self.concat_in)
        h1.addWidget(btn_in)

        h2 = QHBoxLayout()
        h2.addWidget(BodyLabel("Output Folder:"))
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

    def on_chloroplast_mode_changed(self, state):
        is_chloroplast = state == 2
        self.rb_trim_single.setEnabled(not is_chloroplast)
        if is_chloroplast:
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
        if hasattr(self, "chloro_qc_in") and hasattr(self, "chloro_download_dir_edit"):
            download_dir = self.chloro_download_dir_edit.text().strip()
            if download_dir and not self.chloro_qc_in.text().strip():
                self.chloro_qc_in.setText(download_dir)

    def addSubInterface(self, widget: QWidget, objectName, text):
        widget.setObjectName(objectName)
        self.stackedWidget.addWidget(widget)
        self.pivot.addItem(routeKey=objectName, text=text)

    def create_search_page(self):
        w = SingleDirectionScrollArea()
        w.setWidgetResizable(True)
        view = QWidget()
        layout = QVBoxLayout(view)
        layout.setContentsMargins(5, 20, 20, 20)
        layout.setSpacing(20)

        grp_search = SettingCardGroup("Search", view)

        card = CardWidget()
        card.setFixedHeight(230)
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(15, 10, 15, 10)

        self.chloro_tax_edit = PlainTextEdit()
        self.chloro_tax_edit.setPlaceholderText("Enter taxon names (one per line)")
        self.chloro_tax_edit.setFixedHeight(80)
        card_layout.addWidget(BodyLabel("Target Taxa:"))
        card_layout.addWidget(self.chloro_tax_edit)
        card_layout.addSpacing(10)

        self.chloro_date_from = DatePicker(card)
        self.chloro_date_from.setDate(QDate())
        self.chloro_date_from_cleared = True
        self.chloro_date_from.dateChanged.connect(self.on_chloro_date_from_changed)
        self.chloro_btn_clear_from = PushButton("Reset", card)
        self.chloro_btn_clear_from.clicked.connect(self.clear_chloro_date_from)

        self.chloro_date_to = DatePicker(card)
        self.chloro_date_to.setDate(QDate())
        self.chloro_date_to_cleared = True
        self.chloro_date_to.dateChanged.connect(self.on_chloro_date_to_changed)
        self.chloro_btn_clear_to = PushButton("Reset", card)
        self.chloro_btn_clear_to.clicked.connect(self.clear_chloro_date_to)

        h_date = QHBoxLayout()
        h_date.addWidget(BodyLabel("Date From:"))
        h_date.addWidget(self.chloro_date_from)
        h_date.addWidget(self.chloro_btn_clear_from)
        h_date.addStretch()
        h_date.addWidget(BodyLabel("Date To:"))
        h_date.addWidget(self.chloro_date_to)
        h_date.addWidget(self.chloro_btn_clear_to)
        card_layout.addLayout(h_date)
        card_layout.addSpacing(10)

        self.btn_chloro_search = PushButton("Search", self)
        self.btn_chloro_search.setIcon(FIF.GLOBE)
        self.btn_chloro_search.clicked.connect(self.on_chloro_search)
        card_layout.addWidget(self.btn_chloro_search)

        grp_search.addSettingCard(card)
        layout.addWidget(grp_search)

        grp_download = SettingCardGroup("Download", view)

        card_download = CardWidget()
        card_download.setFixedHeight(220)
        download_layout = QVBoxLayout(card_download)
        download_layout.setContentsMargins(15, 10, 15, 10)

        self.chloro_wd_edit = LineEdit()
        self.chloro_wd_edit.setPlaceholderText("Index File Path")
        btn_chloro_wd = PushButton("Browse")
        btn_chloro_wd.setIcon(FIF.FOLDER)
        btn_chloro_wd.clicked.connect(lambda: self.browse_file(self.chloro_wd_edit))

        h_box = QHBoxLayout()
        h_box.addWidget(BodyLabel("Index File:"))
        h_box.addWidget(self.chloro_wd_edit)
        h_box.addWidget(btn_chloro_wd)

        self.chloro_download_dir_edit = LineEdit()
        self.chloro_download_dir_edit.setPlaceholderText("Download Directory Path")
        btn_chloro_download_dir = PushButton("Browse")
        btn_chloro_download_dir.setIcon(FIF.FOLDER)
        btn_chloro_download_dir.clicked.connect(
            lambda: self.browse_folder(self.chloro_download_dir_edit)
        )

        h_box2 = QHBoxLayout()
        h_box2.addWidget(BodyLabel("Download Directory:"))
        h_box2.addWidget(self.chloro_download_dir_edit)
        h_box2.addWidget(btn_chloro_download_dir)

        self.chloro_email_edit = LineEdit()
        self.chloro_email_edit.setPlaceholderText("Email (required for NCBI)")

        h_box3 = QHBoxLayout()
        h_box3.addWidget(BodyLabel("Email:"))
        h_box3.addWidget(self.chloro_email_edit)

        download_layout.addSpacing(10)
        download_layout.addLayout(h_box)
        download_layout.addSpacing(10)
        download_layout.addLayout(h_box2)
        download_layout.addSpacing(10)
        download_layout.addLayout(h_box3)
        download_layout.addSpacing(10)

        self.btn_chloro_download = PushButton("Download")
        self.btn_chloro_download.setIcon(FIF.DOWNLOAD)
        self.btn_chloro_download.clicked.connect(self.on_chloro_download)
        download_layout.addWidget(self.btn_chloro_download)

        grp_download.addSettingCard(card_download)
        layout.addWidget(grp_download)

        grp_prefilter = SettingCardGroup("Pre-filter", view)

        card_prefilter = CardWidget()
        card_prefilter.setFixedHeight(240)
        prefilter_layout = QVBoxLayout(card_prefilter)
        prefilter_layout.setContentsMargins(15, 10, 15, 10)

        self.prefilter_in_edit = LineEdit()
        self.prefilter_in_edit.setPlaceholderText("Input directory with downloaded GeneBank files")
        btn_prefilter_in = PushButton("Browse")
        btn_prefilter_in.setIcon(FIF.FOLDER)
        btn_prefilter_in.clicked.connect(lambda: self.browse_folder(self.prefilter_in_edit))

        h_pf_in = QHBoxLayout()
        h_pf_in.addWidget(BodyLabel("Input Directory:"))
        h_pf_in.addWidget(self.prefilter_in_edit)
        h_pf_in.addWidget(btn_prefilter_in)
        prefilter_layout.addLayout(h_pf_in)

        self.chloro_download_dir_edit.textChanged.connect(
            lambda text: self.prefilter_in_edit.setText(text)
        )

        self.prefilter_out_edit = LineEdit()
        self.prefilter_out_edit.setPlaceholderText("Output directory for filtered GeneBank files")
        btn_prefilter_out = PushButton("Browse")
        btn_prefilter_out.setIcon(FIF.FOLDER)
        btn_prefilter_out.clicked.connect(lambda: self.browse_folder(self.prefilter_out_edit))

        h_pf_out = QHBoxLayout()
        h_pf_out.addWidget(BodyLabel("Output Directory:"))
        h_pf_out.addWidget(self.prefilter_out_edit)
        h_pf_out.addWidget(btn_prefilter_out)
        prefilter_layout.addLayout(h_pf_out)

        h_pf_opts = QHBoxLayout()
        self.prefilter_species_switch = SwitchButton()
        self.prefilter_species_switch.setChecked(False)
        h_pf_opts.addWidget(BodyLabel("Species Level Merge:"))
        h_pf_opts.addWidget(self.prefilter_species_switch)
        h_pf_opts.addSpacing(20)
        h_pf_opts.addWidget(BodyLabel("Records Kept for Each Taxon:"))
        self.prefilter_keep_edit = LineEdit()
        self.prefilter_keep_edit.setText("3")
        self.prefilter_keep_edit.setFixedWidth(40)
        h_pf_opts.addWidget(self.prefilter_keep_edit)
        h_pf_opts.addStretch()
        prefilter_layout.addLayout(h_pf_opts)

        self.btn_chloro_prefilter = PushButton("Run Pre-filter")
        self.btn_chloro_prefilter.setIcon(FIF.FILTER)
        self.btn_chloro_prefilter.clicked.connect(self.on_chloro_prefilter)
        prefilter_layout.addWidget(self.btn_chloro_prefilter)

        grp_prefilter.addSettingCard(card_prefilter)
        layout.addWidget(grp_prefilter)
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

        card = CardWidget()
        card.setFixedHeight(220)
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(15, 10, 15, 10)

        h_input = QHBoxLayout()
        self.chloro_qc_in = LineEdit()
        self.chloro_qc_in.setPlaceholderText("Input directory containing pre-filtered GenBank files")
        btn_chloro_qc_in = PushButton("Browse")
        btn_chloro_qc_in.setIcon(FIF.FOLDER)
        btn_chloro_qc_in.clicked.connect(lambda: self.browse_folder(self.chloro_qc_in))
        h_input.addWidget(BodyLabel("Input Directory:"))
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
        h_output.addWidget(BodyLabel("Output Directory:"))
        h_output.addWidget(self.chloro_qc_out)
        h_output.addWidget(btn_chloro_qc_out)
        card_layout.addLayout(h_output)

        self.chloro_cds_thresh = LineEdit()
        self.chloro_cds_thresh.setText("75")
        self.chloro_ambig_thresh = LineEdit()
        self.chloro_ambig_thresh.setText("0.1")

        h_threshold = QHBoxLayout()
        h_threshold.addWidget(BodyLabel("CDS Threshold:"))
        h_threshold.addWidget(self.chloro_cds_thresh)
        h_threshold.addStretch()
        h_threshold.addWidget(BodyLabel("Ambiguity Threshold:"))
        h_threshold.addWidget(self.chloro_ambig_thresh)
        card_layout.addLayout(h_threshold)

        self.btn_chloro_qc_extract = PushButton("Extract")
        self.btn_chloro_qc_extract.setIcon(FIF.PLAY)
        self.btn_chloro_qc_extract.clicked.connect(self.on_chloro_qc_extract)
        card_layout.addWidget(self.btn_chloro_qc_extract)

        grp.addSettingCard(card)

        layout.addWidget(grp)

        grp_pga = SettingCardGroup("Plastid Genome Annotator", w)

        card_pga = CardWidget()
        card_pga.setFixedHeight(180)
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
        h_pga_input.addWidget(BodyLabel("Input Directory:"))
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
        h_pga_ref.addWidget(BodyLabel("Clades:"))
        h_pga_ref.addWidget(self.chloro_pga_clade)
        h_pga_ref.addWidget(BodyLabel("Reference Genome:"))
        h_pga_ref.addWidget(self.chloro_pga_ref)
        h_pga_ref.addWidget(self.btn_chloro_pga_ref)
        card_pga_layout.addLayout(h_pga_ref)

        self.btn_chloro_pga = PushButton("Reannotate")
        self.btn_chloro_pga.setIcon(FIF.PLAY)
        self.btn_chloro_pga.clicked.connect(self.on_chloro_pga)
        card_pga_layout.addWidget(self.btn_chloro_pga)

        grp_pga.addSettingCard(card_pga)

        layout.addWidget(grp_pga)
        layout.addStretch(1)
        return w

    def create_cds_page(self):
        w = SingleDirectionScrollArea()
        w.setWidgetResizable(True)
        self.cds_view = QWidget()
        self.cds_view.setObjectName("cds_view")
        layout = QVBoxLayout(self.cds_view)
        layout.setContentsMargins(5, 20, 20, 20)
        layout.setSpacing(20)

        grp_get = SettingCardGroup("Get CDS", self.cds_view)

        card_get = CardWidget()
        card_get.setFixedHeight(160)
        card_get_layout = QVBoxLayout(card_get)
        card_get_layout.setContentsMargins(15, 10, 15, 10)

        h_get_input = QHBoxLayout()
        self.cds_get_in = LineEdit()
        self.cds_get_in.setPlaceholderText(
            "Input directory containing filtered GenBank files"
        )
        btn_cds_get_in = PushButton("Browse")
        btn_cds_get_in.setIcon(FIF.FOLDER)
        btn_cds_get_in.clicked.connect(lambda: self.browse_folder(self.cds_get_in))
        h_get_input.addWidget(BodyLabel("Input Directory:"))
        h_get_input.addWidget(self.cds_get_in)
        h_get_input.addWidget(btn_cds_get_in)
        card_get_layout.addLayout(h_get_input)

        h_get_output = QHBoxLayout()
        self.cds_get_out = LineEdit()
        self.cds_get_out.setPlaceholderText("Output directory for CDS files")
        self.cds_get_out.textChanged.connect(self.on_cds_get_out_changed)
        btn_cds_get_out = PushButton("Browse")
        btn_cds_get_out.setIcon(FIF.FOLDER)
        btn_cds_get_out.clicked.connect(
            lambda: self.browse_folder(self.cds_get_out, self.cds_filter_in)
        )
        h_get_output.addWidget(BodyLabel("Output Directory:"))
        h_get_output.addWidget(self.cds_get_out)
        h_get_output.addWidget(btn_cds_get_out)
        card_get_layout.addLayout(h_get_output)

        self.btn_cds_get = PushButton("Extract CDS")
        self.btn_cds_get.setIcon(FIF.CODE)
        self.btn_cds_get.clicked.connect(self.on_cds_get_extract)
        card_get_layout.addWidget(self.btn_cds_get)

        grp_get.addSettingCard(card_get)
        layout.addWidget(grp_get)

        grp_filter = SettingCardGroup("Filter CDS", self.cds_view)

        card_filter = CardWidget()
        card_filter.setFixedHeight(210)
        card_filter_layout = QVBoxLayout(card_filter)
        card_filter_layout.setContentsMargins(15, 10, 15, 10)

        h_filter_input = QHBoxLayout()
        self.cds_filter_in = LineEdit()
        self.cds_filter_in.setPlaceholderText("Input directory containing CDS files")
        btn_cds_filter_in = PushButton("Browse")
        btn_cds_filter_in.setIcon(FIF.FOLDER)
        btn_cds_filter_in.clicked.connect(
            lambda: self.browse_folder(self.cds_filter_in)
        )
        h_filter_input.addWidget(BodyLabel("Input Directory:"))
        h_filter_input.addWidget(self.cds_filter_in)
        h_filter_input.addWidget(btn_cds_filter_in)
        card_filter_layout.addLayout(h_filter_input)

        h_filter_output = QHBoxLayout()
        self.cds_filter_out = LineEdit()
        self.cds_filter_out.setPlaceholderText(
            "Output directory for filtered CDS files"
        )
        self.cds_filter_out.textChanged.connect(self.on_cds_filter_out_changed)
        btn_cds_filter_out = PushButton("Browse")
        btn_cds_filter_out.setIcon(FIF.FOLDER)
        btn_cds_filter_out.clicked.connect(
            lambda: self.browse_folder(self.cds_filter_out, self.cds_select_in)
        )
        h_filter_output.addWidget(BodyLabel("Output Directory:"))
        h_filter_output.addWidget(self.cds_filter_out)
        h_filter_output.addWidget(btn_cds_filter_out)
        card_filter_layout.addLayout(h_filter_output)

        h_filter_params = QHBoxLayout()
        self.cds_filter_ref = ComboBox()
        self.cds_filter_ref.addItems(["Angiosperms", "Gymnosperms"])

        self.cds_filter_ref.setCurrentIndex(0)
        self.cds_filter_lb = LineEdit()
        self.cds_filter_lb.setText("0.5")

        self.cds_filter_ub = LineEdit()
        self.cds_filter_ub.setText("2.0")

        h_filter_params.addWidget(BodyLabel("Reference:"))
        h_filter_params.addWidget(self.cds_filter_ref)
        h_filter_params.addStretch(1)
        h_filter_params.addWidget(BodyLabel("Lower Bound:"))
        h_filter_params.addWidget(self.cds_filter_lb)
        h_filter_params.addStretch(1)
        h_filter_params.addWidget(BodyLabel("Upper Bound:"))
        h_filter_params.addWidget(self.cds_filter_ub)
        card_filter_layout.addLayout(h_filter_params)

        self.btn_cds_filter = PushButton("Filter CDS")
        self.btn_cds_filter.setIcon(FIF.FILTER)
        self.btn_cds_filter.clicked.connect(self.on_cds_filter_extract)
        card_filter_layout.addWidget(self.btn_cds_filter)

        grp_filter.addSettingCard(card_filter)
        layout.addWidget(grp_filter)

        grp_select = SettingCardGroup("Select CDS", self.cds_view)

        card_select = CardWidget()
        card_select.setFixedHeight(200)
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
        h_select_input.addWidget(BodyLabel("Input Directory:"))
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
        h_select_output.addWidget(BodyLabel("Output Directory:"))
        h_select_output.addWidget(self.cds_select_out)
        h_select_output.addWidget(btn_cds_select_out)
        card_select_layout.addLayout(h_select_output)

        h_select_tax = QHBoxLayout()
        h_select_tax.addWidget(BodyLabel("Taxonomic Name Resolution:"))
        self.cds_select_tax_switch = SwitchButton()
        self.cds_select_tax_switch.setChecked(False)
        h_select_tax.addWidget(self.cds_select_tax_switch)
        h_select_tax.addSpacing(10)
        h_select_tax.addWidget(BodyLabel("Resolution Source:"))
        self.cds_select_tax_file = LineEdit()
        self.cds_select_tax_file.setPlaceholderText("Select file (.csv) [ID , organism , new_name]")
        self.cds_select_tax_file.setEnabled(False)

        btn_cds_select_tax_file = PushButton("Browse")
        btn_cds_select_tax_file.setIcon(FIF.FOLDER)
        btn_cds_select_tax_file.setEnabled(False)
        btn_cds_select_tax_file.clicked.connect(
            lambda: self.browse_csv_file(self.cds_select_tax_file)
        )
        h_select_tax.addWidget(self.cds_select_tax_file)
        h_select_tax.addWidget(btn_cds_select_tax_file)
        card_select_layout.addLayout(h_select_tax)

        self.cds_select_tax_switch.checkedChanged.connect(
            lambda checked: self.cds_select_tax_file.setEnabled(checked)
        )
        self.cds_select_tax_switch.checkedChanged.connect(
            lambda checked: btn_cds_select_tax_file.setEnabled(checked)
        )

        self.btn_cds_select = PushButton("Select CDS")
        self.btn_cds_select.setIcon(FIF.TAG)
        self.btn_cds_select.clicked.connect(self.on_cds_select_extract)
        card_select_layout.addWidget(self.btn_cds_select)

        grp_select.addSettingCard(card_select)
        layout.addWidget(grp_select)

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

    def on_chloro_download(self):
        if (
            not self.chloro_wd_edit.text().strip()
            or not self.chloro_download_dir_edit.text().strip()
            or not self.chloro_email_edit.text().strip()
        ):
            self.main_window.backend.emit_log(
                "Please select index file, download directory and enter email",
                "WARNING",
            )
            return

        email = self.chloro_email_edit.text().strip()
        in_path = self.chloro_wd_edit.text().strip()
        out_path = self.chloro_download_dir_edit.text().strip()

        self.main_window.backend.download_chloroplast_genomes(email, in_path, out_path)

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
        self.chloro_date_from.setDate(QDate())
        self.chloro_date_from_cleared = True

    def clear_chloro_date_to(self):
        self.chloro_date_to.setDate(QDate())
        self.chloro_date_to_cleared = True

    def on_chloro_search(self):
        text = self.chloro_tax_edit.toPlainText().strip()
        if not text:
            self.main_window.backend.emit_log(
                "Please enter at least one taxon name", "WARNING"
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

        from urllib.parse import quote

        from PySide6.QtCore import QUrl
        from PySide6.QtGui import QDesktopServices

        taxa = [line.strip() for line in text.split("\n") if line.strip()]

        if len(taxa) == 1:
            taxa_query = f'"{taxa[0]}"[Organism]'
        else:
            taxa_queries = " OR ".join([f'"{t}"[Organism]' for t in taxa])
            taxa_query = f"({taxa_queries})"

        query = f"{taxa_query} AND (plastid[All Fields] OR chloroplast[All Fields]) AND (100000[Sequence Length] : 300000[Sequence Length]) NOT mitochondrion[Title] NOT mitochondrial[Title] NOT chromosome[Title]"

        d_from = ""
        d_to = ""

        if has_from:
            d_from = date_from_obj.toString("yyyy/MM/dd")
        if has_to:
            d_to = date_to_obj.toString("yyyy/MM/dd")

        if d_from and d_to:
            query = f'{query} AND "{d_from}"[PDAT] : "{d_to}"[PDAT]'
        elif d_from:
            query = f'{query} AND "{d_from}"[PDAT]'

        encoded_query = quote(query, safe="()")
        url = f"https://www.ncbi.nlm.nih.gov/nuccore/?term={encoded_query}"

        QDesktopServices.openUrl(QUrl(url))

    def on_chloro_qc_extract(self):
        in_folder = self.chloro_qc_in.text().strip()
        out_folder = self.chloro_qc_out.text().strip()

        if not in_folder or not out_folder:
            self.main_window.backend.emit_log(
                "Please select both input and output directories", "WARNING"
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

    def on_cds_get_extract(self):
        in_folder = self.cds_get_in.text().strip()
        out_folder = self.cds_get_out.text().strip()

        if not in_folder or not out_folder:
            self.main_window.backend.emit_log(
                "Please select both input and output directories", "WARNING"
            )
            return

        self.main_window.backend.emit_log("CDS extraction started...", "INFO")
        self.main_window.backend.run_get_cds(in_folder, out_folder)

    def on_cds_filter_extract(self):
        in_folder = self.cds_filter_in.text().strip()
        out_folder = self.cds_filter_out.text().strip()

        if not in_folder or not out_folder:
            self.main_window.backend.emit_log(
                "Please select both input and output directories", "WARNING"
            )
            return

        ref_text = self.cds_filter_ref.currentText()
        ref_type = "Ang" if ref_text == "Angiosperms" else "Gym"

        try:
            lower_bound = float(self.cds_filter_lb.text().strip())
            if lower_bound <= 0:
                self.main_window.backend.emit_log(
                    "Lower bound must be a positive number", "WARNING"
                )
                return
        except ValueError:
            self.main_window.backend.emit_log("Invalid lower bound value", "WARNING")
            return

        try:
            upper_bound = float(self.cds_filter_ub.text().strip())
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

        self.main_window.backend.emit_log("CDS filtering started...", "INFO")
        self.main_window.backend.run_filter_cds(
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
        tax_file = self.cds_select_tax_file.text().strip() if enable_tax_res else None

        if enable_tax_res and not tax_file:
            self.main_window.backend.emit_log(
                "Please select a taxonomic name resolution file", "WARNING"
            )
            return

        self.main_window.backend.emit_log("CDS selection started...", "INFO")
        self.main_window.backend.run_select_cds(
            in_folder, out_folder, enable_tax_res, tax_file
        )

    def on_cds_get_out_changed(self, text):
        if text:
            self.cds_filter_in.setText(text)

    def on_cds_filter_out_changed(self, text):
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
                "Please select original GenBank directory", "WARNING"
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

        grp = SettingCardGroup("Dependencies Installation", w)

        card_install = CardWidget()
        card_install.setFixedHeight(80)
        h_install = QHBoxLayout(card_install)
        h_install.setContentsMargins(15, 10, 15, 10)
        h_install.setSpacing(30)

        btn_mafft = PushButton("Install MAFFT", card_install)
        btn_mafft.clicked.connect(main_window.run_install_mafft)
        h_install.addWidget(btn_mafft, 1)

        btn_trim = PushButton("Install trimAl", card_install)
        btn_trim.clicked.connect(main_window.run_install_trimal)
        h_install.addWidget(btn_trim, 1)

        btn_pga = PushButton("Install PGA", card_install)
        btn_pga.clicked.connect(main_window.run_install_pga)
        h_install.addWidget(btn_pga, 1)

        grp.addSettingCard(card_install)
        layout.addWidget(grp)

        layout.addSpacing(20)

        app_settings_grp = SettingCardGroup("Application Settings", w)

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
        self.combo_theme.setCurrentIndex(2)
        self.combo_theme.currentIndexChanged.connect(main_window.change_theme)
        theme_layout.addWidget(self.combo_theme)
        h_theme.addWidget(theme_container, 1)

        color_container = QWidget(card_theme)
        color_layout = QHBoxLayout(color_container)
        color_layout.setContentsMargins(0, 0, 0, 0)
        color_layout.addWidget(BodyLabel("Color:"))
        self.color_picker = ColorPickerButton(
            parent=card_theme, title="Color", color=themeColor()
        )
        self.color_picker.colorChanged.connect(lambda c: setThemeColor(c, save=True))
        color_layout.addWidget(self.color_picker)
        h_theme.addWidget(color_container, 1)

        about_container = QWidget(card_theme)
        about_layout = QHBoxLayout(about_container)
        about_layout.setContentsMargins(0, 0, 0, 0)
        about_layout.addWidget(BodyLabel("About:"))
        btn_about = PushButton("About PyNCBIminer-NG", card_theme)
        btn_about.setIcon(FIF.INFO)
        btn_about.clicked.connect(main_window.show_about)
        about_layout.addWidget(btn_about)
        h_theme.addWidget(about_container, 1)

        app_settings_grp.addSettingCard(card_theme)
        layout.addWidget(app_settings_grp)
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
        self.is_closing = False
        self.setWindowTitle("PyNCBIminer-NG")
        self.setWindowIcon(QIcon(get_resource_path("icons/app_icon.ico")))
        self.navigationInterface.setExpandWidth(240)

        self.setMinimumWidth(600)

        self.resize(1100, 750)
        screen = QApplication.primaryScreen()
        screen_geometry = screen.availableGeometry()
        x = (screen_geometry.width() - self.width()) // 2
        y = (screen_geometry.height() - self.height()) // 2
        self.move(x, y)

        if HAS_SYSTEM_ACCENT and sys.platform in ["win32", "darwin"]:
            setThemeColor(getSystemAccentColor(), save=False)

        self.backend = BackendController()
        self.backend.log_signal.connect(self.outputWritten)
        self.backend.infobar_signal.connect(self.show_infobar)
        self.backend.count_signal.connect(self.handle_count)

        self.retrieval_interface = RetrievalInterface(self)
        self.construction_interface = ConstructionInterface(self)
        self.chloroplast_miner_interface = ChloroplastMinerInterface(self)
        self.dependencies_interface = DependenciesInterface(self)

        self.addSubInterface(self.retrieval_interface, FIF.LIBRARY, "Fragments Miner")
        self.addSubInterface(
            self.chloroplast_miner_interface, FIF.LEAF, "Chloroplast Miner"
        )
        self.addSubInterface(
            self.construction_interface, FIF.APPLICATION, "Matrix Construction"
        )
        self.addSubInterface(
            self.dependencies_interface, FIF.SETTING, "Software Settings"
        )

        self.console_interface = QWidget()
        self.console_interface.setObjectName("console_interface")
        console_layout = QVBoxLayout(self.console_interface)
        self.log_widget = LogWidget()
        console_layout.addWidget(self.log_widget)
        self.addSubInterface(
            self.console_interface,
            FIF.COMMAND_PROMPT,
            "Console Output",
            NavigationItemPosition.BOTTOM,
        )

        sys.stdout = EmittingStr()
        sys.stdout.textWritten.connect(self.outputWritten)
        sys.stderr = EmittingStr()
        sys.stderr.textWritten.connect(self.outputWritten)

        self.connect_logic()

        self.mafft_checked = False
        self.trimal_checked = False

        self.setWindowOpacity(0)
        self.fade_in_animation = QPropertyAnimation(self, b"windowOpacity")
        self.fade_in_animation.setDuration(150)
        self.fade_in_animation.setStartValue(0)
        self.fade_in_animation.setEndValue(1)
        self.fade_in_animation.setEasingCurve(QEasingCurve.InOutQuad)
        self.fade_in_animation.start()

    def closeEvent(self, event):
        if self.is_closing:
            event.accept()
            return

        self.is_closing = True
        event.ignore()
        self.fade_out_animation = QPropertyAnimation(self, b"windowOpacity")
        self.fade_out_animation.setDuration(150)
        self.fade_out_animation.setStartValue(1)
        self.fade_out_animation.setEndValue(0)
        self.fade_out_animation.setEasingCurve(QEasingCurve.InOutQuad)
        self.fade_out_animation.finished.connect(self.close)
        self.fade_out_animation.start()

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

    def show_about(self):
        self.backend.show_about(self)


if __name__ == "__main__":
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )
    app = QApplication(sys.argv)

    app.setApplicationName("PyNCBIminer-NG")
    app.setOrganizationName("Sichuan University")
    app.setApplicationDisplayName("PyNCBIminer-NG")
    setTheme(Theme.AUTO)

    w = MainWindow()
    w.show()
    sys.exit(app.exec())
