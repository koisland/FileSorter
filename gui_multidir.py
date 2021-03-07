# https://stackoverflow.com/questions/18707261/how-to-select-multiple-directories-with-kfiledialog
# Germar Solution taken from JohannesMunk

from PyQt5.QtWidgets import (QFileDialog, QAbstractItemView, QListView,
                             QTreeView)


class getExistingDirectories(QFileDialog):
    def __init__(self, *args):
        super(getExistingDirectories, self).__init__(*args)
        self.setOption(self.DontUseNativeDialog, True)
        self.setFileMode(self.Directory)
        self.setOption(self.ShowDirsOnly, True)
        self.findChildren(QListView)[0].setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.findChildren(QTreeView)[0].setSelectionMode(QAbstractItemView.ExtendedSelection)
