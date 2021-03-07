from PyQt5.QtWidgets import *
from PyQt5.QtCore import Qt, QObject, QThread, pyqtSignal
import sys
import os
from collections import OrderedDict

from main import FileSort, Tools
from gui_widgets import SettingsList, KeywordTable, FileTypeButtons, DateButtons
from gui_menu import MenuUI
from gui_multidir import getExistingDirectories


# noinspection PyProtectedMember
class SorterUI(QMainWindow, FileSort):
    UI_DIM = (600, 600)
    UI_TITLE = "File Sorter"

    def __init__(self):
        super().__init__()

        # Tabs
        self.main_tab = QTabWidget()
        self.tabs = {}

        # Sort Parameters and Additional Settings
        self.sort_settings = OrderedDict()
        self.ignored_dirs = []
        self.in_place = False
        self.show_data = True
        self.log_sort = True

        # Main window or frame for all child widgets. vvv
        self.central_widg = QWidget()
        self.main_layout = QGridLayout()
        self.menu = MenuUI(parent=self)

        # Displayed settings list.
        # Show current dir.
        self.displayed_settings = SettingsList()
        SettingsList._add_selected_dir(self.displayed_settings, os.getcwd())

    def _display_ui(self):
        self.setWindowTitle(self.UI_TITLE)
        self.setFixedSize(*self.UI_DIM)
        self.setCentralWidget(self.central_widg)
        self.central_widg.setLayout(self.main_layout)

        self._menu_setup()
        self._button_setup()
        self._create_settings_box()
        self._tab_setup()
        self.show()

    def _menu_setup(self):
        self.menu._fill_menubar()
        self.main_layout.addWidget(self.menu, *self.menu.MENU_POS)

    def _button_setup(self):
        buttons = {'start_btn': {'Widget': QPushButton('Sort!'), 'Position': (5, 0),
                                 'fx': self._prep_sort},
                   'select_dir_btn': {'Widget': QPushButton('Select Folder'), 'Position': (1, 0, 1, 3),
                                      'fx': self._choose_dir},
                   'file_location_btn': {'Widget': QPushButton('Open File Location'), 'Position': (1, 3),
                                         'fx': self._open_file_loc},
                   'unpack_folder_btn': {'Widget': QPushButton('Unpack Folder Contents'), 'Position': (5, 1),
                                         'fx': self._start_unpack},
                   'ignore_dirs_btn': {'Widget': QPushButton('Ignore Folders'), 'Position': (5, 2, 1, 2),
                                       'fx': self._ignore_dirs}}
        for button in buttons.values():
            self.main_layout.addWidget(button['Widget'], *button['Position'])
            button['Widget'].clicked.connect(button['fx'])

    def _tab_setup(self):
        self.main_layout.addWidget(self.main_tab, 3, 1, 1, 3)

        # Create NewTab Instances for each sort type.
        # Need to pass self to NewTab to allow use of confirm_settings function.
        tab_types = {'Date': DateButtons, 'File Type': FileTypeButtons, 'Keyword': KeywordTable}
        self.tabs = {name: tab_cls(self, self.main_tab, name) for name, tab_cls in tab_types.items()}

    def _create_settings_box(self):
        # Group box for sort_settings
        settings_box = QGroupBox("Confirmed Settings")
        self.main_layout.addWidget(settings_box, 3, 0)

        settings_frame = QGridLayout()
        settings_box.setLayout(settings_frame)
        settings_frame.addWidget(self.displayed_settings)

    def _open_file_loc(self):
        if self.path:
            os.startfile(self.path)
        else:
            os.startfile(os.getcwd())

    def _choose_dir(self):
        file_prompt = QFileDialog()
        file_prompt.setWindowTitle("Select a folder to sort.")
        file_prompt.setFileMode(QFileDialog.Directory)
        if file_prompt.exec_():
            self.path = file_prompt.selectedFiles()[0]
            SettingsList._add_selected_dir(self.displayed_settings, self.path)

    def _ignore_dirs(self):
        file_prompt = getExistingDirectories()
        if file_prompt.exec_():
            self.ignored_dirs = file_prompt.selectedFiles()

        print(self.ignored_dirs)
        # Should be absolute paths.

    def _prep_sort(self):
        # If no path given, default to a path.
        if self.path is None:
            self.path = os.path.join(os.getcwd(), 'Microscope Stuff')

        # Message before sort.
        sort_msg = QMessageBox(QMessageBox.Information,
                               f"Notice: Begin Sort?",
                               f"Check settings before beginning. \n"
                               f"Current directory: {self.path}",
                               QMessageBox.Ok | QMessageBox.Cancel)
        sort_msg.setDefaultButton(QMessageBox.Ok)
        if sort_msg.exec_() == QMessageBox.Cancel:
            return

        # Set default empty list for ignored dirs if none selected.
        # Stop sort if no settings given.
        if self.ignored_dirs is None:
            self.ignored_dirs = []
        if len(self.sort_settings) == 0:
            return QMessageBox(QMessageBox.Warning, "Error: No Settings", "Unable to sort without settings.").exec_()

        max_val = Tools.get_file_count(self.path, self.ignored_dirs)

        # Making instance of class allows to remain in scope. Otherwise, thread destroyed after end of code block.
        self.sec_thread = QThread()

        sort_prog = FuncProgress(desc=("Sort Progress", "Sort in progress..."),
                                 thread=self.sec_thread,
                                 sorter_obj=self,
                                 maximum=max_val)

        sort_prog._start_func(sort_settings=self.sort_settings, ignore=self.ignored_dirs,
                              in_place=self.in_place, show_data=self.show_data, log_sort=self.log_sort)

    def _start_unpack(self):
        if self.path is None:
            self.path = os.path.join(os.getcwd(), 'Microscope Stuff')

        unpack_msg = QMessageBox(QMessageBox.Warning,
                                 "Warning: Begin Unpack?",
                                 "Moves ALL nested files into current directory and DELETES ALL directories.\n"
                                 f"Current directory: {self.path}",
                                 QMessageBox.Ok | QMessageBox.Cancel)
        unpack_msg.setDefaultButton(QMessageBox.Ok)
        if unpack_msg.exec_() == QMessageBox.Cancel:
            return

        self.unpack_folders(dest=self.path, ignore=self.ignored_dirs)
        QMessageBox(QMessageBox.Information, "Notice: Unpack Completed", "Folder was unpacked successfully.").exec_()

    def _end_sort(self, num):
        # Messages need to be in main thread to work.
        self.sec_thread.exit()
        if num == 1:
            QMessageBox(QMessageBox.Information, "Notice: Sort Shutdown", "Sort was canceled prematurely.").exec_()
        else:
            QMessageBox(QMessageBox.Information, "Notice: Sort Completed", "Folder was successfully sorted.").exec_()

    def closeEvent(self, event):
        # Overwrite QWidget closeEvent.
        self._quit()

    @staticmethod
    def _quit():
        sys.exit()


