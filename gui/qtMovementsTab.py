from PySide6 import QtCore


class MovementsModel(QtCore.QAbstractTableModel):
    def __init__(self, data):
        super().__init__()
        self._data = data

    def rowCount(self, index, parent=QtCore.QModelIndex()):
        return len(self._data)

    def columnCount(self, index, parent=QtCore.QModelIndex()):
        return len(self._data[0]) if self._data else 0

    def data(self, index, role=QtCore.Qt.DisplayRole):
        if role == QtCore.Qt.DisplayRole:
            return self._data[index.row()][index.column()]
        return None

    def roleNames(self):
        roles = {
            QtCore.Qt.UserRole + 1: b"stringRole1",
            QtCore.Qt.UserRole + 2: b"stringRole2",
            QtCore.Qt.UserRole + 3: b"dateRole",
            QtCore.Qt.UserRole + 4: b"stringRole3",
            QtCore.Qt.UserRole + 5: b"boolRole",
            QtCore.Qt.UserRole + 6: b"floatRole",
            QtCore.Qt.UserRole + 7: b"stringRole4",
        }
        return roles

    def updateData(self, new_data):
        self.beginResetModel()
        self._data = new_data
        self.endResetModel()


class MovementsBackend(QtCore.QObject):
    accountsModelChanged = QtCore.Signal()
    tagsModelChanged = QtCore.Signal()
    movementsModelChanged = QtCore.Signal()

    def __init__(self, parent=None, cc=None):
        super().__init__(parent)

        self.cc = cc
        self._accountsModel = QtCore.QStringListModel(["<ANY>", *self.cc.get_bank_accounts()])
        self._tagsModel = QtCore.QStringListModel(self.cc.data.all_tags)
        self._maxDateValue = len(self.cc.months) - 1
        self._movementsModel = MovementsModel([])  # Initialize with empty data
        self.accountsModelChanged.emit()

    def setAccountsModelItems(self, items):
        self._accountsModel.setStringList(items)
        self.accountsModelChanged.emit()

    @QtCore.Property(QtCore.QObject, constant=True)
    def accountsModel(self):
        return self._accountsModel

    @QtCore.Property(QtCore.QObject, notify=tagsModelChanged)
    def tagsModel(self):
        return self._tagsModel

    @QtCore.Property(QtCore.QObject, notify=movementsModelChanged)
    def movementsModel(self):
        return self._movementsModel

    @QtCore.Property(int)
    def maxDateValue(self):
        return self._maxDateValue

    @QtCore.Slot()
    def setNonInternalFilter(self):
        # Implement filter logic
        self.updateMovements()

    @QtCore.Slot()
    def setInternalOnlyFilter(self):
        # Implement filter logic
        self.updateMovements()

    @QtCore.Slot()
    def setAllFilter(self):
        # Implement filter logic
        self.updateMovements()

    @QtCore.Slot(int)
    def setfilterByDate(self, value):
        print(value)

    @QtCore.Slot(int, result=str)
    def getMonthStrByIndex(self, value):
        s = self.cc.months[value]
        if not isinstance(s, str):
            s = f"{s[0]}/{s[1]}"
        return s

    @QtCore.Slot()
    def updateMovements(self):
        # Implement logic to update movements based on filters
        # Example: self._movementsModel = MovementsModel(filtered_data)
        it = self.cc.data.m.itertuples()
        self._movementsModel.updateData([[i.bank, i.account, i.date, i.tags, i.internal, i.value, i.description] for i in it])
        # self.movementsModelChanged.emit()
