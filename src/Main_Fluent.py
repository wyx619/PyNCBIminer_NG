# *-* coding:utf-8 *-*
import sys

from pathlib import Path

from PySide6.QtCore import (
    Qt,
    Signal,
    QObject,
    QEventLoop,
    QTimer,
    Slot,
    QPropertyAnimation,
    QEasingCurve,
    QDate,
)
from PySide6.QtGui import QTextCursor, QIcon
from PySide6.QtWidgets import (
    QApplication,
    QFileDialog,
    QHBoxLayout,
    QVBoxLayout,
    QWidget,
    QStackedWidget,
)

try:
    from qframelesswindow.utils import getSystemAccentColor

    HAS_SYSTEM_ACCENT = True
except ImportError:
    HAS_SYSTEM_ACCENT = False

from qfluentwidgets import (
    FluentWindow,
    NavigationItemPosition,
    SubtitleLabel,
    PrimaryPushButton,
    PushButton,
    LineEdit,
    TextEdit,
    ComboBox,
    CheckBox,
    RadioButton,
    CardWidget,
    SwitchButton,
    BodyLabel,
    InfoBar,
    FluentIcon as FIF,
    SegmentedWidget,
    SettingCardGroup,
    ExpandSettingCard,
    PlainTextEdit,
    setTheme,
    Theme,
    InfoBarPosition,
    DatePicker,
    SingleDirectionScrollArea,
    setThemeColor,
    themeColor,
    ColorPickerButton,
)

from main_utils import BackendController
# --- Tools / Utils ---


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


# --- Custom UI Components ---


class LogWidget(CardWidget):
    """A dedicated widget for console output"""

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


# --- Interfaces (Pages) ---


