from PyQt5.QtWidgets import *
from PyQt5.QtCore import pyqtSlot, QTimer
from collections import defaultdict
from datetime import datetime, date
import pprint
import os

from gen_tools import Tools


class SettingsList(QListWidget):
    UNICODE_SYMBOLS = {'Spreadsheet': '📅', 'Word Document': '📰', 'Presentation': '📊',
                       'PDF': '📋', 'Audio': '♫', 'Video': '🎬',
                       'Image': '📷', 'Text': '📄', 'Archive': '🗂'}
    EMPTY_CONTENTS = (set(), defaultdict(list))

    def __init__(self):
        super().__init__()
        self.qlist_indices = {}

    def _add_selected_dir(self, selected_path):
        if 'Current Directory' in self.qlist_indices:
            end, start = self.qlist_indices['Current Directory']
            for i in range(end - 1, start - 1, -1):
                self.takeItem(i)
        self.insertItem(0, "[Current Directory]")
        self.insertItem(1, Tools.shorten_path(selected_path))
        self.insertItem(2, "")
        self.qlist_indices['Current Directory'] = (3, 0)

    @staticmethod
    def _valid_pos(pos, settings):
        if pos in [setting[0] for setting in list(settings)]:
            QMessageBox(QMessageBox.Warning, "Error: Position already selected",
                        f"The selected position, \"{pos}\", has a setting already mapped to it.",
                        QMessageBox.Ok | QMessageBox.Cancel).exec()
            return False
        else:
            return True

    @pyqtSlot()
    def _ignore_settings(self, tab, main_ui):
        tab.main_box.setEnabled(False)
        if tab.name in self.qlist_indices:
            end, start = self.qlist_indices[tab.name]
            total_length = end-start
            # Go backwards to remove last added item.
            # Rows have 0 indexing so -1.
            for i in range(end - 1, start - 1, -1):
                self.takeItem(i)
            # Adjust other categ indices when above row removed.
            for tab_type, indices in self.qlist_indices.items():
                # Subtract indices of categ being removed only when the other categories have higher indices.
                if tab_type != tab.name and indices[0] > end:
                    self.qlist_indices[tab_type] = (indices[0] - total_length, indices[1] - total_length)
            self.qlist_indices.pop(tab.name)
            main_ui.sort_settings.pop(tab.name)

    @pyqtSlot()
    def _confirm_settings(self, tab, main_ui):
        # TODO: Insert item based on pos. Use range(len(list)) with insertItem()

        tab.main_box.setEnabled(False)

        # Need to keep isChecked() because state of both buttons changes when either one clicked.
        sort_pos = tab.order.currentText().split(":")[-1].replace(" ", "")[0]

        main_ui.sort_settings[tab.name] = defaultdict(list)

        # Starting index in confirmed_settings QListObject.
        qlist_st_ind = self.count()

        # Exit function if sort pos already exists or tab contents is empty.
        contents = (tab.contents[1] if isinstance(tab.contents, tuple) else tab.contents)
        if self._valid_pos(sort_pos, main_ui.sort_settings.values()) and contents not in self.EMPTY_CONTENTS:
            self.addItem(f"[{sort_pos} - Sort By {tab.name}]")
        else:
            # Reset tribox to "Ignore" state.
            tab.confirm_tribox.setCheckState(0)
            return

        if tab.name == 'Keyword':

            for folder, keywords in tab.contents.items():
                self.addItem(f"{' ' * 3}📁 {folder}")
                for keyword in keywords:
                    self.addItem(f" {' ' * 6}🔍 {keyword}")
                    main_ui.sort_settings[tab.name][folder].append(keyword)

        elif tab.name == 'File Type':
            # Contents is tuple of option and list of ftypes
            (option, ftypes) = tab.contents
            for ftype in ftypes:
                self.addItem(f"{' ' * 3}{self.UNICODE_SYMBOLS.get(ftype, '🔍')} {ftype}")
                main_ui.sort_settings[tab.name][option].append(ftype)

        elif tab.name == 'Date':
            (mode, interval, date_range) = tab.contents
            if date_range['Starting Date'] == '':
                date_range['Starting Date'] = date(1900, 1, 1).strftime("%m-%d-%Y")
            if date_range['Ending Date'] == '':
                date_range['Ending Date'] = datetime.now().strftime("%m-%d-%Y")
            self.addItem(f"{' ' * 3}⌛ {interval.capitalize()} - {mode}")
            self.addItem(f"{' ' * 6}📆 ({date_range['Starting Date']}) → ({date_range['Ending Date']})")

            main_ui.sort_settings[tab.name] = {'Time Mode': mode, 'Time Interval': interval, 'Date Range': date_range}

        # Spacer between items.
        self.addItem("")

        # Ending index in confirmed_settings QListObject
        qlist_end_ind = self.count()

        # Save range of settings in QList Object. Subtract by 1 from start because of range().
        self.qlist_indices[tab.name] = (qlist_end_ind, qlist_st_ind)

        # Add position to first index of values rather than key. Easier to access later.
        # Convert back to normal dictionary for logging clarity.
        main_ui.sort_settings[tab.name] = (sort_pos, dict(main_ui.sort_settings[tab.name]))


