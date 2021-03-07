from PyQt5.QtWidgets import *
from PyQt5.QtCore import pyqtSlot


class HelpUI:
    pass


class HelpCateg(HelpUI):
    def __int__(self):
        pass

    def _display(self):
        print('categ')


class HelpSettings(HelpUI):
    def __int__(self):
        pass

    def _display(self):
        print('settings')


class HelpLogging(HelpUI):
    def __int__(self):
        pass

    def _display(self):
        print('logging')