class RetrievalInterface(SingleDirectionScrollArea):
    """Tab 1: Sequence Retrieval"""

    def __init__(self, main_window):
        super().__init__(parent=main_window)
        self.main_window = main_window
        self.date_from_cleared = True
        self.date_to_cleared = True

        self.view = QWidget(self)
        self.vBoxLayout = QVBoxLayout(self.view)
        self.vBoxLayout.setContentsMargins(30, 30, 30, 30)
        self.vBoxLayout.setSpacing(20)

        # 1. Working Directory Card
        self.wd_group = SettingCardGroup("Working Directory", self.view)
        self.wd_card = CardWidget(self.view)
        self.wd_card.setFixedHeight(60)
        wd_layout = QHBoxLayout(self.wd_card)
        wd_layout.setContentsMargins(15, 10, 15, 10)
        self.wd_edit = LineEdit(self.wd_card)
        self.wd_edit.setPlaceholderText("Absolute path of working directory")
        self.btn_wd_view = PushButton("Browse", self.wd_card)
        self.btn_wd_view.setIcon(FIF.FOLDER)
        wd_layout.addWidget(BodyLabel("Path:"))
        wd_layout.addWidget(self.wd_edit)
        wd_layout.addWidget(self.btn_wd_view)
        self.wd_group.addSettingCard(self.wd_card)
        self.vBoxLayout.addWidget(self.wd_group)

        # 2. Basic Settings
        self.basic_group = SettingCardGroup("Basic Settings", self.view)

        # 3. Taxonomy
        self.tax_card = CardWidget(self.view)
        self.tax_card.setFixedHeight(150)
        tax_layout = QVBoxLayout(self.tax_card)
        tax_layout.setContentsMargins(15, 10, 15, 15)
        tax_layout.addWidget(BodyLabel("Target Groups (Taxonomy):"))
        self.tax_edit = PlainTextEdit(self.tax_card)
        self.tax_edit.setPlaceholderText("One taxon per line")
        self.tax_edit.setFixedHeight(100)
        tax_layout.addWidget(self.tax_edit)
        self.basic_group.addSettingCard(self.tax_card)

        # 4. Target Region Selection
        self.region_card = CardWidget(self.view)
        self.region_card.setFixedHeight(80)
        reg_layout = QHBoxLayout(self.region_card)
        reg_layout.setContentsMargins(15, 10, 15, 10)
        self.combo_region = ComboBox(self.region_card)
        self.combo_region.setMaxVisibleItems(6)

        # Dynamically load all available markers from blast_parameters directory
        blast_params_dir = Path(get_writable_path("blast_parameters"))
        default_params_dir = Path(get_resource_path("blast_parameters"))

        marker_set = set()
        marker_set.add("")  # Add empty option

        # Load from custom directory
        if blast_params_dir.exists():
            for f in blast_params_dir.iterdir():
                if f.is_file() and f.suffix == ".txt":
                    marker_set.add(f.stem)

        # Load from default directory
        if default_params_dir.exists():
            for f in default_params_dir.iterdir():
                if f.is_file() and f.suffix == ".txt":
                    marker_set.add(f.stem)

        # Sort markers (empty first, then alphabetical)
        markers = sorted(marker_set, key=lambda x: (x != "", x))
        self.combo_region.addItems(markers)

        # New region input (only enabled when combo is empty)
        self.new_region_edit = LineEdit(self.region_card)
        self.new_region_edit.setPlaceholderText("Enter new region name")
        self.new_region_edit.setEnabled(False)
        self.new_region_edit.setFixedWidth(180)

        self.btn_set_region = PrimaryPushButton("Set Region", self.region_card)
        self.btn_save_settings = PushButton("Save Settings", self.region_card)
        reg_layout.addWidget(BodyLabel("Target Region:"))
        reg_layout.addWidget(self.combo_region)
        reg_layout.addWidget(self.new_region_edit)
        reg_layout.addWidget(self.btn_set_region)
        reg_layout.addWidget(self.btn_save_settings)
        self.basic_group.addSettingCard(self.region_card)

        # 5. Entrez & Dates
        self.entrez_card = CardWidget(self.view)
        self.entrez_card.setFixedHeight(230)
        ent_layout = QVBoxLayout(self.entrez_card)
        ent_layout.setContentsMargins(15, 10, 15, 10)

        row1 = QHBoxLayout()
        self.entrez_qualifier = PlainTextEdit(self.entrez_card)
        ent_layout.addWidget(BodyLabel("Entrez Qualifier:"))
        self.entrez_qualifier.setPlaceholderText(
            "Constraint on BLAST search (Entrez Qualifier)"
        )
        self.entrez_qualifier.setFixedHeight(100)
        row1.addWidget(self.entrez_qualifier)
        ent_layout.addLayout(row1)

        row2 = QHBoxLayout()
        self.email_edit = LineEdit(self.entrez_card)
        self.email_edit.setPlaceholderText("User's Email")
        row2.addWidget(BodyLabel("Email:"))
        row2.addWidget(self.email_edit)
        ent_layout.addLayout(row2)

        row3 = QHBoxLayout()
        self.date_from = DatePicker(self.entrez_card)
        self.date_from.setDate(QDate())
        self.date_from_cleared = True
        self.date_from.dateChanged.connect(self.on_date_from_changed)
        self.btn_clear_from = PushButton("Reset", self.entrez_card)


        self.btn_clear_from.clicked.connect(self.clear_date_from)
        row3.addWidget(BodyLabel("Date From:"))
        row3.addWidget(self.date_from)
        row3.addWidget(self.btn_clear_from)
        row3.addStretch()

        self.date_to = DatePicker(self.entrez_card)
        self.date_to.setDate(QDate())
        self.date_to_cleared = True
        self.date_to.dateChanged.connect(self.on_date_to_changed)
        self.btn_clear_to = PushButton("Reset", self.entrez_card)


        self.btn_clear_to.clicked.connect(self.clear_date_to)
        row3.addWidget(BodyLabel("Date To:"))
        row3.addWidget(self.date_to)
        row3.addWidget(self.btn_clear_to)
        ent_layout.addLayout(row3)

        self.basic_group.addSettingCard(self.entrez_card)

        # 6. Actions Row
        self.action_card = CardWidget(self.view)
        self.action_card.setFixedHeight(80)
        act_layout = QHBoxLayout(self.action_card)
        act_layout.setContentsMargins(15, 10, 15, 10)
        self.chk_summary = CheckBox("Summarize widely used marker", self.action_card)
        self.btn_esearch = PrimaryPushButton("Entrez Search", self.action_card)
        self.btn_esearch.setIcon(FIF.SEARCH)
        act_layout.addWidget(self.chk_summary)
        act_layout.addStretch(1)
        act_layout.addWidget(self.btn_esearch)
        self.basic_group.addSettingCard(self.action_card)

        self.vBoxLayout.addWidget(self.basic_group)

        # 7. Advanced Settings (Expandable)
        self.adv_group = ExpandSettingCard(
            FIF.SETTING, "Advanced BLAST Parameters", "Click to expand configuration"
        )
        self.adv_group.setExpand(True)
        self.adv_view = QWidget()
        adv_layout = QVBoxLayout(self.adv_view)

        # Initial Queries (Fasta) - Full width
        adv_layout.addWidget(BodyLabel("Initial Queries (Fasta):"))
        self.init_queries = PlainTextEdit()
        self.init_queries.setPlaceholderText("Paste sequences in fasta format here")
        self.init_queries.setFixedHeight(200)
        adv_layout.addWidget(self.init_queries)

        # Grid for params
        grid_layout = QHBoxLayout()
        col1 = QVBoxLayout()
        col2 = QVBoxLayout()

        # Left column: Key Annotations, Exclude Sources
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

        # Right column: Other parameters (evenly distributed)
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

        self.adv_group.viewLayout.addWidget(self.adv_view)
        self.vBoxLayout.addWidget(self.adv_group)

        # 4. Final Buttons
        self.btn_submit_blast = PrimaryPushButton("Submit New BLAST", self)
        self.btn_submit_blast.setIcon(FIF.PLAY)
        self.btn_load_job = PushButton("Load Previous Job", self)
        self.btn_load_job.setIcon(FIF.HISTORY)
        self.btn_stop = PushButton("Stop", self)
        self.btn_stop.setIcon(FIF.CLOSE)
        self.btn_stop.setEnabled(False)

        btn_row = QHBoxLayout()
        btn_row.addWidget(self.btn_submit_blast)
        btn_row.addWidget(self.btn_load_job)
        self.vBoxLayout.addLayout(btn_row)

        stop_row = QHBoxLayout()
        stop_row.addWidget(self.btn_stop)
        self.vBoxLayout.addLayout(stop_row)

        self.vBoxLayout.addStretch(1)

        # Set widget and properties after all components are added
        self.setWidget(self.view)
        self.setWidgetResizable(True)
        self.setObjectName("retrieval_interface")

        self.setStyleSheet("QScrollArea {border: none; background:transparent}")
        self.view.setStyleSheet("QWidget {background:transparent}")

        # Connect internal signals
        self.btn_wd_view.clicked.connect(self.select_wd)

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
    """Tab 2: Supermatrix Construction using SegmentedWidget for sub-steps"""

    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        self.setObjectName("construction_interface")

        self.vBoxLayout = QVBoxLayout(self)
        self.pivot = SegmentedWidget(self)
        self.stackedWidget = QStackedWidget(self)

        # -- Pages --
        self.page_filter = self.create_filtering_page()
        self.page_align = self.create_alignment_page()
        self.page_trim = self.create_trimming_page()
        self.page_concat = self.create_concat_page()

        # Add items to SegmentedWidget
        self.addSubInterface(self.page_filter, "filter", "Filtering")
        self.addSubInterface(self.page_align, "align", "Alignment")
        self.addSubInterface(self.page_trim, "trim", "Trimming")
        self.addSubInterface(self.page_concat, "concat", "Concatenation")

        self.vBoxLayout.addWidget(self.pivot)
        self.vBoxLayout.addWidget(self.stackedWidget)
        self.vBoxLayout.setContentsMargins(30, 25, 30, 15)

        # Init state
        self.stackedWidget.setCurrentWidget(self.page_filter)
        self.pivot.setCurrentItem("filter")
        self.pivot.currentItemChanged.connect(
            lambda k: self.stackedWidget.setCurrentWidget(self.findChild(QWidget, k))
        )

    def addSubInterface(self, widget: QWidget, objectName, text):
        widget.setObjectName(objectName)
        self.stackedWidget.addWidget(widget)
        self.pivot.addItem(routeKey=objectName, text=text)

    def create_filtering_page(self):
        w = QWidget()
        layout = QVBoxLayout(w)
        layout.setContentsMargins(5, 20, 5, 20)

        grp = SettingCardGroup("Sequence Filtering", w)

        # Options
        card_opts = CardWidget()
        card_opts.setFixedHeight(80)
        l_opts = QHBoxLayout(card_opts)
        l_opts.setContentsMargins(15, 10, 15, 10)
        self.switch_ext = SwitchButton(card_opts)
        self.switch_ext.setChecked(False)
        self.switch_reduce = SwitchButton(card_opts)
        self.switch_reduce.setChecked(False)

        l_opts.addWidget(BodyLabel("Extended segments refinement"))
        l_opts.addWidget(self.switch_ext)
        l_opts.addStretch()

        l_opts.addWidget(BodyLabel("Species-level sequence selection"))
        l_opts.addWidget(self.switch_reduce)

        grp.addSettingCard(card_opts)

        # Parameters
        card_params = CardWidget()
        card_params.setFixedHeight(60)
        l_params = QHBoxLayout(card_params)
        l_params.setContentsMargins(15, 10, 15, 10)
        self.len_thresh = LineEdit()
        self.len_thresh.setText("100")
        self.combo_consensus = ComboBox()
        self.combo_consensus.addItems(["True", "False"])
        l_params.addWidget(BodyLabel("Length Threshold:"))
        l_params.addWidget(self.len_thresh)
        l_params.addStretch()
        l_params.addWidget(BodyLabel("Abnormal Index (Consensus):"))
        l_params.addWidget(self.combo_consensus)
        grp.addSettingCard(card_params)

        # Paths
        card_paths = CardWidget()
        card_paths.setFixedHeight(180)
        l_paths = QVBoxLayout(card_paths)
        l_paths.setContentsMargins(15, 10, 15, 10)

        self.filter_in = LineEdit()
        self.filter_in.setPlaceholderText(
            "One working directory or the parent directory of multiple working directories"
        )
        btn_in = PushButton("Browse")
        btn_in.setIcon(FIF.FOLDER)
        btn_in.clicked.connect(lambda: self.browse_dir(self.filter_in))
        h1 = QHBoxLayout()
        h1.addWidget(BodyLabel("Input Path:"))
        h1.addWidget(self.filter_in)
        h1.addWidget(btn_in)

        self.filter_out = LineEdit()
        self.filter_out.setPlaceholderText("The same as input path by default")
        btn_out = PushButton("Browse")
        btn_out.setIcon(FIF.FOLDER)
        btn_out.clicked.connect(lambda: self.browse_dir(self.filter_out))
        h2 = QHBoxLayout()
        h2.addWidget(BodyLabel("Output Path:"))
        h2.addWidget(self.filter_out)
        h2.addWidget(btn_out)

        l_paths.addLayout(h1)
        l_paths.addLayout(h2)
        grp.addSettingCard(card_paths)

        self.btn_run_filter = PrimaryPushButton("Run Filtering")
        self.btn_run_filter.setIcon(FIF.PLAY)

        layout.addWidget(grp)
        layout.addWidget(self.btn_run_filter)
        return w

    def create_alignment_page(self):
        w = QWidget()
        layout = QVBoxLayout(w)
        layout.setContentsMargins(5, 20, 5, 20)

        grp = SettingCardGroup("Sequence Alignment (MAFFT)", w)

        # Mode and Paths
        card_paths = CardWidget()
        card_paths.setFixedHeight(180)
        l_paths = QVBoxLayout(card_paths)
        l_paths.setContentsMargins(15, 10, 15, 10)

        self.rb_align_single = RadioButton("Input one file")
        self.rb_align_multi = RadioButton("Input multiple files")
        self.rb_align_single.setChecked(True)
        row_rb = QHBoxLayout()
        row_rb.addWidget(self.rb_align_single)
        row_rb.addWidget(self.rb_align_multi)
        l_paths.addLayout(row_rb)

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
        l_paths.addLayout(h1)
        l_paths.addLayout(h2)
        grp.addSettingCard(card_paths)

        # Params
        card_param = CardWidget()
        card_param.setFixedHeight(80)
        l_param = QHBoxLayout(card_param)
        l_param.setContentsMargins(15, 10, 15, 10)
        self.align_thread = LineEdit()
        self.align_thread.setText("-1")
        self.align_algo = ComboBox()
        self.align_algo.addItems(
            [
                "auto(depends on datasize)",
                "add(use long sequences as backbone to align fragment sequences)",
            ]
        )
        self.align_reorder = ComboBox()
        self.align_reorder.addItems(["True", "False"])

        l_param.addWidget(BodyLabel("Threads:"))
        l_param.addWidget(self.align_thread)
        l_param.addWidget(BodyLabel("Strategy:"))
        l_param.addWidget(self.align_algo)
        l_param.addWidget(BodyLabel("Reorder:"))
        l_param.addWidget(self.align_reorder)
        grp.addSettingCard(card_param)

        self.btn_run_align = PrimaryPushButton("Run Alignment")
        self.btn_run_align.setIcon(FIF.PLAY)

        layout.addWidget(grp)
        layout.addWidget(self.btn_run_align)
        return w

    def create_trimming_page(self):
        w = QWidget()
        layout = QVBoxLayout(w)
        layout.setContentsMargins(5, 20, 5, 20)

        grp = SettingCardGroup("Alignment Trimming (trimAl)", w)

        # Input/Output
        card_io = CardWidget()
        card_io.setFixedHeight(180)
        l_io = QVBoxLayout(card_io)
        l_io.setContentsMargins(15, 10, 15, 10)
        self.rb_trim_single = RadioButton("Input one file")
        self.rb_trim_multi = RadioButton("Input multiple files")
        self.rb_trim_single.setChecked(True)
        row_rb = QHBoxLayout()
        row_rb.addWidget(self.rb_trim_single)
        row_rb.addWidget(self.rb_trim_multi)
        l_io.addLayout(row_rb)

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
        l_io.addLayout(h1)
        l_io.addLayout(h2)
        grp.addSettingCard(card_io)

        # Methods
        card_met = CardWidget()
        card_met.setFixedHeight(220)
        l_met = QVBoxLayout(card_met)
        l_met.setContentsMargins(15, 10, 15, 10)
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
        l_met.addWidget(BodyLabel("Trimming Method:"))
        l_met.addWidget(self.combo_trim_method)

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
        l_met.addLayout(grid)
        grp.addSettingCard(card_met)

        self.btn_run_trim = PrimaryPushButton("Run Trimming")
        self.btn_run_trim.setIcon(FIF.PLAY)

        layout.addWidget(grp)
        layout.addWidget(self.btn_run_trim)
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
        return w

    def browse_dir(self, line_edit):
        path = QFileDialog.getExistingDirectory(self, "Select Directory")
        if path:
            line_edit.setText(path)

    def on_date_changed(self, date, date_type):
        pass

    def browse_file_or_dir(self, line_edit, is_single):
        if is_single:
            path, _ = QFileDialog.getOpenFileName(self, "Select File")
        else:
            path = QFileDialog.getExistingDirectory(self, "Select Directory")
        if path:
            line_edit.setText(path)


