from PyQt5.QtWidgets import *
from PyQt5.QtCore import pyqtSlot

from gui_help import HelpCateg, HelpSettings, HelpLogging


class AboutUI(QGridLayout):
    ABOUT_DIM = (400, 300)
    ABOUT_TITLE = "About"

    def __init__(self):
        super().__init__()
        self.window = QWidget()

        self._about_setup()

    def _about_setup(self):
        self.window.setWindowTitle(self.ABOUT_TITLE)
        self.window.setFixedSize(*self.ABOUT_DIM)

        self.addWidget(QLabel("Hi! This is a file sorter built by Keith Oshima in Python\n"
                              "using the PyQt library. \n\n"
                              "I decided to build something like this after looking\n"
                              "at the T: drive and wondering if there was a quicker\n"
                              "way of sorting through the files. My first attempts were\n"
                              "not nearly as robust as this final version. Hope this helps!\n"
                              ))
        self.window.setLayout(self)

    def _display(self):
        self.window.show()


class OptionsUI(QVBoxLayout):
    OPTIONS_DIM = (400, 300)
    OPTIONS_TITLE = "Options"
    ALL_OPTIONS = {"Sort in-place": {'var_name': 'in_place',
                                     'fx': lambda parent, btn: setattr(parent, 'in_place', btn.isChecked())},
                   "Log sort process": {'var_name': 'log_sort',
                                        'fx': lambda parent, btn: setattr(parent, 'log_sort', btn.isChecked())},
                   "Show folder data": {'var_name': 'show_data',
                                        'fx': lambda parent, btn: setattr(parent, 'show_data', btn.isChecked())}}

    def __init__(self, parent):
        super().__init__()
        self.parent = parent
        self.window = QWidget()
        self.window_layout = QGridLayout()
        self.buttons = QButtonGroup()

        self._options_setup()
        self._button_setup()

    def _options_setup(self):
        self.window.setWindowTitle(self.OPTIONS_TITLE)
        self.window.setFixedSize(*self.OPTIONS_DIM)
        self.window.setLayout(self.window_layout)

        options_box = QGroupBox("Additional Options")
        options_box.setLayout(self)
        self.window_layout.addWidget(options_box)

    def _button_setup(self):
        self.buttons.setExclusive(False)
        for option, info in self.ALL_OPTIONS.items():
            temp_btn = QCheckBox(option)
            temp_btn.setChecked(getattr(self.parent, info['var_name']))
            self.buttons.addButton(temp_btn)
            self.addWidget(temp_btn)
        self.buttons.buttonClicked.connect(lambda btn: self.ALL_OPTIONS[btn.text()]['fx'](self.parent, btn))

    @pyqtSlot()
    def _display(self):
        self.window.show()


class MenuUI(QMenuBar):
    MENU_ITEMS = {'General': {'Select Folder': '_choose_dir',
                              'Start Sort': '_prep_sort',
                              'Unpack Folder': '_start_unpack',
                              'Ignore Folders': '_ignore_dirs',
                              'View Current Folder': '_open_file_loc',
                              'Quit': '_quit'},
                  'Options': lambda option_obj: getattr(option_obj, '_display'),
                  'Help': {'On Sort Categories': lambda help_obj: getattr(help_obj, '_display'),
                           'On Additional Settings': lambda help_obj: getattr(help_obj, '_display'),
                           'On Logging': lambda help_obj: getattr(help_obj, '_display')},
                  'About': lambda about_obj: getattr(about_obj, '_display')}
    MENU_POS = (0, 0, 1, 5)

    def __init__(self, parent):
        super().__init__()
        self.parent = parent
        self.menu_assoc_objects = {'Options': OptionsUI(self.parent),
                                   'On Sort Categories': HelpCateg(),
                                   'On Additional Settings': HelpSettings(),
                                   'On Logging': HelpLogging(),
                                   'About': AboutUI()}

    def _fill_menubar(self):
        for categ, submenus in self.MENU_ITEMS.items():
            if not isinstance(submenus, dict):
                func = submenus
                self.addAction(categ).triggered.connect(func(self.menu_assoc_objects[categ]))
                continue
            menu_obj = self.addMenu(categ)
            for submenu, fx in submenus.items():
                func = getattr(self.parent, fx) if isinstance(fx, str) else fx(self.menu_assoc_objects[submenu])
                submenu_action = menu_obj.addAction(submenu)
                submenu_action.triggered.connect(func)