# noinspection PyProtectedMember
class NewTab:
    """
    Adds a new tab to a parent widget (parent) and fills it depending on its name.
    Connects widgets to functions in SorterUI.
    """

    CONF_BOX_POS = (1, 1)

    def __init__(self, ui, parent_tab, name):
        self.name = name
        self.ui = ui

        # Settings list obj created in SorterUI class.
        self.settings_list = ui.displayed_settings

        self.mtab_widg = QWidget()
        self.mtab_layout = QGridLayout()
        parent_tab.addTab(self.mtab_widg, name)
        self.mtab_widg.setLayout(self.mtab_layout)

        self.main_box = QGroupBox(name)
        self.order = QComboBox()
        self.confirm_tribox = QCheckBox('Ignore | Edit | Confirm')

        # Fill tab
        self._fill_tab()

    def _fill_tab(self):
        self.main_box.setEnabled(False)
        self.confirm_tribox.setTristate(True)

        # Connect widgets to function from SettingsList
        # Tristate outputs 0 (Empty), 1 (Filled), and 2 (Checked).
        box_states = {0: self.settings_list._ignore_settings, 1: lambda *args: self.main_box.setEnabled(True),
                      2: self.settings_list._confirm_settings}
        self.confirm_tribox.clicked.connect(lambda: box_states[self.confirm_tribox.checkState()](self, self.ui))

        self.order.insertItems(0, ["Sort Order: 1st", "Sort Order: 2nd", "Sort Order: 3rd"])
        self.mtab_layout.addWidget(self._create_confirm_box(), *self.CONF_BOX_POS)

    def _create_confirm_box(self):
        box = QGroupBox("Confirmation")
        box_layout = QVBoxLayout()
        box.setLayout(box_layout)
        box_layout.addWidget(self.order)
        box_layout.addWidget(self.confirm_tribox)
        return box


class DateButtons(NewTab):
    WIDGET_POS = (2, 1, 3, 1)

    def __init__(self, main_ui, parent_tab, name):
        super().__init__(main_ui, parent_tab, name)
        self.date_btn_layout = QGridLayout()
        self.main_box.setLayout(self.date_btn_layout)
        self.mtab_layout.addWidget(self.main_box, *self.WIDGET_POS)

        self.date_intervals = QComboBox()
        self.date_modes = QComboBox()
        self.calendar = QCalendarWidget()
        self.calendar_ranges = {}
        self.calendar_range_btns = QButtonGroup()
        self.current_btn = None

        self._add_date_options()
        self._add_calendar()

    def _add_date_options(self):
        date_intervals_box = QFrame()
        date_intervals_layout = QGridLayout()
        date_intervals_box.setLayout(date_intervals_layout)

        self.date_intervals.addItems(("Day", "Month", "Year"))
        self.date_modes.addItems(("Time Modified", "Time Accessed", "Time Created"))

        date_intervals_layout.addWidget(QLabel("File Time Mode (m/a/c)"), 0, 0)
        date_intervals_layout.addWidget(QLabel("Date Intervals (D/M/Y)"), 1, 0)
        date_intervals_layout.addWidget(self.date_modes, 0, 1)
        date_intervals_layout.addWidget(self.date_intervals, 1, 1)

        self.date_btn_layout.addWidget(date_intervals_box)
        self.date_btn_layout.addWidget(Tools.create_seperator())

    @pyqtSlot()
    def _select_date(self, chosen_date):
        self.calendar_ranges[self.current_btn].setText(chosen_date.toString("MM-dd-yyyy"))
        self.calendar.setEnabled(False)

    @pyqtSlot()
    def _set_btn_categ(self, btn_categ):
        self.current_btn = btn_categ

    def _create_date_range(self):
        range_box = QWidget()
        range_layout = QHBoxLayout()
        range_box.setLayout(range_layout)

        self.calendar_ranges['Starting Date'] = QLineEdit()
        self.calendar_ranges['Ending Date'] = QLineEdit()

        for name, widg in self.calendar_ranges.items():
            update_btn = QPushButton(name)
            self.calendar_range_btns.addButton(update_btn)
            range_layout.addWidget(update_btn)
            range_layout.addWidget(widg)
            widg.setReadOnly(True)

        # Enable calendar to be clicked and set the date categ to be modified.
        self.calendar_range_btns.buttonPressed.connect(lambda btn: [self.calendar.setEnabled(True),
                                                                    self._set_btn_categ(btn.text())])
        return range_box

    def _add_calendar(self):
        self.calendar.setEnabled(False)
        self.calendar.clicked.connect(lambda chosen_date: self._select_date(chosen_date))
        self.date_btn_layout.addWidget(self.calendar)
        self.date_btn_layout.addWidget(self._create_date_range())

    @property
    def contents(self):
        return self.date_modes.currentText(), self.date_intervals.currentText(), \
               {categ: fin_date.text() for categ, fin_date in self.calendar_ranges.items()}