class ChloroplastMinerInterface(QWidget):
    """Chloroplast Miner Page"""

    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        self.setObjectName("chloroplast_miner_interface")

        self.vBoxLayout = QVBoxLayout(self)
        self.pivot = SegmentedWidget(self)
        self.stackedWidget = QStackedWidget(self)

        # -- Pages --
        self.page_search = self.create_search_page()
        self.page_extract = self.create_extract_page()
        self.page_cds = self.create_cds_page()
        self.page_align = self.create_chloroplast_align_page()

        # Add items to SegmentedWidget
        self.addSubInterface(self.page_search, "search", "Search && Download")
        self.addSubInterface(self.page_extract, "extract", "Extract Info && Quality Control")
        self.addSubInterface(self.page_cds, "cds", "Get && Filter CDS")
        self.addSubInterface(self.page_align, "chloroplast_align", "Align && Trim")

        self.vBoxLayout.addWidget(self.pivot)
        self.vBoxLayout.addWidget(self.stackedWidget)
        self.vBoxLayout.setContentsMargins(30, 25, 30, 15)

        # Init state
        self.stackedWidget.setCurrentWidget(self.page_search)
        self.pivot.setCurrentItem("search")
        self.pivot.currentItemChanged.connect(self.on_chloroplast_page_changed)

    def on_chloroplast_page_changed(self, key):
        self.stackedWidget.setCurrentWidget(self.findChild(QWidget, key))
        if key == "extract":
            self.update_qc_input_default()

    def update_qc_input_default(self):
        if hasattr(self, 'chloro_qc_in') and hasattr(self, 'chloro_download_dir_edit'):
            download_dir = self.chloro_download_dir_edit.text().strip()
            if download_dir and not self.chloro_qc_in.text().strip():
                self.chloro_qc_in.setText(download_dir)

    def addSubInterface(self, widget: QWidget, objectName, text):
        widget.setObjectName(objectName)
        self.stackedWidget.addWidget(widget)
        self.pivot.addItem(routeKey=objectName, text=text)

    def create_search_page(self):
        w = QWidget()
        layout = QVBoxLayout(w)
        layout.setContentsMargins(5, 20, 5, 20)

        grp = SettingCardGroup("Search & Download", w)

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

        grp.addSettingCard(card)

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
        btn_chloro_download_dir.clicked.connect(lambda: self.browse_folder(self.chloro_download_dir_edit))

        h_box2 = QHBoxLayout()
        h_box2.addWidget(BodyLabel("Download Directory:"))
        h_box2.addWidget(self.chloro_download_dir_edit)
        h_box2.addWidget(btn_chloro_download_dir)

        self.chloro_email_edit = LineEdit()
        self.chloro_email_edit.setPlaceholderText("Email (required for NCBI)")

        h_box3 = QHBoxLayout()
        h_box3.addWidget(BodyLabel("Email:"))
        h_box3.addWidget(self.chloro_email_edit)

        download_layout.addWidget(BodyLabel("Download Prepare:"))
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

        grp.addSettingCard(card_download)

        layout.addWidget(grp)
        return w

    def create_extract_page(self):
        w = QWidget()
        layout = QVBoxLayout(w)
        layout.setContentsMargins(5, 20, 5, 20)

        grp = SettingCardGroup("Extract Info & Quality Control", w)

        card = CardWidget()
        card.setFixedHeight(280)
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(15, 10, 15, 10)

        h_input = QHBoxLayout()
        self.chloro_qc_in = LineEdit()
        self.chloro_qc_in.setPlaceholderText("Input directory containing GenBank files")
        btn_chloro_qc_in = PushButton("Browse")
        btn_chloro_qc_in.setIcon(FIF.FOLDER)
        btn_chloro_qc_in.clicked.connect(lambda: self.browse_folder(self.chloro_qc_in))
        h_input.addWidget(BodyLabel("Input Directory:"))
        h_input.addWidget(self.chloro_qc_in)
        h_input.addWidget(btn_chloro_qc_in)
        card_layout.addLayout(h_input)

        h_output = QHBoxLayout()
        self.chloro_qc_out = LineEdit()
        self.chloro_qc_out.setPlaceholderText("Output directory for problematic genome FASTA files")
        btn_chloro_qc_out = PushButton("Browse")
        btn_chloro_qc_out.setIcon(FIF.FOLDER)
        btn_chloro_qc_out.clicked.connect(lambda: self.browse_folder(self.chloro_qc_out))
        h_output.addWidget(BodyLabel("Output Directory:"))
        h_output.addWidget(self.chloro_qc_out)
        h_output.addWidget(btn_chloro_qc_out)
        card_layout.addLayout(h_output)

        self.chloro_cds_thresh = LineEdit()
        self.chloro_cds_thresh.setText("80")
        self.chloro_ambig_thresh = LineEdit()
        self.chloro_ambig_thresh.setText("0.2")

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
        layout.addStretch(1)
        return w

    def create_cds_page(self):
        w = QWidget()
        layout = QVBoxLayout(w)
        layout.setContentsMargins(5, 20, 5, 20)

        grp = SettingCardGroup("Get CDS", w)

        card = CardWidget()
        card.setFixedHeight(120)
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(15, 10, 15, 10)

        self.chloro_cds_in = LineEdit()
        self.chloro_cds_in.setPlaceholderText("Input directory containing filtered GenBank files")
        btn_chloro_cds_in = PushButton("Browse")
        btn_chloro_cds_in.setIcon(FIF.FOLDER)
        btn_chloro_cds_in.clicked.connect(lambda: self.browse_dir(self.chloro_cds_in))

        card_layout.addWidget(BodyLabel("Input Directory:"))
        card_layout.addWidget(self.chloro_cds_in)
        card_layout.addWidget(btn_chloro_cds_in)

        grp.addSettingCard(card)

        card_output = CardWidget()
        card_output.setFixedHeight(120)
        output_layout = QVBoxLayout(card_output)
        output_layout.setContentsMargins(15, 10, 15, 10)

        self.chloro_cds_out = LineEdit()
        self.chloro_cds_out.setPlaceholderText("Output directory for CDS files")
        btn_chloro_cds_out = PushButton("Browse")
        btn_chloro_cds_out.setIcon(FIF.FOLDER)
        btn_chloro_cds_out.clicked.connect(lambda: self.browse_dir(self.chloro_cds_out))

        output_layout.addWidget(BodyLabel("Output Directory:"))
        output_layout.addWidget(self.chloro_cds_out)
        output_layout.addWidget(btn_chloro_cds_out)

        grp.addSettingCard(card_output)

        self.btn_chloro_cds = PrimaryPushButton("Extract CDS")
        self.btn_chloro_cds.setIcon(FIF.CODE)

        layout.addWidget(grp)
        layout.addWidget(self.btn_chloro_cds)
        return w

    def create_chloroplast_align_page(self):
        w = QWidget()
        layout = QVBoxLayout(w)
        layout.setContentsMargins(5, 20, 5, 20)

        grp = SettingCardGroup("Align & Trim", w)

        card = CardWidget()
        card.setFixedHeight(240)
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(15, 10, 15, 10)

        self.chloro_align_in = LineEdit()
        self.chloro_align_in.setPlaceholderText("Input directory containing CDS files")
        btn_chloro_align_in = PushButton("Browse")
        btn_chloro_align_in.setIcon(FIF.FOLDER)
        btn_chloro_align_in.clicked.connect(lambda: self.browse_dir(self.chloro_align_in))

        self.chloro_align_out = LineEdit()
        self.chloro_align_out.setPlaceholderText("Output directory for aligned files")
        btn_chloro_align_out = PushButton("Browse")
        btn_chloro_align_out.setIcon(FIF.FOLDER)
        btn_chloro_align_out.clicked.connect(lambda: self.browse_dir(self.chloro_align_out))

        card_layout.addWidget(BodyLabel("Input Directory:"))
        card_layout.addWidget(self.chloro_align_in)
        card_layout.addWidget(btn_chloro_align_in)
        card_layout.addWidget(BodyLabel("Output Directory:"))
        card_layout.addWidget(self.chloro_align_out)
        card_layout.addWidget(btn_chloro_align_out)

        grp.addSettingCard(card)

        card_trim = CardWidget()
        card_trim.setFixedHeight(80)
        trim_layout = QHBoxLayout(card_trim)
        trim_layout.setContentsMargins(15, 10, 15, 10)

        self.chloro_trim_method = ComboBox()
        self.chloro_trim_method.addItems([
            "automated1",
            "gappyout",
            "strict",
            "strictplus"
        ])

        trim_layout.addWidget(BodyLabel("Trimming Method:"))
        trim_layout.addWidget(self.chloro_trim_method)

        grp.addSettingCard(card_trim)

        self.btn_chloro_align = PrimaryPushButton("Align & Trim")
        self.btn_chloro_align.setIcon(FIF.PLAY)

        layout.addWidget(grp)
        layout.addWidget(self.btn_chloro_align)
        return w

    def browse_file(self, line_edit):
        path, _ = QFileDialog.getOpenFileName(self, "Select File")
        if path:
            line_edit.setText(path)

    def browse_folder(self, line_edit):
        path = QFileDialog.getExistingDirectory(self, "Select Directory")
        if path:
            line_edit.setText(path)

    def on_chloro_download(self):
        if not self.chloro_wd_edit.text().strip() or not self.chloro_download_dir_edit.text().strip() or not self.chloro_email_edit.text().strip():
            self.main_window.backend.emit_log("Please select index file, download directory and enter email", "WARNING")
            return

        email = self.chloro_email_edit.text().strip()
        in_path = self.chloro_wd_edit.text().strip()
        out_path = self.chloro_download_dir_edit.text().strip()

        self.main_window.backend.download_chloroplast_genomes(email, in_path, out_path)

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
            self.main_window.backend.emit_log("Please enter at least one taxon name", "WARNING")
            return

        date_from_obj = self.chloro_date_from.date
        date_to_obj = self.chloro_date_to.date

        has_from = not self.chloro_date_from_cleared and date_from_obj.isValid()
        has_to = not self.chloro_date_to_cleared and date_to_obj.isValid()

        if has_from and not has_to:
            self.chloro_date_to.setDate(QDate.currentDate())
            self.main_window.backend.emit_log("Date To not set, automatically set to today", "INFO")
        elif not has_from and has_to:
            self.main_window.backend.emit_log("Please select both Date From and Date To, or leave both empty", "WARNING")
            return

        from urllib.parse import quote
        from PySide6.QtGui import QDesktopServices
        from PySide6.QtCore import QUrl

        taxa = [line.strip() for line in text.split('\n') if line.strip()]

        if len(taxa) == 1:
            taxa_query = f'"{taxa[0]}"[Organism]'
        else:
            taxa_queries = " OR ".join([f'"{t}"[Organism]' for t in taxa])
            taxa_query = f"({taxa_queries})"

        query = f'{taxa_query} AND (plastid[All Fields] OR chloroplast[All Fields]) AND (100000[Sequence Length] : 300000[Sequence Length]) NOT mitochondrion[Title] NOT mitochondrial[Title] NOT chromosome[Title]'

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

        encoded_query = quote(query, safe='()')
        url = f"https://www.ncbi.nlm.nih.gov/nuccore/?term={encoded_query}"

        QDesktopServices.openUrl(QUrl(url))

    def on_chloro_qc_extract(self):
        in_folder = self.chloro_qc_in.text().strip()
        out_folder = self.chloro_qc_out.text().strip()

        if not in_folder or not out_folder:
            self.main_window.backend.emit_log("Please select both input and output directories", "WARNING")
            return

        cds_threshold = 80
        try:
            cds_threshold = int(self.chloro_cds_thresh.text().strip())
            if cds_threshold < 0:
                self.main_window.backend.emit_log("CDS threshold must be a positive integer", "WARNING")
                return
        except ValueError:
            self.main_window.backend.emit_log("Invalid CDS threshold value", "WARNING")
            return

        ambig_threshold = 0.2
        try:
            ambig_threshold = float(self.chloro_ambig_thresh.text().strip())
            if ambig_threshold < 0 or ambig_threshold > 1:
                self.main_window.backend.emit_log("Ambiguity threshold must be between 0 and 1", "WARNING")
                return
        except ValueError:
            self.main_window.backend.emit_log("Invalid ambiguity threshold value", "WARNING")
            return

        self.main_window.backend.emit_log("Quality control started...", "INFO")
        self.main_window.backend.quality_control(in_folder, out_folder, cds_threshold, ambig_threshold)


