from PyQt5.QtWidgets import *
from PyQt5.QtCore import Qt, QObject, QThread, pyqtSignal


class StatsUI(QWidget):
    def __init__(self):
        super().__init__()
        self.stats_layout = QGridLayout()
        self.setLayout(self.stats_layout)

        self.show()
    # Should close if new sort started or remain in-focus until closed.