class FileTypeButtons(NewTab):
    FILE_CATEG = ('Spreadsheet', 'Word Document', 'Presentation', 'PDF', 'Audio', 'Video', 'Image', 'Text', 'Archive')
    WIDGET_POS = (2, 1, 3, 1)

    def __init__(self, main_ui, parent_tab, name):
        super().__init__(main_ui, parent_tab, name)

        self.main_btns = QButtonGroup()
        self.specific_btns = QButtonGroup()
        self.specific_btns.setExclusive(False)
        self.ftype_entry = QLineEdit()
        self.ftype_entry.setClearButtonEnabled(True)

        self.button_results = {"All Types": self.FILE_CATEG,
                               "Specific Types": set(),
                               "Custom File Extension": set()}

        self.ftypes_layout = QVBoxLayout()
        self.main_box.setLayout(self.ftypes_layout)
        self.mtab_layout.addWidget(self.main_box, *self.WIDGET_POS)
        self._add_file_categ_btns()

    @pyqtSlot()
    def _enable_ftype_btns(self, boolean):
        for button in self.specific_btns.buttons():
            button.setEnabled(boolean)

    def _add_file_categ_btns(self):
        categ_slots = {'All Types': lambda: [self._enable_ftype_btns(False), self.ftype_entry.setEnabled(False)],
                       # Disable specific type btns and qlineedit
                       'Specific Types': lambda: [self._enable_ftype_btns(True), self.ftype_entry.setEnabled(False)],
                       # Enable specific type btns and disable qlineedit
                       'Custom File Extension': lambda: [self._enable_ftype_btns(False), self.ftype_entry.setEnabled(
                           True)]}  # Disable specific type btns and enable qlineedit
        for num, (categ, button) in enumerate(self.button_results.items(), 1):
            categ_btn = QRadioButton(categ)
            self.main_btns.addButton(categ_btn, id=num)
            if categ == 'All Types':
                # Set default to be All Types.
                categ_btn.toggle()
            categ_btn.clicked.connect(categ_slots[categ])

            self.ftypes_layout.addWidget(categ_btn)
            self._add_child_widgs(categ, num)
            self._enable_ftype_btns(False)

    @property
    def contents(self):
        categ = self.main_btns.checkedButton().text().strip(" ✔").strip(" 🗙")
        # Convert to dict.
        return categ, self.button_results[categ]

    def _add_child_widgs(self, categ, btn_num):
        """
        Adds QButtonGroup (File types) buttons for Specific as QWidgets with QHboxlayouts with a spacing and a checkbutton.
        Adds a QLineEdit for Custom.
        """

        if categ == 'Specific Types':

            def _build_row():
                checkbox_frame = QWidget()
                checkbox_hbox = QHBoxLayout()
                checkbox_frame.setLayout(checkbox_hbox)

                # Reset content margins to avoid cutting off next QWidget.
                # Add spacing to left to indent.
                checkbox_hbox.setContentsMargins(0, 0, 0, 0)
                checkbox_hbox.addSpacing(10)
                return checkbox_frame, checkbox_hbox

            for num, ftype in enumerate(self.FILE_CATEG):
                # Row with spacing.
                chk_frame, chk_layout = _build_row()

                # Added to checkbox frame and QButtonGroup.
                temp_checkbox = QCheckBox(ftype)
                temp_checkbox.clicked.connect(lambda: self.ftype_entry.setEnabled(False))
                self.specific_btns.addButton(temp_checkbox, id=num)
                chk_layout.addWidget(self.specific_btns.button(num))

                # Add frame with spacing + checkbox to main tab layout.
                self.ftypes_layout.addWidget(chk_frame)

            # Toggle the parent button if child button clicked.
            self.specific_btns.buttonClicked.connect(lambda: self.main_btns.button(btn_num).toggle())
            self.specific_btns.buttonClicked.connect(lambda btn: self.button_results[categ].add(btn.text()))

        elif categ == 'Custom File Extension':
            def _add_ftype(ftypes, new_ftype, btn, og_text):
                # Ignore entry if empty
                if new_ftype.strip() != "":
                    # reformat entry to be file extension and have . at start
                    new_ftype = "." + new_ftype.replace(".", "")
                    if new_ftype in ftypes:
                        ftypes.remove(new_ftype)
                        _alter_qlinetext(btn, og_text, "🗙")
                    else:
                        ftypes.add(new_ftype)
                        _alter_qlinetext(btn, og_text, "✔")

            def _alter_qlinetext(btn, og_text, char):
                btn.setText(og_text + f" {char}")
                QTimer(self.ftype_entry).singleShot(2000, lambda: btn.setText(og_text))

            self.ftype_entry.setEnabled(False)
            self.ftypes_layout.addWidget(self.ftype_entry)
            original_text = self.main_btns.button(3).text()
            self.ftype_entry.returnPressed.connect(lambda: _add_ftype(self.button_results[original_text],
                                                                      self.ftype_entry.text(),
                                                                      self.main_btns.button(3),
                                                                      original_text))


