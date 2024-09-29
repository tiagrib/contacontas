from PySide6 import QtCore, QtWidgets
import sys

class CCQT(QtCore.QObject):
    summaryPlotUpdated = QtCore.Signal(int)

    def __init__(self, cc):
        super().__init__()
        self.app = QtWidgets.QApplication(sys.argv)
        self.cc = cc