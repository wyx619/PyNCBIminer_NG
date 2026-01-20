# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'PyNCBIminer_main10.ui'
##
## Created by: Qt User Interface Compiler version 5.15.2
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from PySide6.QtCore import QCoreApplication, QMetaObject, QRect
from PySide6.QtGui import QAction
from PySide6.QtWidgets import (
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QFormLayout,
    QTabWidget,
    QGroupBox,
    QLabel,
    QLineEdit,
    QPlainTextEdit,
    QComboBox,
    QPushButton,
    QCheckBox,
    QRadioButton,
    QButtonGroup,
    QSpacerItem,
    QSizePolicy,
    QMenuBar,
    QMenu,
    QStatusBar,
    QLayout,
)


class Ui_MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setupUi(self)

    def setupUi(self, MainWindow):
        if not MainWindow.objectName():
            MainWindow.setObjectName("MainWindow")
        MainWindow.resize(2499, 1284)
        self.actionChange_font = QAction(MainWindow)
        self.actionChange_font.setObjectName("actionChange_font")
        self.actionInstall_MAFFT = QAction(MainWindow)
        self.actionInstall_MAFFT.setObjectName("actionInstall_MAFFT")
        self.actionInstall_trimAl = QAction(MainWindow)
        self.actionInstall_trimAl.setObjectName("actionInstall_trimAl")
        self.actionAbout = QAction(MainWindow)
        self.actionAbout.setObjectName("actionAbout")
        self.actionExit = QAction(MainWindow)
        self.actionExit.setObjectName("actionExit")
        self.centralwidget = QWidget(MainWindow)
        self.centralwidget.setObjectName("centralwidget")
        self.horizontalLayout = QHBoxLayout(self.centralwidget)
        self.horizontalLayout.setSpacing(6)
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.horizontalLayout.setSizeConstraint(QHBoxLayout.SetDefaultConstraint)
        self.horizontalLayout.setContentsMargins(9, 9, 9, 9)
        self.tabWidget = QTabWidget(self.centralwidget)
        self.tabWidget.setObjectName("tabWidget")
        sizePolicy = QSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(1)
        sizePolicy.setVerticalStretch(1)
        sizePolicy.setHeightForWidth(self.tabWidget.sizePolicy().hasHeightForWidth())
        self.tabWidget.setSizePolicy(sizePolicy)
        self.tab = QWidget()
        self.tab.setObjectName("tab")
        self.verticalLayout_10 = QVBoxLayout(self.tab)
        self.verticalLayout_10.setObjectName("verticalLayout_10")
        self.groupBox_7 = QGroupBox(self.tab)
        self.groupBox_7.setObjectName("groupBox_7")
        self.verticalLayout = QVBoxLayout(self.groupBox_7)
        self.verticalLayout.setObjectName("verticalLayout")
        self.horizontalLayout_5 = QHBoxLayout()
        self.horizontalLayout_5.setObjectName("horizontalLayout_5")
        self.label_32 = QLabel(self.groupBox_7)
        self.label_32.setObjectName("label_32")

        self.horizontalLayout_5.addWidget(self.label_32)

        self.wd = QLineEdit(self.groupBox_7)
        self.wd.setObjectName("wd")

        self.horizontalLayout_5.addWidget(self.wd)

        self.view = QPushButton(self.groupBox_7)
        self.view.setObjectName("view")

        self.horizontalLayout_5.addWidget(self.view)

        self.verticalLayout.addLayout(self.horizontalLayout_5)

        self.verticalLayout_10.addWidget(self.groupBox_7)

        self.horizontalLayout_23 = QHBoxLayout()
        self.horizontalLayout_23.setObjectName("horizontalLayout_23")
        self.groupBox_8 = QGroupBox(self.tab)
        self.groupBox_8.setObjectName("groupBox_8")
        sizePolicy1 = QSizePolicy(QSizePolicy.Preferred, QSizePolicy.Minimum)
        sizePolicy1.setHorizontalStretch(0)
        sizePolicy1.setVerticalStretch(0)
        sizePolicy1.setHeightForWidth(self.groupBox_8.sizePolicy().hasHeightForWidth())
        self.groupBox_8.setSizePolicy(sizePolicy1)
        self.verticalLayout_2 = QVBoxLayout(self.groupBox_8)
        self.verticalLayout_2.setObjectName("verticalLayout_2")
        self.label_24 = QLabel(self.groupBox_8)
        self.label_24.setObjectName("label_24")

        self.verticalLayout_2.addWidget(self.label_24)

        self.taxonomy = QPlainTextEdit(self.groupBox_8)
        self.taxonomy.setObjectName("taxonomy")
        sizePolicy2 = QSizePolicy(QSizePolicy.Preferred, QSizePolicy.Expanding)
        sizePolicy2.setHorizontalStretch(0)
        sizePolicy2.setVerticalStretch(0)
        sizePolicy2.setHeightForWidth(self.taxonomy.sizePolicy().hasHeightForWidth())
        self.taxonomy.setSizePolicy(sizePolicy2)

        self.verticalLayout_2.addWidget(self.taxonomy)

        self.horizontalLayout_4 = QHBoxLayout()
        self.horizontalLayout_4.setObjectName("horizontalLayout_4")
        self.label_4 = QLabel(self.groupBox_8)
        self.label_4.setObjectName("label_4")

        self.horizontalLayout_4.addWidget(self.label_4)

        self.target_region = QComboBox(self.groupBox_8)
        self.target_region.addItem("")
        self.target_region.addItem("")
        self.target_region.addItem("")
        self.target_region.addItem("")
        self.target_region.addItem("")
        self.target_region.addItem("")
        self.target_region.addItem("")
        self.target_region.addItem("")
        self.target_region.setObjectName("target_region")
        self.target_region.setEditable(True)
        self.target_region.setMaxVisibleItems(5)
        self.target_region.setMaxCount(2147483645)

        self.horizontalLayout_4.addWidget(self.target_region)

        self.verticalLayout_2.addLayout(self.horizontalLayout_4)

        self.horizontalLayout_2 = QHBoxLayout()
        self.horizontalLayout_2.setObjectName("horizontalLayout_2")
        self.set_target_region = QPushButton(self.groupBox_8)
        self.set_target_region.setObjectName("set_target_region")

        self.horizontalLayout_2.addWidget(self.set_target_region)

        self.save_settings = QPushButton(self.groupBox_8)
        self.save_settings.setObjectName("save_settings")

        self.horizontalLayout_2.addWidget(self.save_settings)

        self.verticalLayout_2.addLayout(self.horizontalLayout_2)

        self.label_25 = QLabel(self.groupBox_8)
        self.label_25.setObjectName("label_25")

        self.verticalLayout_2.addWidget(self.label_25)

        self.entrez_qualifier = QPlainTextEdit(self.groupBox_8)
        self.entrez_qualifier.setObjectName("entrez_qualifier")

        self.verticalLayout_2.addWidget(self.entrez_qualifier)

        self.horizontalLayout_33 = QHBoxLayout()
        self.horizontalLayout_33.setObjectName("horizontalLayout_33")
        self.label_31 = QLabel(self.groupBox_8)
        self.label_31.setObjectName("label_31")

        self.horizontalLayout_33.addWidget(self.label_31)

        self.horizontalLayout_11 = QHBoxLayout()
        self.horizontalLayout_11.setObjectName("horizontalLayout_11")
        self.label_43 = QLabel(self.groupBox_8)
        self.label_43.setObjectName("label_43")

        self.horizontalLayout_11.addWidget(self.label_43)

        self.date_from = QLineEdit(self.groupBox_8)
        self.date_from.setObjectName("date_from")

        self.horizontalLayout_11.addWidget(self.date_from)

        self.label_42 = QLabel(self.groupBox_8)
        self.label_42.setObjectName("label_42")

        self.horizontalLayout_11.addWidget(self.label_42)

        self.date_to = QLineEdit(self.groupBox_8)
        self.date_to.setObjectName("date_to")

        self.horizontalLayout_11.addWidget(self.date_to)

        self.horizontalLayout_33.addLayout(self.horizontalLayout_11)

        self.verticalLayout_2.addLayout(self.horizontalLayout_33)

        self.horizontalLayout_10 = QHBoxLayout()
        self.horizontalLayout_10.setObjectName("horizontalLayout_10")
        self.label_27 = QLabel(self.groupBox_8)
        self.label_27.setObjectName("label_27")

        self.horizontalLayout_10.addWidget(self.label_27)

        self.entrez_email = QLineEdit(self.groupBox_8)
        self.entrez_email.setObjectName("entrez_email")

        self.horizontalLayout_10.addWidget(self.entrez_email)

        self.verticalLayout_2.addLayout(self.horizontalLayout_10)

        self.horizontalLayout_32 = QHBoxLayout()
        self.horizontalLayout_32.setObjectName("horizontalLayout_32")
        self.marker_summary = QCheckBox(self.groupBox_8)
        self.marker_summary.setObjectName("marker_summary")

        self.horizontalLayout_32.addWidget(self.marker_summary)

        self.esearch = QPushButton(self.groupBox_8)
        self.esearch.setObjectName("esearch")

        self.horizontalLayout_32.addWidget(self.esearch)

        self.verticalLayout_2.addLayout(self.horizontalLayout_32)

        self.horizontalLayout_23.addWidget(self.groupBox_8)

        self.groupBox_5 = QGroupBox(self.tab)
        self.groupBox_5.setObjectName("groupBox_5")
        sizePolicy2.setHeightForWidth(self.groupBox_5.sizePolicy().hasHeightForWidth())
        self.groupBox_5.setSizePolicy(sizePolicy2)
        self.verticalLayout_3 = QVBoxLayout(self.groupBox_5)
        self.verticalLayout_3.setObjectName("verticalLayout_3")
        self.formLayout_5 = QFormLayout()
        self.formLayout_5.setObjectName("formLayout_5")
        self.label_33 = QLabel(self.groupBox_5)
        self.label_33.setObjectName("label_33")

        self.formLayout_5.setWidget(0, QFormLayout.LabelRole, self.label_33)

        self.initial_queries = QPlainTextEdit(self.groupBox_5)
        self.initial_queries.setObjectName("initial_queries")

        self.formLayout_5.setWidget(0, QFormLayout.FieldRole, self.initial_queries)

        self.label_30 = QLabel(self.groupBox_5)
        self.label_30.setObjectName("label_30")

        self.formLayout_5.setWidget(1, QFormLayout.LabelRole, self.label_30)

        self.key_annotations = QLineEdit(self.groupBox_5)
        self.key_annotations.setObjectName("key_annotations")

        self.formLayout_5.setWidget(1, QFormLayout.FieldRole, self.key_annotations)

        self.label_29 = QLabel(self.groupBox_5)
        self.label_29.setObjectName("label_29")

        self.formLayout_5.setWidget(2, QFormLayout.LabelRole, self.label_29)

        self.exclude_sources = QPlainTextEdit(self.groupBox_5)
        self.exclude_sources.setObjectName("exclude_sources")

        self.formLayout_5.setWidget(2, QFormLayout.FieldRole, self.exclude_sources)

        self.label_18 = QLabel(self.groupBox_5)
        self.label_18.setObjectName("label_18")

        self.formLayout_5.setWidget(3, QFormLayout.LabelRole, self.label_18)

        self.max_length = QLineEdit(self.groupBox_5)
        self.max_length.setObjectName("max_length")

        self.formLayout_5.setWidget(3, QFormLayout.FieldRole, self.max_length)

        self.label_7 = QLabel(self.groupBox_5)
        self.label_7.setObjectName("label_7")

        self.formLayout_5.setWidget(6, QFormLayout.LabelRole, self.label_7)

        self.expect_value = QLineEdit(self.groupBox_5)
        self.expect_value.setObjectName("expect_value")

        self.formLayout_5.setWidget(6, QFormLayout.FieldRole, self.expect_value)

        self.label_15 = QLabel(self.groupBox_5)
        self.label_15.setObjectName("label_15")

        self.formLayout_5.setWidget(7, QFormLayout.LabelRole, self.label_15)

        self.word_size = QLineEdit(self.groupBox_5)
        self.word_size.setObjectName("word_size")

        self.formLayout_5.setWidget(7, QFormLayout.FieldRole, self.word_size)

        self.label_21 = QLabel(self.groupBox_5)
        self.label_21.setObjectName("label_21")

        self.formLayout_5.setWidget(8, QFormLayout.LabelRole, self.label_21)

        self.gap_costs = QLineEdit(self.groupBox_5)
        self.gap_costs.setObjectName("gap_costs")

        self.formLayout_5.setWidget(8, QFormLayout.FieldRole, self.gap_costs)

        self.label_23 = QLabel(self.groupBox_5)
        self.label_23.setObjectName("label_23")

        self.formLayout_5.setWidget(9, QFormLayout.LabelRole, self.label_23)

        self.nucl_reward = QLineEdit(self.groupBox_5)
        self.nucl_reward.setObjectName("nucl_reward")

        self.formLayout_5.setWidget(9, QFormLayout.FieldRole, self.nucl_reward)

        self.label_22 = QLabel(self.groupBox_5)
        self.label_22.setObjectName("label_22")

        self.formLayout_5.setWidget(10, QFormLayout.LabelRole, self.label_22)

        self.nucl_penalty = QLineEdit(self.groupBox_5)
        self.nucl_penalty.setObjectName("nucl_penalty")

        self.formLayout_5.setWidget(10, QFormLayout.FieldRole, self.nucl_penalty)

        self.verticalLayout_3.addLayout(self.formLayout_5)

        self.horizontalLayout_23.addWidget(self.groupBox_5)

        self.horizontalLayout_23.setStretch(0, 1)
        self.horizontalLayout_23.setStretch(1, 1)

        self.verticalLayout_10.addLayout(self.horizontalLayout_23)

        self.horizontalLayout_12 = QHBoxLayout()
        self.horizontalLayout_12.setObjectName("horizontalLayout_12")
        self.submit_new_blast = QPushButton(self.tab)
        self.submit_new_blast.setObjectName("submit_new_blast")

        self.horizontalLayout_12.addWidget(self.submit_new_blast)

        self.load_previous_job = QPushButton(self.tab)
        self.load_previous_job.setObjectName("load_previous_job")

        self.horizontalLayout_12.addWidget(self.load_previous_job)

        self.verticalLayout_10.addLayout(self.horizontalLayout_12)

        self.tabWidget.addTab(self.tab, "")
        self.tab_2 = QWidget()
        self.tab_2.setObjectName("tab_2")
        self.verticalLayout_5 = QVBoxLayout(self.tab_2)
        self.verticalLayout_5.setObjectName("verticalLayout_5")
        self.groupBox_2 = QGroupBox(self.tab_2)
        self.groupBox_2.setObjectName("groupBox_2")
        self.verticalLayout_9 = QVBoxLayout(self.groupBox_2)
        self.verticalLayout_9.setObjectName("verticalLayout_9")
        self.control_extension = QCheckBox(self.groupBox_2)
        self.buttonGroup = QButtonGroup(MainWindow)
        self.buttonGroup.setObjectName("buttonGroup")
        self.buttonGroup.addButton(self.control_extension)
        self.control_extension.setObjectName("control_extension")

        self.verticalLayout_9.addWidget(self.control_extension)

        self.horizontalLayout_31 = QHBoxLayout()
        self.horizontalLayout_31.setObjectName("horizontalLayout_31")
        self.reduce_dataset = QCheckBox(self.groupBox_2)
        self.buttonGroup.addButton(self.reduce_dataset)
        self.reduce_dataset.setObjectName("reduce_dataset")

        self.horizontalLayout_31.addWidget(self.reduce_dataset)

        self.horizontalSpacer_6 = QSpacerItem(
            40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum
        )

        self.horizontalLayout_31.addItem(self.horizontalSpacer_6)

        self.horizontalLayout_30 = QHBoxLayout()
        self.horizontalLayout_30.setObjectName("horizontalLayout_30")
        self.label_9 = QLabel(self.groupBox_2)
        self.label_9.setObjectName("label_9")

        self.horizontalLayout_30.addWidget(self.label_9)

        self.consensus_value = QComboBox(self.groupBox_2)
        self.consensus_value.addItem("")
        self.consensus_value.addItem("")
        self.consensus_value.setObjectName("consensus_value")
        sizePolicy3 = QSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        sizePolicy3.setHorizontalStretch(0)
        sizePolicy3.setVerticalStretch(0)
        sizePolicy3.setHeightForWidth(
            self.consensus_value.sizePolicy().hasHeightForWidth()
        )
        self.consensus_value.setSizePolicy(sizePolicy3)
        self.consensus_value.setEditable(True)
        self.consensus_value.setMaxVisibleItems(5)
        self.consensus_value.setMaxCount(2147483645)

        self.horizontalLayout_30.addWidget(self.consensus_value)

        self.horizontalLayout_31.addLayout(self.horizontalLayout_30)

        self.horizontalSpacer_5 = QSpacerItem(
            40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum
        )

        self.horizontalLayout_31.addItem(self.horizontalSpacer_5)

        self.horizontalLayout_29 = QHBoxLayout()
        self.horizontalLayout_29.setObjectName("horizontalLayout_29")
        self.label_5 = QLabel(self.groupBox_2)
        self.label_5.setObjectName("label_5")

        self.horizontalLayout_29.addWidget(self.label_5)

        self.len_threshold = QLineEdit(self.groupBox_2)
        self.len_threshold.setObjectName("len_threshold")

        self.horizontalLayout_29.addWidget(self.len_threshold)

        self.horizontalLayout_31.addLayout(self.horizontalLayout_29)

        self.horizontalLayout_31.setStretch(0, 2)
        self.horizontalLayout_31.setStretch(1, 1)
        self.horizontalLayout_31.setStretch(2, 2)
        self.horizontalLayout_31.setStretch(3, 1)
        self.horizontalLayout_31.setStretch(4, 2)

        self.verticalLayout_9.addLayout(self.horizontalLayout_31)

        self.horizontalLayout_21 = QHBoxLayout()
        self.horizontalLayout_21.setObjectName("horizontalLayout_21")
        self.verticalLayout_4 = QVBoxLayout()
        self.verticalLayout_4.setObjectName("verticalLayout_4")
        self.horizontalLayout_13 = QHBoxLayout()
        self.horizontalLayout_13.setObjectName("horizontalLayout_13")
        self.label_8 = QLabel(self.groupBox_2)
        self.label_8.setObjectName("label_8")

        self.horizontalLayout_13.addWidget(self.label_8)

        self.in_path1 = QLineEdit(self.groupBox_2)
        self.in_path1.setObjectName("in_path1")

        self.horizontalLayout_13.addWidget(self.in_path1)

        self.view_in_path1 = QPushButton(self.groupBox_2)
        self.view_in_path1.setObjectName("view_in_path1")

        self.horizontalLayout_13.addWidget(self.view_in_path1)

        self.horizontalLayout_13.setStretch(0, 1)
        self.horizontalLayout_13.setStretch(1, 7)
        self.horizontalLayout_13.setStretch(2, 1)

        self.verticalLayout_4.addLayout(self.horizontalLayout_13)

        self.horizontalLayout_14 = QHBoxLayout()
        self.horizontalLayout_14.setObjectName("horizontalLayout_14")
        self.label_14 = QLabel(self.groupBox_2)
        self.label_14.setObjectName("label_14")

        self.horizontalLayout_14.addWidget(self.label_14)

        self.out_path1 = QLineEdit(self.groupBox_2)
        self.out_path1.setObjectName("out_path1")

        self.horizontalLayout_14.addWidget(self.out_path1)

        self.view_out_path1 = QPushButton(self.groupBox_2)
        self.view_out_path1.setObjectName("view_out_path1")

        self.horizontalLayout_14.addWidget(self.view_out_path1)

        self.horizontalLayout_14.setStretch(0, 1)
        self.horizontalLayout_14.setStretch(1, 7)
        self.horizontalLayout_14.setStretch(2, 1)

        self.verticalLayout_4.addLayout(self.horizontalLayout_14)

        self.horizontalLayout_21.addLayout(self.verticalLayout_4)

        self.run_filtering = QPushButton(self.groupBox_2)
        self.run_filtering.setObjectName("run_filtering")
        sizePolicy4 = QSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        sizePolicy4.setHorizontalStretch(0)
        sizePolicy4.setVerticalStretch(0)
        sizePolicy4.setHeightForWidth(
            self.run_filtering.sizePolicy().hasHeightForWidth()
        )
        self.run_filtering.setSizePolicy(sizePolicy4)
        self.run_filtering.setAutoDefault(False)
        self.run_filtering.setFlat(False)

        self.horizontalLayout_21.addWidget(self.run_filtering)

        self.horizontalLayout_21.setStretch(0, 4)
        self.horizontalLayout_21.setStretch(1, 1)

        self.verticalLayout_9.addLayout(self.horizontalLayout_21)

        self.verticalLayout_5.addWidget(self.groupBox_2)

        self.groupBox = QGroupBox(self.tab_2)
        self.groupBox.setObjectName("groupBox")
        self.verticalLayout_11 = QVBoxLayout(self.groupBox)
        self.verticalLayout_11.setObjectName("verticalLayout_11")
        self.horizontalLayout_43 = QHBoxLayout()
        self.horizontalLayout_43.setObjectName("horizontalLayout_43")
        self.radioButton_3 = QRadioButton(self.groupBox)
        self.buttonGroup_2 = QButtonGroup(MainWindow)
        self.buttonGroup_2.setObjectName("buttonGroup_2")
        self.buttonGroup_2.addButton(self.radioButton_3)
        self.radioButton_3.setObjectName("radioButton_3")
        self.radioButton_3.setChecked(True)

        self.horizontalLayout_43.addWidget(self.radioButton_3)

        self.radioButton_4 = QRadioButton(self.groupBox)
        self.buttonGroup_2.addButton(self.radioButton_4)
        self.radioButton_4.setObjectName("radioButton_4")

        self.horizontalLayout_43.addWidget(self.radioButton_4)

        self.verticalLayout_11.addLayout(self.horizontalLayout_43)

        self.horizontalLayout_26 = QHBoxLayout()
        self.horizontalLayout_26.setObjectName("horizontalLayout_26")
        self.verticalLayout_6 = QVBoxLayout()
        self.verticalLayout_6.setObjectName("verticalLayout_6")
        self.horizontalLayout_8 = QHBoxLayout()
        self.horizontalLayout_8.setObjectName("horizontalLayout_8")
        self.label_13 = QLabel(self.groupBox)
        self.label_13.setObjectName("label_13")

        self.horizontalLayout_8.addWidget(self.label_13)

        self.in_path2 = QLineEdit(self.groupBox)
        self.in_path2.setObjectName("in_path2")

        self.horizontalLayout_8.addWidget(self.in_path2)

        self.view_in_path2 = QPushButton(self.groupBox)
        self.view_in_path2.setObjectName("view_in_path2")

        self.horizontalLayout_8.addWidget(self.view_in_path2)

        self.horizontalLayout_8.setStretch(0, 1)
        self.horizontalLayout_8.setStretch(1, 7)
        self.horizontalLayout_8.setStretch(2, 1)

        self.verticalLayout_6.addLayout(self.horizontalLayout_8)

        self.horizontalLayout_17 = QHBoxLayout()
        self.horizontalLayout_17.setObjectName("horizontalLayout_17")
        self.label_16 = QLabel(self.groupBox)
        self.label_16.setObjectName("label_16")

        self.horizontalLayout_17.addWidget(self.label_16)

        self.out_path2 = QLineEdit(self.groupBox)
        self.out_path2.setObjectName("out_path2")

        self.horizontalLayout_17.addWidget(self.out_path2)

        self.view_out_path2 = QPushButton(self.groupBox)
        self.view_out_path2.setObjectName("view_out_path2")

        self.horizontalLayout_17.addWidget(self.view_out_path2)

        self.horizontalLayout_17.setStretch(0, 1)
        self.horizontalLayout_17.setStretch(1, 7)
        self.horizontalLayout_17.setStretch(2, 1)

        self.verticalLayout_6.addLayout(self.horizontalLayout_17)

        self.horizontalLayout_25 = QHBoxLayout()
        self.horizontalLayout_25.setObjectName("horizontalLayout_25")
        self.horizontalLayout_9 = QHBoxLayout()
        self.horizontalLayout_9.setObjectName("horizontalLayout_9")
        self.label_2 = QLabel(self.groupBox)
        self.label_2.setObjectName("label_2")

        self.horizontalLayout_9.addWidget(self.label_2)

        self.ali_thr = QLineEdit(self.groupBox)
        self.ali_thr.setObjectName("ali_thr")
        sizePolicy3.setHeightForWidth(self.ali_thr.sizePolicy().hasHeightForWidth())
        self.ali_thr.setSizePolicy(sizePolicy3)

        self.horizontalLayout_9.addWidget(self.ali_thr)

        self.horizontalLayout_25.addLayout(self.horizontalLayout_9)

        self.horizontalLayout_16 = QHBoxLayout()
        self.horizontalLayout_16.setObjectName("horizontalLayout_16")
        self.label_3 = QLabel(self.groupBox)
        self.label_3.setObjectName("label_3")

        self.horizontalLayout_16.addWidget(self.label_3)

        self.ali_reo = QComboBox(self.groupBox)
        self.ali_reo.addItem("")
        self.ali_reo.addItem("")
        self.ali_reo.setObjectName("ali_reo")
        sizePolicy3.setHeightForWidth(self.ali_reo.sizePolicy().hasHeightForWidth())
        self.ali_reo.setSizePolicy(sizePolicy3)
        self.ali_reo.setEditable(True)
        self.ali_reo.setMaxVisibleItems(5)
        self.ali_reo.setMaxCount(2147483645)

        self.horizontalLayout_16.addWidget(self.ali_reo)

        self.horizontalLayout_25.addLayout(self.horizontalLayout_16)

        self.verticalLayout_6.addLayout(self.horizontalLayout_25)

        self.horizontalLayout_20 = QHBoxLayout()
        self.horizontalLayout_20.setObjectName("horizontalLayout_20")
        self.label = QLabel(self.groupBox)
        self.label.setObjectName("label")

        self.horizontalLayout_20.addWidget(self.label)

        self.ali_alg = QComboBox(self.groupBox)
        self.ali_alg.addItem("")
        self.ali_alg.addItem("")
        self.ali_alg.setObjectName("ali_alg")
        sizePolicy3.setHeightForWidth(self.ali_alg.sizePolicy().hasHeightForWidth())
        self.ali_alg.setSizePolicy(sizePolicy3)
        self.ali_alg.setEditable(True)
        self.ali_alg.setMaxVisibleItems(5)
        self.ali_alg.setMaxCount(2147483645)

        self.horizontalLayout_20.addWidget(self.ali_alg)

        self.verticalLayout_6.addLayout(self.horizontalLayout_20)

        self.horizontalLayout_26.addLayout(self.verticalLayout_6)

        self.run_alignment = QPushButton(self.groupBox)
        self.run_alignment.setObjectName("run_alignment")
        sizePolicy4.setHeightForWidth(
            self.run_alignment.sizePolicy().hasHeightForWidth()
        )
        self.run_alignment.setSizePolicy(sizePolicy4)

        self.horizontalLayout_26.addWidget(self.run_alignment)

        self.horizontalLayout_26.setStretch(0, 4)
        self.horizontalLayout_26.setStretch(1, 1)

        self.verticalLayout_11.addLayout(self.horizontalLayout_26)

        self.verticalLayout_5.addWidget(self.groupBox)

        self.groupBox_4 = QGroupBox(self.tab_2)
        self.groupBox_4.setObjectName("groupBox_4")
        self.verticalLayout_12 = QVBoxLayout(self.groupBox_4)
        self.verticalLayout_12.setObjectName("verticalLayout_12")
        self.horizontalLayout_27 = QHBoxLayout()
        self.horizontalLayout_27.setObjectName("horizontalLayout_27")
        self.radioButton_5 = QRadioButton(self.groupBox_4)
        self.buttonGroup_3 = QButtonGroup(MainWindow)
        self.buttonGroup_3.setObjectName("buttonGroup_3")
        self.buttonGroup_3.addButton(self.radioButton_5)
        self.radioButton_5.setObjectName("radioButton_5")
        self.radioButton_5.setChecked(True)

        self.horizontalLayout_27.addWidget(self.radioButton_5)

        self.radioButton_6 = QRadioButton(self.groupBox_4)
        self.buttonGroup_3.addButton(self.radioButton_6)
        self.radioButton_6.setObjectName("radioButton_6")

        self.horizontalLayout_27.addWidget(self.radioButton_6)

        self.horizontalLayout_27.setStretch(0, 1)
        self.horizontalLayout_27.setStretch(1, 1)

        self.verticalLayout_12.addLayout(self.horizontalLayout_27)

        self.horizontalLayout_18 = QHBoxLayout()
        self.horizontalLayout_18.setObjectName("horizontalLayout_18")
        self.verticalLayout_7 = QVBoxLayout()
        self.verticalLayout_7.setObjectName("verticalLayout_7")
        self.horizontalLayout_22 = QHBoxLayout()
        self.horizontalLayout_22.setObjectName("horizontalLayout_22")
        self.label_17 = QLabel(self.groupBox_4)
        self.label_17.setObjectName("label_17")

        self.horizontalLayout_22.addWidget(self.label_17)

        self.in_path3 = QLineEdit(self.groupBox_4)
        self.in_path3.setObjectName("in_path3")

        self.horizontalLayout_22.addWidget(self.in_path3)

        self.view_in_path3 = QPushButton(self.groupBox_4)
        self.view_in_path3.setObjectName("view_in_path3")

        self.horizontalLayout_22.addWidget(self.view_in_path3)

        self.horizontalLayout_22.setStretch(0, 1)
        self.horizontalLayout_22.setStretch(1, 7)
        self.horizontalLayout_22.setStretch(2, 1)

        self.verticalLayout_7.addLayout(self.horizontalLayout_22)

        self.horizontalLayout_6 = QHBoxLayout()
        self.horizontalLayout_6.setObjectName("horizontalLayout_6")
        self.label_26 = QLabel(self.groupBox_4)
        self.label_26.setObjectName("label_26")

        self.horizontalLayout_6.addWidget(self.label_26)

        self.out_path3 = QLineEdit(self.groupBox_4)
        self.out_path3.setObjectName("out_path3")

        self.horizontalLayout_6.addWidget(self.out_path3)

        self.view_out_path3 = QPushButton(self.groupBox_4)
        self.view_out_path3.setObjectName("view_out_path3")

        self.horizontalLayout_6.addWidget(self.view_out_path3)

        self.horizontalLayout_6.setStretch(0, 1)
        self.horizontalLayout_6.setStretch(1, 7)
        self.horizontalLayout_6.setStretch(2, 1)

        self.verticalLayout_7.addLayout(self.horizontalLayout_6)

        self.horizontalLayout_19 = QHBoxLayout()
        self.horizontalLayout_19.setObjectName("horizontalLayout_19")
        self.horizontalLayout_15 = QHBoxLayout()
        self.horizontalLayout_15.setObjectName("horizontalLayout_15")
        self.label_6 = QLabel(self.groupBox_4)
        self.label_6.setObjectName("label_6")
        sizePolicy5 = QSizePolicy(QSizePolicy.Minimum, QSizePolicy.Preferred)
        sizePolicy5.setHorizontalStretch(0)
        sizePolicy5.setVerticalStretch(0)
        sizePolicy5.setHeightForWidth(self.label_6.sizePolicy().hasHeightForWidth())
        self.label_6.setSizePolicy(sizePolicy5)

        self.horizontalLayout_15.addWidget(self.label_6)

        self.tri_met = QComboBox(self.groupBox_4)
        self.tri_met.addItem("")
        self.tri_met.addItem("")
        self.tri_met.addItem("")
        self.tri_met.addItem("")
        self.tri_met.addItem("")
        self.tri_met.setObjectName("tri_met")
        sizePolicy3.setHeightForWidth(self.tri_met.sizePolicy().hasHeightForWidth())
        self.tri_met.setSizePolicy(sizePolicy3)
        self.tri_met.setEditable(True)
        self.tri_met.setMaxVisibleItems(5)
        self.tri_met.setMaxCount(2147483645)

        self.horizontalLayout_15.addWidget(self.tri_met)

        self.horizontalLayout_19.addLayout(self.horizontalLayout_15)

        self.horizontalLayout_19.setStretch(0, 3)

        self.verticalLayout_7.addLayout(self.horizontalLayout_19)

        self.horizontalLayout_57 = QHBoxLayout()
        self.horizontalLayout_57.setObjectName("horizontalLayout_57")
        self.horizontalLayout_52 = QHBoxLayout()
        self.horizontalLayout_52.setObjectName("horizontalLayout_52")
        self.label_48 = QLabel(self.groupBox_4)
        self.label_48.setObjectName("label_48")

        self.horizontalLayout_52.addWidget(self.label_48)

        self.tri_gt = QLineEdit(self.groupBox_4)
        self.tri_gt.setObjectName("tri_gt")

        self.horizontalLayout_52.addWidget(self.tri_gt)

        self.horizontalLayout_57.addLayout(self.horizontalLayout_52)

        self.horizontalLayout_53 = QHBoxLayout()
        self.horizontalLayout_53.setObjectName("horizontalLayout_53")
        self.label_49 = QLabel(self.groupBox_4)
        self.label_49.setObjectName("label_49")

        self.horizontalLayout_53.addWidget(self.label_49)

        self.tri_st = QLineEdit(self.groupBox_4)
        self.tri_st.setObjectName("tri_st")

        self.horizontalLayout_53.addWidget(self.tri_st)

        self.horizontalLayout_57.addLayout(self.horizontalLayout_53)

        self.horizontalLayout_57.setStretch(0, 1)
        self.horizontalLayout_57.setStretch(1, 1)

        self.verticalLayout_7.addLayout(self.horizontalLayout_57)

        self.horizontalLayout_61 = QHBoxLayout()
        self.horizontalLayout_61.setObjectName("horizontalLayout_61")
        self.horizontalLayout_54 = QHBoxLayout()
        self.horizontalLayout_54.setObjectName("horizontalLayout_54")
        self.label_50 = QLabel(self.groupBox_4)
        self.label_50.setObjectName("label_50")

        self.horizontalLayout_54.addWidget(self.label_50)

        self.tri_ct = QLineEdit(self.groupBox_4)
        self.tri_ct.setObjectName("tri_ct")

        self.horizontalLayout_54.addWidget(self.tri_ct)

        self.horizontalLayout_61.addLayout(self.horizontalLayout_54)

        self.horizontalLayout_55 = QHBoxLayout()
        self.horizontalLayout_55.setObjectName("horizontalLayout_55")
        self.label_51 = QLabel(self.groupBox_4)
        self.label_51.setObjectName("label_51")

        self.horizontalLayout_55.addWidget(self.label_51)

        self.tri_con = QLineEdit(self.groupBox_4)
        self.tri_con.setObjectName("tri_con")

        self.horizontalLayout_55.addWidget(self.tri_con)

        self.horizontalLayout_61.addLayout(self.horizontalLayout_55)

        self.horizontalLayout_61.setStretch(0, 1)
        self.horizontalLayout_61.setStretch(1, 1)

        self.verticalLayout_7.addLayout(self.horizontalLayout_61)

        self.horizontalLayout_18.addLayout(self.verticalLayout_7)

        self.run_trimming = QPushButton(self.groupBox_4)
        self.run_trimming.setObjectName("run_trimming")
        sizePolicy4.setHeightForWidth(
            self.run_trimming.sizePolicy().hasHeightForWidth()
        )
        self.run_trimming.setSizePolicy(sizePolicy4)

        self.horizontalLayout_18.addWidget(self.run_trimming)

        self.horizontalLayout_18.setStretch(0, 4)
        self.horizontalLayout_18.setStretch(1, 1)

        self.verticalLayout_12.addLayout(self.horizontalLayout_18)

        self.verticalLayout_5.addWidget(self.groupBox_4)

        self.groupBox_6 = QGroupBox(self.tab_2)
        self.groupBox_6.setObjectName("groupBox_6")
        self.horizontalLayout_28 = QHBoxLayout(self.groupBox_6)
        self.horizontalLayout_28.setObjectName("horizontalLayout_28")
        self.verticalLayout_8 = QVBoxLayout()
        self.verticalLayout_8.setObjectName("verticalLayout_8")
        self.horizontalLayout_64 = QHBoxLayout()
        self.horizontalLayout_64.setObjectName("horizontalLayout_64")
        self.label_55 = QLabel(self.groupBox_6)
        self.label_55.setObjectName("label_55")

        self.horizontalLayout_64.addWidget(self.label_55)

        self.in_path4 = QLineEdit(self.groupBox_6)
        self.in_path4.setObjectName("in_path4")

        self.horizontalLayout_64.addWidget(self.in_path4)

        self.view_in_path4 = QPushButton(self.groupBox_6)
        self.view_in_path4.setObjectName("view_in_path4")

        self.horizontalLayout_64.addWidget(self.view_in_path4)

        self.horizontalLayout_64.setStretch(0, 1)
        self.horizontalLayout_64.setStretch(1, 7)
        self.horizontalLayout_64.setStretch(2, 1)

        self.verticalLayout_8.addLayout(self.horizontalLayout_64)

        self.horizontalLayout_24 = QHBoxLayout()
        self.horizontalLayout_24.setObjectName("horizontalLayout_24")
        self.label_39 = QLabel(self.groupBox_6)
        self.label_39.setObjectName("label_39")

        self.horizontalLayout_24.addWidget(self.label_39)

        self.out_path4 = QLineEdit(self.groupBox_6)
        self.out_path4.setObjectName("out_path4")

        self.horizontalLayout_24.addWidget(self.out_path4)

        self.view_out_path4 = QPushButton(self.groupBox_6)
        self.view_out_path4.setObjectName("view_out_path4")

        self.horizontalLayout_24.addWidget(self.view_out_path4)

        self.horizontalLayout_24.setStretch(0, 1)
        self.horizontalLayout_24.setStretch(1, 7)
        self.horizontalLayout_24.setStretch(2, 1)

        self.verticalLayout_8.addLayout(self.horizontalLayout_24)

        self.horizontalLayout_28.addLayout(self.verticalLayout_8)

        self.horizontalLayout_7 = QHBoxLayout()
        self.horizontalLayout_7.setObjectName("horizontalLayout_7")
        self.run_concatenation = QPushButton(self.groupBox_6)
        self.run_concatenation.setObjectName("run_concatenation")
        sizePolicy6 = QSizePolicy(QSizePolicy.Expanding, QSizePolicy.Ignored)
        sizePolicy6.setHorizontalStretch(0)
        sizePolicy6.setVerticalStretch(0)
        sizePolicy6.setHeightForWidth(
            self.run_concatenation.sizePolicy().hasHeightForWidth()
        )
        self.run_concatenation.setSizePolicy(sizePolicy6)

        self.horizontalLayout_7.addWidget(self.run_concatenation)

        self.horizontalLayout_28.addLayout(self.horizontalLayout_7)

        self.horizontalLayout_28.setStretch(0, 4)
        self.horizontalLayout_28.setStretch(1, 1)

        self.verticalLayout_5.addWidget(self.groupBox_6)

        self.verticalLayout_5.setStretch(1, 2)
        self.verticalLayout_5.setStretch(2, 3)
        self.verticalLayout_5.setStretch(3, 1)
        self.tabWidget.addTab(self.tab_2, "")

        self.horizontalLayout.addWidget(self.tabWidget)

        self.groupBox_3 = QGroupBox(self.centralwidget)
        self.groupBox_3.setObjectName("groupBox_3")
        self.horizontalLayout_3 = QHBoxLayout(self.groupBox_3)
        self.horizontalLayout_3.setSpacing(4)
        self.horizontalLayout_3.setObjectName("horizontalLayout_3")
        self.horizontalLayout_3.setSizeConstraint(QLayout.SetMaximumSize)
        self.message_box = QPlainTextEdit(self.groupBox_3)
        self.message_box.setObjectName("message_box")
        sizePolicy2.setHeightForWidth(self.message_box.sizePolicy().hasHeightForWidth())
        self.message_box.setSizePolicy(sizePolicy2)

        self.horizontalLayout_3.addWidget(self.message_box)

        self.horizontalLayout_3.setStretch(0, 1)

        self.horizontalLayout.addWidget(self.groupBox_3)

        self.horizontalLayout.setStretch(0, 2)
        self.horizontalLayout.setStretch(1, 1)
        MainWindow.setCentralWidget(self.centralwidget)
        self.menubar = QMenuBar(MainWindow)
        self.menubar.setObjectName("menubar")
        self.menubar.setGeometry(QRect(0, 0, 1499, 21))
        self.menuMain = QMenu(self.menubar)
        self.menuMain.setObjectName("menuMain")
        self.menuTools = QMenu(self.menubar)
        self.menuTools.setObjectName("menuTools")
        self.menuInstall_dependencies = QMenu(self.menuTools)
        self.menuInstall_dependencies.setObjectName("menuInstall_dependencies")
        MainWindow.setMenuBar(self.menubar)
        self.statusbar = QStatusBar(MainWindow)
        self.statusbar.setObjectName("statusbar")
        MainWindow.setStatusBar(self.statusbar)

        self.menubar.addAction(self.menuMain.menuAction())
        self.menubar.addAction(self.menuTools.menuAction())
        self.menuMain.addAction(self.actionAbout)
        self.menuMain.addAction(self.actionExit)
        self.menuTools.addAction(self.menuInstall_dependencies.menuAction())
        self.menuInstall_dependencies.addAction(self.actionInstall_MAFFT)
        self.menuInstall_dependencies.addAction(self.actionInstall_trimAl)

        self.retranslateUi(MainWindow)

        self.tabWidget.setCurrentIndex(0)
        self.run_filtering.setDefault(False)

        QMetaObject.connectSlotsByName(MainWindow)

    # setupUi

    def retranslateUi(self, MainWindow):
        MainWindow.setWindowTitle(
            QCoreApplication.translate("MainWindow", "PyNCBIminer", None)
        )
        self.actionChange_font.setText(
            QCoreApplication.translate("MainWindow", "Change font", None)
        )
        self.actionInstall_MAFFT.setText(
            QCoreApplication.translate("MainWindow", "Install MAFFT", None)
        )
        self.actionInstall_trimAl.setText(
            QCoreApplication.translate("MainWindow", "Install Trimal", None)
        )
        self.groupBox_7.setTitle(
            QCoreApplication.translate("MainWindow", "Working Directory", None)
        )
        self.label_32.setText(
            QCoreApplication.translate("MainWindow", "working directory:", None)
        )
        self.wd.setPlaceholderText(
            QCoreApplication.translate(
                "MainWindow", "absolute path of working directory", None
            )
        )
        self.view.setText(QCoreApplication.translate("MainWindow", "view", None))
        self.groupBox_8.setTitle(
            QCoreApplication.translate("MainWindow", "Basic Settings", None)
        )
        self.label_24.setText(
            QCoreApplication.translate("MainWindow", "target groups:", None)
        )
        self.taxonomy.setPlaceholderText(
            QCoreApplication.translate("MainWindow", "one taxon per line", None)
        )
        self.label_4.setText(
            QCoreApplication.translate(
                "MainWindow", "select or input target regeion:", None
            )
        )
        self.target_region.setItemText(0, "")
        self.target_region.setItemText(
            1, QCoreApplication.translate("MainWindow", "ITS", None)
        )
        self.target_region.setItemText(
            2, QCoreApplication.translate("MainWindow", "rbcL", None)
        )
        self.target_region.setItemText(
            3, QCoreApplication.translate("MainWindow", "matK", None)
        )
        self.target_region.setItemText(
            4, QCoreApplication.translate("MainWindow", "trnL-trnF", None)
        )
        self.target_region.setItemText(
            5, QCoreApplication.translate("MainWindow", "psbA-trnH", None)
        )
        self.target_region.setItemText(
            6, QCoreApplication.translate("MainWindow", "ndhF", None)
        )
        self.target_region.setItemText(
            7, QCoreApplication.translate("MainWindow", "rpoB", None)
        )

        self.target_region.setCurrentText("")
        self.target_region.setPlaceholderText("")
        self.set_target_region.setText(
            QCoreApplication.translate("MainWindow", "set target region", None)
        )
        self.save_settings.setText(
            QCoreApplication.translate("MainWindow", "save settings", None)
        )
        self.label_25.setText(
            QCoreApplication.translate("MainWindow", "entrez qualifier:", None)
        )
        self.entrez_qualifier.setPlaceholderText(
            QCoreApplication.translate("MainWindow", "constraint on BLAST search", None)
        )
        self.label_31.setText(
            QCoreApplication.translate("MainWindow", "publication date:  ", None)
        )
        self.label_43.setText(QCoreApplication.translate("MainWindow", "from", None))
        self.date_from.setPlaceholderText(
            QCoreApplication.translate("MainWindow", "YYYY/MM/DD", None)
        )
        self.label_42.setText(QCoreApplication.translate("MainWindow", "to", None))
        self.date_to.setPlaceholderText(
            QCoreApplication.translate("MainWindow", "YYYY/MM/DD", None)
        )
        self.label_27.setText(
            QCoreApplication.translate("MainWindow", "entrez email:", None)
        )
        self.entrez_email.setPlaceholderText(
            QCoreApplication.translate("MainWindow", "user's email", None)
        )
        self.marker_summary.setText(
            QCoreApplication.translate(
                "MainWindow", "summarize widely used marker", None
            )
        )
        self.esearch.setText(
            QCoreApplication.translate("MainWindow", "entrez search", None)
        )
        self.groupBox_5.setTitle(
            QCoreApplication.translate("MainWindow", "Advanced Settings", None)
        )
        self.label_33.setText(
            QCoreApplication.translate("MainWindow", "initial queries:", None)
        )
        self.initial_queries.setPlaceholderText(
            QCoreApplication.translate(
                "MainWindow", "paste sequences in fasta format here", None
            )
        )
        self.label_30.setText(
            QCoreApplication.translate("MainWindow", "key annotations:", None)
        )
        self.key_annotations.setPlaceholderText(
            QCoreApplication.translate("MainWindow", "one keyword per line", None)
        )
        self.label_29.setText(
            QCoreApplication.translate("MainWindow", "exclude sources:", None)
        )
        self.exclude_sources.setPlaceholderText(
            QCoreApplication.translate("MainWindow", "one keyword per line", None)
        )
        self.label_18.setText(
            QCoreApplication.translate("MainWindow", "max length:", None)
        )
        self.max_length.setPlaceholderText(
            QCoreApplication.translate("MainWindow", "integer", None)
        )
        self.label_7.setText(
            QCoreApplication.translate("MainWindow", "expect value:", None)
        )
        self.expect_value.setPlaceholderText(
            QCoreApplication.translate("MainWindow", "nonnegative number", None)
        )
        self.label_15.setText(
            QCoreApplication.translate("MainWindow", "word size:", None)
        )
        self.word_size.setPlaceholderText(
            QCoreApplication.translate("MainWindow", "positive integer", None)
        )
        self.label_21.setText(
            QCoreApplication.translate("MainWindow", "gap costs:", None)
        )
        self.gap_costs.setPlaceholderText(
            QCoreApplication.translate(
                "MainWindow",
                "two positive integers separated  such as \u201c11 1\u201d",
                None,
            )
        )
        self.label_23.setText(
            QCoreApplication.translate("MainWindow", "nucleotide reward:", None)
        )
        self.nucl_reward.setPlaceholderText(
            QCoreApplication.translate("MainWindow", "nonnegative number", None)
        )
        self.label_22.setText(
            QCoreApplication.translate("MainWindow", "nucleotide penalty:", None)
        )
        self.nucl_penalty.setText("")
        self.nucl_penalty.setPlaceholderText(
            QCoreApplication.translate("MainWindow", "nonpositive integer", None)
        )
        self.submit_new_blast.setText(
            QCoreApplication.translate("MainWindow", "submit new BLAST", None)
        )
        self.load_previous_job.setText(
            QCoreApplication.translate("MainWindow", "load previous job", None)
        )
        self.tabWidget.setTabText(
            self.tabWidget.indexOf(self.tab),
            QCoreApplication.translate("MainWindow", "Sequence Retrieval", None),
        )
        self.groupBox_2.setTitle(
            QCoreApplication.translate("MainWindow", "Sequences Filtering", None)
        )
        self.control_extension.setText(
            QCoreApplication.translate(
                "MainWindow", "Extended segments refinement", None
            )
        )
        self.reduce_dataset.setText(
            QCoreApplication.translate(
                "MainWindow", "Species-level sequence selection", None
            )
        )
        self.label_9.setText(
            QCoreApplication.translate("MainWindow", "abnormal index", None)
        )
        self.consensus_value.setItemText(
            0, QCoreApplication.translate("MainWindow", "True", None)
        )
        self.consensus_value.setItemText(
            1, QCoreApplication.translate("MainWindow", "False", None)
        )

        self.consensus_value.setCurrentText(
            QCoreApplication.translate("MainWindow", "True", None)
        )
        self.label_5.setText(
            QCoreApplication.translate("MainWindow", "length threshold:", None)
        )
        self.len_threshold.setText(
            QCoreApplication.translate("MainWindow", "100", None)
        )
        self.label_8.setText(
            QCoreApplication.translate("MainWindow", "input path:", None)
        )
        self.in_path1.setPlaceholderText(
            QCoreApplication.translate(
                "MainWindow",
                "one working directory or the parent directory of multiple working directories",
                None,
            )
        )
        self.view_in_path1.setText(
            QCoreApplication.translate("MainWindow", "view", None)
        )
        self.label_14.setText(
            QCoreApplication.translate("MainWindow", "output path:", None)
        )
        self.out_path1.setPlaceholderText(
            QCoreApplication.translate(
                "MainWindow", "the same as input path by default", None
            )
        )
        self.view_out_path1.setText(
            QCoreApplication.translate("MainWindow", "view", None)
        )
        self.run_filtering.setText(
            QCoreApplication.translate("MainWindow", "run", None)
        )
        self.groupBox.setTitle(
            QCoreApplication.translate("MainWindow", "Sequences Alignment", None)
        )
        self.radioButton_3.setText(
            QCoreApplication.translate("MainWindow", "input one file", None)
        )
        self.radioButton_4.setText(
            QCoreApplication.translate(
                "MainWindow", "input multiple files in one folder", None
            )
        )
        self.label_13.setText(
            QCoreApplication.translate("MainWindow", "input path:", None)
        )
        self.in_path2.setPlaceholderText(
            QCoreApplication.translate(
                "MainWindow",
                "the path of one fasta file or the folder path that contains multiple fasta files",
                None,
            )
        )
        self.view_in_path2.setText(
            QCoreApplication.translate("MainWindow", "view", None)
        )
        self.label_16.setText(
            QCoreApplication.translate("MainWindow", "output path:", None)
        )
        self.out_path2.setPlaceholderText(
            QCoreApplication.translate(
                "MainWindow",
                "one folder to save the aligned fasta files, create a new one if does not exists",
                None,
            )
        )
        self.view_out_path2.setText(
            QCoreApplication.translate("MainWindow", "view", None)
        )
        self.label_2.setText(QCoreApplication.translate("MainWindow", "thread:", None))
        self.ali_thr.setText(QCoreApplication.translate("MainWindow", "-1", None))
        self.label_3.setText(QCoreApplication.translate("MainWindow", "reorder:", None))
        self.ali_reo.setItemText(
            0, QCoreApplication.translate("MainWindow", "True", None)
        )
        self.ali_reo.setItemText(
            1, QCoreApplication.translate("MainWindow", "False", None)
        )

        self.ali_reo.setCurrentText(
            QCoreApplication.translate("MainWindow", "True", None)
        )
        self.label.setText(
            QCoreApplication.translate("MainWindow", "alignment strategies:", None)
        )
        self.ali_alg.setItemText(
            0,
            QCoreApplication.translate(
                "MainWindow", "auto (depends on data size)", None
            ),
        )
        self.ali_alg.setItemText(
            1,
            QCoreApplication.translate(
                "MainWindow",
                "add (use long sequences as backbone to align fragment sequences)",
                None,
            ),
        )

        self.ali_alg.setCurrentText(
            QCoreApplication.translate(
                "MainWindow", "auto (depends on data size)", None
            )
        )
        self.run_alignment.setText(
            QCoreApplication.translate("MainWindow", "run", None)
        )
        self.groupBox_4.setTitle(
            QCoreApplication.translate("MainWindow", "Alignments Trimming", None)
        )
        self.radioButton_5.setText(
            QCoreApplication.translate("MainWindow", "input one file", None)
        )
        self.radioButton_6.setText(
            QCoreApplication.translate(
                "MainWindow", "input multiple files in one folder", None
            )
        )
        self.label_17.setText(
            QCoreApplication.translate("MainWindow", "input path:", None)
        )
        self.in_path3.setText("")
        self.in_path3.setPlaceholderText(
            QCoreApplication.translate(
                "MainWindow",
                "the path of one fasta file or the folder path that contains multiple fasta files",
                None,
            )
        )
        self.view_in_path3.setText(
            QCoreApplication.translate("MainWindow", "view", None)
        )
        self.label_26.setText(
            QCoreApplication.translate("MainWindow", "output path:", None)
        )
        self.out_path3.setPlaceholderText(
            QCoreApplication.translate(
                "MainWindow",
                "one folder to save the trimmeded fasta files, create a new one if does not exists",
                None,
            )
        )
        self.view_out_path3.setText(
            QCoreApplication.translate("MainWindow", "view", None)
        )
        self.label_6.setText(
            QCoreApplication.translate("MainWindow", "automatic methods", None)
        )
        self.tri_met.setItemText(
            0,
            QCoreApplication.translate(
                "MainWindow",
                "automated1 (heuristic selection based on similarity statistics)",
                None,
            ),
        )
        self.tri_met.setItemText(
            1,
            QCoreApplication.translate(
                "MainWindow",
                "gappyout (uses information based on gaps' distribution)",
                None,
            ),
        )
        self.tri_met.setItemText(
            2,
            QCoreApplication.translate(
                "MainWindow", 'strict (automatic selection on "strict" mode)', None
            ),
        )
        self.tri_met.setItemText(
            3,
            QCoreApplication.translate(
                "MainWindow",
                'strictplus (automatic selection on "strictplus" mode)',
                None,
            ),
        )
        self.tri_met.setItemText(
            4,
            QCoreApplication.translate(
                "MainWindow",
                "user defined method (set thresholds of non gap, similarity, consistency...)",
                None,
            ),
        )

        self.tri_met.setCurrentText(
            QCoreApplication.translate(
                "MainWindow",
                "automated1 (heuristic selection based on similarity statistics)",
                None,
            )
        )
        self.label_48.setText(
            QCoreApplication.translate("MainWindow", "non gap threshold (0-1):", None)
        )
        self.tri_gt.setText("")
        self.tri_gt.setPlaceholderText("")
        self.label_49.setText(
            QCoreApplication.translate(
                "MainWindow", "similarity threshold (0-1):", None
            )
        )
        self.tri_st.setText("")
        self.label_50.setText(
            QCoreApplication.translate(
                "MainWindow", "consistency threshold (0-1):", None
            )
        )
        self.tri_ct.setText("")
        self.label_51.setText(
            QCoreApplication.translate(
                "MainWindow", "min percentage to conserve (0-100):", None
            )
        )
        self.tri_con.setText("")
        self.run_trimming.setText(QCoreApplication.translate("MainWindow", "run", None))
        self.groupBox_6.setTitle(
            QCoreApplication.translate("MainWindow", "Alignments concatenation", None)
        )
        self.label_55.setText(
            QCoreApplication.translate("MainWindow", "input path:", None)
        )
        self.in_path4.setPlaceholderText(
            QCoreApplication.translate(
                "MainWindow",
                "the  folder path that contains multiple fasta files",
                None,
            )
        )
        self.view_in_path4.setText(
            QCoreApplication.translate("MainWindow", "view", None)
        )
        self.label_39.setText(
            QCoreApplication.translate("MainWindow", "output path:", None)
        )
        self.out_path4.setPlaceholderText(
            QCoreApplication.translate(
                "MainWindow",
                "one folder to save the concatenation results, create a new one if does not exists",
                None,
            )
        )
        self.view_out_path4.setText(
            QCoreApplication.translate("MainWindow", "view", None)
        )
        self.run_concatenation.setText(
            QCoreApplication.translate("MainWindow", "run", None)
        )
        self.tabWidget.setTabText(
            self.tabWidget.indexOf(self.tab_2),
            QCoreApplication.translate("MainWindow", "Supermatrix Construction", None),
        )
        self.groupBox_3.setTitle(
            QCoreApplication.translate("MainWindow", "Message Box", None)
        )
        self.message_box.setPlaceholderText(
            QCoreApplication.translate(
                "MainWindow", "Welcome to use PyNCBIminer!", None
            )
        )
        self.menuMain.setTitle(QCoreApplication.translate("MainWindow", "Main", None))
        self.menuTools.setTitle(QCoreApplication.translate("MainWindow", "Tools", None))
        self.menuInstall_dependencies.setTitle(
            QCoreApplication.translate("MainWindow", "Install dependencies", None)
        )
        self.actionAbout.setText(
            QCoreApplication.translate("MainWindow", "About", None)
        )
        self.actionExit.setText(QCoreApplication.translate("MainWindow", "Exit", None))

    # retranslateUi