class KeywordTable(NewTab):
    DEF_TABLE_DIM = (5, 2)
    WIDGET_POS = (2, 0, 1, 2)

    def __init__(self, main_ui, parent_tab, name):
        super().__init__(main_ui, parent_tab, name)
        self.table = QTableWidget()

        self._build_table()
        self._add_table_buttons()
        self._set_table_dim(*self.DEF_TABLE_DIM)

    def _set_table_dim(self, rows, columns):
        self.table.setRowCount(rows)
        self.table.setColumnCount(columns)
        self.table.clearContents()

        for i in range(1, columns + 1):
            # Header index starts at 0.
            self.table.setHorizontalHeaderItem(i - 1, QTableWidgetItem(str(i)))

    def _name_column(self, column):
        name_dir_prompt, dir_name = QInputDialog.getText(self.table, "Name your folder", "Folder name:")
        if dir_name:
            self.table.setHorizontalHeaderItem(column, QTableWidgetItem(f"{name_dir_prompt}"))

    def _mod_table(self, row_col, add_rem):
        options = {'row': {'add': lambda: self.table.setRowCount(self.table.rowCount() + 1),
                           'remove': lambda: self.table.setRowCount(
                               self.table.rowCount() - 1 if self.table.rowCount() > 1 else self.table.rowCount())},
                   'column': {'add': lambda: self.table.setColumnCount(self.table.columnCount() + 1),
                              'remove': lambda: self.table.setColumnCount(
                                  self.table.columnCount() - 1 if self.table.columnCount() > 1 else self.table.columnCount())}}
        if self.table.isEnabled():
            options[row_col][add_rem]()

    def _build_table(self):
        # Add table.
        table_holder = QHBoxLayout()
        self.main_box.setLayout(table_holder)
        table_holder.addWidget(self.table)

        header = self.table.horizontalHeader()
        header.sectionClicked.connect(lambda col: self._name_column(column=col))
        self.mtab_layout.addWidget(self.main_box, *self.WIDGET_POS)

    @property
    def contents(self):
        table_settings = defaultdict(list)
        for col in range(self.table.columnCount()):
            header = str(col + 1)
            if hasattr(self.table.horizontalHeaderItem(col), 'text'):
                header = self.table.horizontalHeaderItem(col).text()
            for row in range(self.table.rowCount()):
                # Result of item() set to keyword var.
                # Ignore empty cells or cells that were clicked but had no input.
                if keyword := self.table.item(row, col):
                    if keyword.text().strip() != "":
                        keyword = keyword.text()
                        if header != str(col + 1):
                            # If not default column number as header.
                            table_settings[header].append(keyword)
                        else:
                            table_settings['Ungrouped Keywords'].append(keyword)
        return table_settings

    def _add_table_buttons(self):
        # Add button groupbox.
        button_frame = QGroupBox("Adjust Table")
        button_layout = QVBoxLayout()
        button_frame.setLayout(button_layout)
        self.mtab_layout.addWidget(button_frame, 1, 0)

        # Add buttons.
        button_types = {'add_row': {'Widget': QPushButton('Add Row'),
                                    'fx': lambda: self._mod_table(row_col='row', add_rem='add')},
                        'rem_row': {'Widget': QPushButton('Remove Row'),
                                    'fx': lambda: self._mod_table(row_col='row', add_rem='remove')},
                        'add_col': {'Widget': QPushButton('Add Column'),
                                    'fx': lambda: self._mod_table(row_col='column', add_rem='add')},
                        'rem_col': {'Widget': QPushButton('Remove Column'),
                                    'fx': lambda: self._mod_table(row_col='column', add_rem='remove')},
                        'reset': {'Widget': QPushButton('Reset to Default'),
                                  'fx': lambda: (
                                      self._set_table_dim(*self.DEF_TABLE_DIM) if self.table.isEnabled() else None)}}

        for button in button_types.values():
            button_layout.addWidget(button['Widget'])
            button['Widget'].clicked.connect(button['fx'])