class DependenciesInterface(QWidget):
    """Dependencies Page"""

    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        self.setObjectName("dependencies_interface")
        self.vBoxLayout = QVBoxLayout(self)
        self.vBoxLayout.setContentsMargins(30, 30, 30, 30)
        self.vBoxLayout.setSpacing(20)

        # Dependencies Group
        grp = SettingCardGroup("Dependencies", self)

        # Install MAFFT
        card_mafft = CardWidget()
        card_mafft.setFixedHeight(80)
        h1 = QHBoxLayout(card_mafft)
        h1.setContentsMargins(15, 10, 15, 10)
        h1.addWidget(BodyLabel("Install MAFFT dependency"))
        btn_mafft = PushButton("Install", card_mafft)
        btn_mafft.clicked.connect(main_window.run_install_mafft)
        h1.addWidget(btn_mafft)
        grp.addSettingCard(card_mafft)

        # Install TrimAl
        card_trim = CardWidget()
        card_trim.setFixedHeight(80)
        h2 = QHBoxLayout(card_trim)
        h2.setContentsMargins(15, 10, 15, 10)
        h2.addWidget(BodyLabel("Install trimAl dependency"))
        btn_trim = PushButton("Install", card_trim)
        btn_trim.clicked.connect(main_window.run_install_trimal)
        h2.addWidget(btn_trim)
        grp.addSettingCard(card_trim)

        # Install PGA
        card_pga = CardWidget()
        card_pga.setFixedHeight(80)
        h3 = QHBoxLayout(card_pga)
        h3.setContentsMargins(15, 10, 15, 10)
        h3.addWidget(BodyLabel("Install PGA dependency"))
        btn_pga = PushButton("Install", card_pga)
        btn_pga.clicked.connect(main_window.run_install_pga)
        h3.addWidget(btn_pga)
        grp.addSettingCard(card_pga)

        self.vBoxLayout.addWidget(grp)

        # Theme Group
        theme_grp = SettingCardGroup("Theme Settings", self)

        card_theme = CardWidget()
        card_theme.setFixedHeight(80)
        h3 = QHBoxLayout(card_theme)
        h3.setContentsMargins(15, 10, 15, 10)
        h3.addWidget(BodyLabel("Application Theme"))
        self.combo_theme = ComboBox(card_theme)
        self.combo_theme.addItems(["Light", "Dark", "Auto"])
        self.combo_theme.setCurrentIndex(2)
        self.combo_theme.currentIndexChanged.connect(main_window.change_theme)
        h3.addWidget(self.combo_theme)
        theme_grp.addSettingCard(card_theme)

        # Theme Color Card
        card_color = CardWidget()
        card_color.setFixedHeight(80)
        h4 = QHBoxLayout(card_color)
        h4.setContentsMargins(15, 10, 15, 10)
        h4.addWidget(BodyLabel("Theme Color"))
        self.color_picker = ColorPickerButton(
            parent=card_color, title="Color", color=themeColor()
        )
        self.color_picker.colorChanged.connect(lambda c: setThemeColor(c, save=True))
        h4.addWidget(self.color_picker)

        theme_grp.addSettingCard(card_color)

        self.vBoxLayout.addWidget(theme_grp)
        self.vBoxLayout.addStretch()