class FuncProgress(QObject):
    # Cannot be instance variables made after initializing.
    progress_sig, fin_sig = pyqtSignal(int), pyqtSignal(int)

    # func has to emit a progress signal and a finished signal
    def __init__(self, desc, thread, sorter_obj, maximum):
        super().__init__()
        (self.title, self.desc) = desc
        self.prog_window = QProgressDialog(self.desc, "Cancel", 0, maximum)
        self._setup_prog_bar()

        self.sorter_obj = sorter_obj
        self.sorter_func = getattr(sorter_obj, 'sort_files')
        self.thread = thread
        self.moveToThread(self.thread)

        self.progress_sig.connect(self.prog_window.setValue)
        self.fin_sig.connect(lambda num: self.sorter_obj._end_sort(num))

    def _setup_prog_bar(self):
        self.prog_window.setWindowModality(Qt.WindowModal)
        self.prog_window.setWindowTitle(self.title)
        self.prog_window.canceled.connect(lambda: setattr(self.sorter_obj, '_shutdown', 1))
        self.prog_window.setMinimumDuration(0)
        self.prog_window.show()

    def _start_func(self, *args, **kwargs):
        kwargs['progress_sig'], kwargs['fin_sig'] = self.progress_sig, self.fin_sig
        self.thread.started.connect(lambda: self.sorter_func(*args, **kwargs))

        # Starting thread starts func.
        self.thread.start()


if __name__ == "__main__":
    # Create application object
    pysorter = QApplication([])
    sorter_ui = SorterUI()
    sorter_ui._display_ui()
    # Execute application event loop
    sys.exit(pysorter.exec())