class AboutInterface(QWidget):
    """About Page"""

    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        self.setObjectName("about_interface")
        self.vBoxLayout = QVBoxLayout(self)
        self.vBoxLayout.setContentsMargins(30, 30, 30, 30)
        self.vBoxLayout.setSpacing(20)

        # About Group
        grp = SettingCardGroup("About", self)

        # About Card
        card_about = CardWidget()
        card_about.setFixedHeight(100)
        h3 = QHBoxLayout(card_about)
        h3.setContentsMargins(15, 10, 15, 10)

        h3.addWidget(BodyLabel("About PyNCBIminer-NG"))
        btn_about = PushButton("Show Info", card_about)
        btn_about.clicked.connect(main_window.show_about)
        h3.addWidget(btn_about)
        grp.addSettingCard(card_about)

        self.vBoxLayout.addWidget(grp)
        self.vBoxLayout.addStretch()


# --- Main Window ---
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

        # Set minimum window width
        self.setMinimumWidth(1100)

        # Set window size and center on screen
        self.resize(1100, 750)
        screen = QApplication.primaryScreen()
        screen_geometry = screen.availableGeometry()
        x = (screen_geometry.width() - self.width()) // 2
        y = (screen_geometry.height() - self.height()) // 2
        self.move(x, y)

        # Sync with system theme color (Windows and macOS only)
        if HAS_SYSTEM_ACCENT and sys.platform in ["win32", "darwin"]:
            setThemeColor(getSystemAccentColor(), save=False)

        # Initialize Backend Controller
        self.backend = BackendController()
        self.backend.log_signal.connect(self.outputWritten)
        self.backend.infobar_signal.connect(self.show_infobar)
        self.backend.count_signal.connect(self.handle_count)

        # Define Interfaces
        self.retrieval_interface = RetrievalInterface(self)
        self.construction_interface = ConstructionInterface(self)
        self.chloroplast_miner_interface = ChloroplastMinerInterface(self)
        self.dependencies_interface = DependenciesInterface(self)
        self.about_interface = AboutInterface(self)

        # Add Interfaces to Navigation
        self.addSubInterface(self.retrieval_interface, FIF.SEARCH, "Sequence Retrieval")
        self.addSubInterface(
            self.construction_interface, FIF.APPLICATION, "Supermatrix Construction"
        )
        self.addSubInterface(
            self.chloroplast_miner_interface, FIF.LEAF, "Chloroplast Miner"
        )
        self.addSubInterface(self.dependencies_interface, FIF.SETTING, "Dependencies")
        self.addSubInterface(
            self.about_interface, FIF.INFO, "About", NavigationItemPosition.BOTTOM
        )

        # Global Log Widget (Bottom Dock area approximation)
        # In FluentWindow, the central widget stack takes all space.
        # We can insert the LogWidget into the main layout of FluentWindow
        # but FluentWindow logic is complex.
        # Easier strategy: Pass the log widget to the interfaces or
        # create a custom central widget wrapper.
        # Here, I will add the Log Widget to the BOTTOM of the Retrieval and Construction interfaces
        # or separate it.
        # Let's add it as a separate "Console" Tab for simplicity and cleanliness,
        # or implement a splitter.
        # *Decision*: I will use a custom layout. I will add the LogWidget to the stack
        # but output is global. I will actually make a 'Console' page.

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

        # Redirect stdout/stderr
        sys.stdout = EmittingStr()
        sys.stdout.textWritten.connect(self.outputWritten)
        sys.stderr = EmittingStr()
        sys.stderr.textWritten.connect(self.outputWritten)

        # --- Connections (Logic Mapping) ---
        self.connect_logic()

        # Check tools
        QTimer.singleShot(100, self.check_dependencies)
        self.mafft_checked = False
        self.trimal_checked = False

        # Fade in effect
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
        # Retrieval
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

        # Construction
        ci = self.construction_interface
        ci.switch_reduce.checkedChanged.connect(self.set_reduce_threshold)
        ci.combo_trim_method.currentIndexChanged.connect(self.select_tri_method)

        ci.btn_run_filter.clicked.connect(self.run_filtering)

        ci.btn_run_align.clicked.connect(self.run_alignment)
        ci.btn_run_trim.clicked.connect(self.run_trimming)
        ci.btn_run_concat.clicked.connect(self.run_concatenation)

        # Initial UI State
        ri.btn_set_region.setEnabled(False)
        ri.new_region_edit.setEnabled(True)  # Initially enabled since combo is empty
        self.set_marker_summary(0)  # Init state
        self.set_reduce_threshold(0)  # Init state
        self.select_tri_method()

    # --- Logic Methods (Adapted from original) ---

    def on_region_combo_changed(self):
        ri = self.retrieval_interface
        target_region = ri.combo_region.currentText()
        # Enable new_region_edit only when combo box is empty
        ri.new_region_edit.setEnabled(target_region == "")
        if target_region != "":
            ri.new_region_edit.clear()

    def on_new_region_changed(self):
        ri = self.retrieval_interface
        # When typing in new_region_edit, clear combo box selection
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
        # Use new_region_edit if it has text, otherwise use combo box
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
                        f"Line {i} invalid format: {parameter[:20]}...",
                        "WARNING"
                    )

        ri.init_queries.clear()
        # Load Queries Logic
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

        # Set UI elements
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
        self.backend.set_reduce_threshold(self.construction_interface, state)

    def select_tri_method(self):
        self.backend.select_tri_method(self.construction_interface)

    def run_filtering(self):
        self.backend.run_filtering(self.construction_interface)

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

    def check_dependencies(self):
        self.backend.check_dependencies()


if __name__ == "__main__":
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )
    app = QApplication(sys.argv)
    # 设置全局字体

    app.setApplicationName("PyNCBIminer-NG")
    app.setOrganizationName("Sichuan University")
    app.setApplicationDisplayName("PyNCBIminer-NG")
    setTheme(Theme.AUTO)

    w = MainWindow()
    w.show()
    sys.exit(app.exec())
