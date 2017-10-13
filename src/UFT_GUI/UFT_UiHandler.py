#!/usr/bin/env python
# encoding: utf-8

'''
Created on Nov 01, 2014
@author: mzfa
'''
import sys
import os
import re
from PyQt4 import QtCore, QtGui, QtSql
from UFT_GUI.UFT_Ui import Ui_Form as UFT_UiForm
from UFT.config import RESULT_DB, CONFIG_DB, RESOURCE, CONFIG_FILE
from UFT.backend import sync_config

BARCODE_PATTERN = re.compile(r'^(?P<SN>(?P<PN>AGIGA\d{4}-\d{3}\w{3})'
                             r'(?P<VV>\d{2})(?P<YY>[1-2][0-9])'
                             r'(?P<WW>[0-4][0-9]|5[0-3])'
                             r'(?P<ID>\d{8})-(?P<RR>\d{2}))$')


# class MyLineEdit(QtGui.QLineEdit):
# def __init__(self, parent=None):
#         super(MyLineEdit, self).__init__(parent)
#
#     def focusInEvent(self, event):
#         # print 'This widget is in focus'
#         self.clear()
#         QtGui.QLineEdit.focusInEvent(self,
#                                      QtGui.QFocusEvent(QtCore.QEvent.FocusIn))


class LoginDialog(QtGui.QDialog):
    def __init__(self, parent=None):
        QtGui.QDialog.__init__(self, parent)
        self.setWindowTitle(u'login')
        self.resize(300, 150)

        self.leName = QtGui.QLineEdit(self)
        self.leName.setPlaceholderText(u'user')

        self.lePassword = QtGui.QLineEdit(self)
        self.lePassword.setEchoMode(QtGui.QLineEdit.Password)
        self.lePassword.setPlaceholderText(u'password')

        self.pbLogin = QtGui.QPushButton(u'login', self)
        self.pbCancel = QtGui.QPushButton(u'cancel', self)

        self.pbLogin.clicked.connect(self.login)
        self.pbCancel.clicked.connect(self.reject)

        layout = QtGui.QVBoxLayout()
        layout.addWidget(self.leName)
        layout.addWidget(self.lePassword)

        spacerItem = QtGui.QSpacerItem(20, 48, QtGui.QSizePolicy.Minimum,
                                       QtGui.QSizePolicy.Expanding)
        layout.addItem(spacerItem)

        buttonLayout = QtGui.QHBoxLayout()
        spancerItem2 = QtGui.QSpacerItem(40, 20, QtGui.QSizePolicy.Expanding,
                                         QtGui.QSizePolicy.Minimum)
        buttonLayout.addItem(spancerItem2)
        buttonLayout.addWidget(self.pbLogin)
        buttonLayout.addWidget(self.pbCancel)

        layout.addLayout(buttonLayout)

        self.setLayout(layout)

    def login(self):
        print 'login'
        if self.leName.text() == 'cypress' and self.lePassword.text() == '123':
            self.accept()
        else:
            QtGui.QMessageBox.critical(self, u'error', u'password wrong')


class UFT_UiHandler(UFT_UiForm):
    def __init__(self, parent=None):
        UFT_UiForm.__init__(self)
        self.dut_image = None
        # sync config db from config xml
        sync_config("sqlite:///" + CONFIG_DB, CONFIG_FILE, direction="in")
        #
        # setup config db, view and model
        self.config_db = QtSql.QSqlDatabase.addDatabase("QSQLITE", "config")
        self.config_db.setDatabaseName(CONFIG_DB)
        result = self.config_db.open()
        if (not result):
            msgbox = QtGui.QMessageBox()
            msg = self.config_db.lastError().text()
            msgbox.critical(msgbox, "error", msg + " db=" + CONFIG_DB)
        self.config_tableView = QtGui.QTableView()
        # self.test_item_tableView already created in UI.
        self.config_model = QtSql.QSqlTableModel(db=self.config_db)
        self.test_item_model = QtSql.QSqlRelationalTableModel(db=self.config_db)
        self.test_item_model.setEditStrategy(
            QtSql.QSqlTableModel.OnManualSubmit)

        # setup log db, view and model
        self.log_db = QtSql.QSqlDatabase.addDatabase("QSQLITE", "log")
        self.log_db.setDatabaseName(RESULT_DB)
        result = self.log_db.open()
        if (not result):
            msgbox = QtGui.QMessageBox()
            msg = self.config_db.lastError().text()
            msgbox.critical(msgbox, "error", msg + " db=" + RESULT_DB)
        # self.log_tableView
        self.log_model = QtSql.QSqlTableModel(db=self.log_db)
        self.cycle_model = QtSql.QSqlRelationalTableModel(db=self.log_db)

    def setupWidget(self, wobj):
        wobj.setWindowIcon(QtGui.QIcon(QtGui.QPixmap(RESOURCE + "logo.png")))

        # setup configuration model
        self.config_model.setTable("configuration")
        self.test_item_model.setTable("test_item")
        self.test_item_model.setRelation(1, QtSql.QSqlRelation(
            "configuration", "id", u"partnumber"))

        # setup log model
        self.log_model.setTable("dut")
        self.cycle_model.setTable("cycle")
        self.cycle_model.setRelation(7, QtSql.QSqlRelation(
            "dut", "id", u"barcode, archived"))

        # set log view
        self.log_tableView.setModel(self.log_model)
        # self.log_tableView.resizeColumnsToContents()

        # update comboBox
        partnumber_list = []
        self.config_model.select()  # get data
        for row in range(self.config_model.rowCount()):
            index = self.config_model.index(row, 1)  # 1 for partnumber
            pn = self.config_model.data(index).toString()
            if (pn not in partnumber_list):
                partnumber_list.append(pn)
                self.partNum_comboBox.addItem(pn)

        # set configuration view
        self.revision_comboBox.setModel(self.config_model)
        self.revision_comboBox.setModelColumn(self.config_model.fieldIndex(
            "revision"))
        self.test_item_tableView.setModel(self.test_item_model)
        self.testItem_update()

    def auto_enable_disable_widgets(self, ch_is_alive):
        if ch_is_alive:
            self.start_pushButton.setDisabled(True)
            self.sn_lineEdit_1.setDisabled(True)
            self.sn_lineEdit_2.setDisabled(True)
            self.sn_lineEdit_3.setDisabled(True)
            self.sn_lineEdit_4.setDisabled(True)
            self.sn_lineEdit_5.setDisabled(True)
            self.sn_lineEdit_6.setDisabled(True)
            self.sn_lineEdit_7.setDisabled(True)
            self.sn_lineEdit_8.setDisabled(True)
            self.sn_lineEdit_9.setDisabled(True)
            self.sn_lineEdit_10.setDisabled(True)
            self.sn_lineEdit_11.setDisabled(True)
            self.sn_lineEdit_12.setDisabled(True)
            self.sn_lineEdit_13.setDisabled(True)
            self.sn_lineEdit_14.setDisabled(True)
            self.sn_lineEdit_15.setDisabled(True)
            self.sn_lineEdit_16.setDisabled(True)
            self.CablelineEdit_1.setDisabled(True)
            self.CablelineEdit_2.setDisabled(True)
            self.CablelineEdit_3.setDisabled(True)
            self.CablelineEdit_4.setDisabled(True)
            self.CablelineEdit_5.setDisabled(True)
            self.CablelineEdit_6.setDisabled(True)
            self.CablelineEdit_7.setDisabled(True)
            self.CablelineEdit_8.setDisabled(True)
            self.CablelineEdit_9.setDisabled(True)
            self.CablelineEdit_10.setDisabled(True)
            self.CablelineEdit_11.setDisabled(True)
            self.CablelineEdit_12.setDisabled(True)
            self.CablelineEdit_13.setDisabled(True)
            self.CablelineEdit_14.setDisabled(True)
            self.CablelineEdit_15.setDisabled(True)
            self.CablelineEdit_16.setDisabled(True)
            self.BatterylineEdit_1.setDisabled(True)
            self.BatterylineEdit_2.setDisabled(True)
            self.BatterylineEdit_3.setDisabled(True)
            self.BatterylineEdit_4.setDisabled(True)
            self.BatterylineEdit_5.setDisabled(True)
            self.BatterylineEdit_6.setDisabled(True)
            self.BatterylineEdit_7.setDisabled(True)
            self.BatterylineEdit_8.setDisabled(True)
            self.BatterylineEdit_9.setDisabled(True)
            self.BatterylineEdit_10.setDisabled(True)
            self.BatterylineEdit_11.setDisabled(True)
            self.BatterylineEdit_12.setDisabled(True)
            self.BatterylineEdit_13.setDisabled(True)
            self.BatterylineEdit_14.setDisabled(True)
            self.BatterylineEdit_15.setDisabled(True)
            self.BatterylineEdit_16.setDisabled(True)
            self.Mode4in1.setDisabled(True)
        else:
            self.start_pushButton.setEnabled(True)
            self.sn_lineEdit_1.setEnabled(True)
            self.sn_lineEdit_2.setEnabled(True)
            self.sn_lineEdit_3.setEnabled(True)
            self.sn_lineEdit_4.setEnabled(True)
            self.sn_lineEdit_5.setEnabled(True)
            self.sn_lineEdit_6.setEnabled(True)
            self.sn_lineEdit_7.setEnabled(True)
            self.sn_lineEdit_8.setEnabled(True)
            self.sn_lineEdit_9.setEnabled(True)
            self.sn_lineEdit_10.setEnabled(True)
            self.sn_lineEdit_11.setEnabled(True)
            self.sn_lineEdit_12.setEnabled(True)
            self.sn_lineEdit_13.setEnabled(True)
            self.sn_lineEdit_14.setEnabled(True)
            self.sn_lineEdit_15.setEnabled(True)
            self.sn_lineEdit_16.setEnabled(True)
            self.CablelineEdit_1.setEnabled(True)
            self.CablelineEdit_2.setEnabled(True)
            self.CablelineEdit_3.setEnabled(True)
            self.CablelineEdit_4.setEnabled(True)
            self.CablelineEdit_5.setEnabled(True)
            self.CablelineEdit_6.setEnabled(True)
            self.CablelineEdit_7.setEnabled(True)
            self.CablelineEdit_8.setEnabled(True)
            self.CablelineEdit_9.setEnabled(True)
            self.CablelineEdit_10.setEnabled(True)
            self.CablelineEdit_11.setEnabled(True)
            self.CablelineEdit_12.setEnabled(True)
            self.CablelineEdit_13.setEnabled(True)
            self.CablelineEdit_14.setEnabled(True)
            self.CablelineEdit_15.setEnabled(True)
            self.CablelineEdit_16.setEnabled(True)
            self.BatterylineEdit_1.setEnabled(True)
            self.BatterylineEdit_2.setEnabled(True)
            self.BatterylineEdit_3.setEnabled(True)
            self.BatterylineEdit_4.setEnabled(True)
            self.BatterylineEdit_5.setEnabled(True)
            self.BatterylineEdit_6.setEnabled(True)
            self.BatterylineEdit_7.setEnabled(True)
            self.BatterylineEdit_8.setEnabled(True)
            self.BatterylineEdit_9.setEnabled(True)
            self.BatterylineEdit_10.setEnabled(True)
            self.BatterylineEdit_11.setEnabled(True)
            self.BatterylineEdit_12.setEnabled(True)
            self.BatterylineEdit_13.setEnabled(True)
            self.BatterylineEdit_14.setEnabled(True)
            self.BatterylineEdit_15.setEnabled(True)
            self.BatterylineEdit_16.setEnabled(True)
            self.Mode4in1.setEnabled(True)
            self.sn_lineEdit_1.selectAll()
            self.sn_lineEdit_1.setFocus()

    def append_format_data(self, data):
        if data:
            self.info_textBrowser.append(data)
            # self.info_textBrowser.moveCursor(QtGui.QTextCursor.End)
        else:
            pass

    def set_status_text(self, slotnum, status):
        status_list = ["Idle", "Pass", "Fail", "Charging", "Discharging", "Self_Discharging", "Cap_Measuring"]
        label = [self.label_1, self.label_2, self.label_3, self.label_4, self.label_5, self.label_6, self.label_7, self.label_8,
                 self.label_9, self.label_10, self.label_11, self.label_12, self.label_13, self.label_14, self.label_15, self.label_16]
        color_list = ["background-color: wheat",
                      "background-color: green",
                      "background-color: red",
                      "background-color: yellow",
                      "background-color: yellow",
                      "background-color: yellow",
                      "background-color: yellow"]
        label[slotnum].setText(status_list[status])
        label[slotnum].setStyleSheet(color_list[status])

    def barcodes(self):
        barcodes = [str(self.sn_lineEdit_1.text()),
                    str(self.sn_lineEdit_2.text()),
                    str(self.sn_lineEdit_3.text()),
                    str(self.sn_lineEdit_4.text()),
                    str(self.sn_lineEdit_5.text()),
                    str(self.sn_lineEdit_6.text()),
                    str(self.sn_lineEdit_7.text()),
                    str(self.sn_lineEdit_8.text()),
                    str(self.sn_lineEdit_9.text()),
                    str(self.sn_lineEdit_10.text()),
                    str(self.sn_lineEdit_11.text()),
                    str(self.sn_lineEdit_12.text()),
                    str(self.sn_lineEdit_13.text()),
                    str(self.sn_lineEdit_14.text()),
                    str(self.sn_lineEdit_15.text()),
                    str(self.sn_lineEdit_16.text())]
        for i in barcodes:
            if not i:
                i = ""
        return barcodes

    def InMode4in1(self):
        return bool(self.Mode4in1.checkState())

    def cabel_barcodes(self):
        cabel_barcodes = [str(self.CablelineEdit_1.text()),
                          str(self.CablelineEdit_2.text()),
                          str(self.CablelineEdit_3.text()),
                          str(self.CablelineEdit_4.text()),
                          str(self.CablelineEdit_5.text()),
                          str(self.CablelineEdit_6.text()),
                          str(self.CablelineEdit_7.text()),
                          str(self.CablelineEdit_8.text()),
                          str(self.CablelineEdit_9.text()),
                          str(self.CablelineEdit_10.text()),
                          str(self.CablelineEdit_11.text()),
                          str(self.CablelineEdit_12.text()),
                          str(self.CablelineEdit_13.text()),
                          str(self.CablelineEdit_14.text()),
                          str(self.CablelineEdit_15.text()),
                          str(self.CablelineEdit_16.text())]
        for i in cabel_barcodes:
            if not i:
                i = ""
        return cabel_barcodes

    def capacitor_barcodes(self):
        capacitor_barcodes = [str(self.BatterylineEdit_1.text()),
                          str(self.BatterylineEdit_2.text()),
                          str(self.BatterylineEdit_3.text()),
                          str(self.BatterylineEdit_4.text()),
                          str(self.BatterylineEdit_5.text()),
                          str(self.BatterylineEdit_6.text()),
                          str(self.BatterylineEdit_7.text()),
                          str(self.BatterylineEdit_8.text()),
                          str(self.BatterylineEdit_9.text()),
                          str(self.BatterylineEdit_10.text()),
                          str(self.BatterylineEdit_11.text()),
                          str(self.BatterylineEdit_12.text()),
                          str(self.BatterylineEdit_13.text()),
                          str(self.BatterylineEdit_14.text()),
                          str(self.BatterylineEdit_15.text()),
                          str(self.BatterylineEdit_16.text())]
        for i in capacitor_barcodes:
            if not i:
                i = ""
        return capacitor_barcodes

    def click_on_TabCable(self):
        self.CablelineEdit_1.selectAll()
        self.CablelineEdit_1.setFocus()

    def click_on_TabBattery(self):
        self.BatterylineEdit_1.selectAll()
        self.BatterylineEdit_1.setFocus()

    def show_image(self):
        barcodes = self.barcodes()
        image_labels = [self.imageLabel1,
                        self.imageLabel2,
                        self.imageLabel3,
                        self.imageLabel4]
        for i in range(len(barcodes)):
            r = BARCODE_PATTERN.search(barcodes[i])
            if barcodes[i] == "":
                image_labels[i].setText("")
            elif r:
                barcode_dict = r.groupdict()
                partnumber = barcode_dict["PN"]
                image_file = RESOURCE + partnumber + ".jpg"
                if os.path.isfile(image_file):
                    my_pixmap = QtGui.QPixmap(image_file)
                    my_scaled_pixmap = my_pixmap.scaled(
                        image_labels[i].maximumSize(),
                        QtCore.Qt.KeepAspectRatio)
                    image_labels[i].setPixmap(my_scaled_pixmap)
                else:
                    image_labels[i].setText("No dut image found")
            else:
                image_labels[i].setText("Invalid Serial Number")

    def comboBox_update(self):
        current_pn = self.partNum_comboBox.currentText()
        self.config_model.setFilter("PARTNUMBER='" + current_pn + "'")
        self.config_model.select()
        descrip = self.config_model.record(0).value('DESCRIPTION').toString()
        self.descriptionLabel.setText(descrip)

    def update_table(self):
        filter_combo = "PARTNUMBER = '" + self.partNum_comboBox.currentText() \
                       + "' AND REVISION = '" \
                       + self.revision_comboBox.currentText() + "'"
        self.test_item_model.setFilter(filter_combo)
        self.test_item_model.select()
        self.test_item_tableView.hideColumn(0)
        self.test_item_tableView.resizeColumnsToContents()

    def testItem_update(self):
        self.comboBox_update()
        self.update_table()

    def submit_config(self):
        result = self.test_item_model.submitAll()
        msg = QtGui.QMessageBox()
        if result:
            sync_config("sqlite:///" + CONFIG_DB, CONFIG_FILE, direction="out")
            msg.setText("Update Success!")
            msg.exec_()
        else:
            error_msg = self.test_item_model.lastError().text()
            msg.critical(msg, "error", error_msg)

    def search(self):
        if self.search_lineEdit.text():
            self.search_result_label.setText("")
            barcode = str(self.search_lineEdit.text())

            self.log_model.record().indexOf("id")
            self.log_model.setFilter("barcode = '" + barcode + "'")
            self.log_model.select()

            if self.log_model.rowCount() == 0:
                self.search_result_label.setText("No Item Found")

            self.log_tableView.resizeColumnsToContents()

    def push_multi_mpls(self):
        mpls = [self.mplwidget,
                self.mplwidget_2,
                self.mplwidget_3,
                self.mplwidget_4]
        item = ""
        for i in self.buttonGroup.buttons():
            if i.isChecked():
                item = i.text()

        for i, barcode in enumerate(self.barcodes()):
            if barcode == "":
                continue
            time = []
            data = []
            mpls[i].setFocus()

            self.cycle_model.setFilter(
                "barcode = '" + barcode + "' AND archived = 0")
            self.cycle_model.select()
            for j in range(self.cycle_model.rowCount()):
                record = self.cycle_model.record(j)
                time.append(int(record.value("counter").toString()))
                data.append(float(record.value(item).toString()))
            self.plot(mpls[i], time, data)

    def plot(self, mpl_widget, t, d):
        mpl_widget.axes.plot(t, d)
        mpl_widget.draw()

    def print_time(self, sec):
        min = sec // 60
        sec -= min * 60
        sec = str(sec) if sec >= 10 else "0" + str(sec)
        self.lcdNumber.display(str(min) + ":" + sec)

    def config_edit_toggle(self, toggle_bool):
        if not toggle_bool:
            self.test_item_tableView.setEditTriggers(
                QtGui.QAbstractItemView.NoEditTriggers)
        else:
            dialog = LoginDialog()
            if dialog.exec_():
                self.checkBox.setChecked(True)
                self.test_item_tableView.setEditTriggers(
                    QtGui.QAbstractItemView.DoubleClicked)
            else:
                self.checkBox.setChecked(False)

                # def login(self):
                # dialog = LoginDialog()
                # if dialog.exec_():
                #         self.checkBox.setChecked(True)
                #     else:
                #         self.checkBox.setChecked(False)


if __name__ == "__main__":
    a = QtGui.QApplication(sys.argv)
    Form = QtGui.QWidget()
    w = UFT_UiHandler()
    w.setupUi(Form)
    w.setupWidget(Form)
    w.show_image("../res/icons/despicableMe.jpg")
    Form.show()
    sys.exit(a.exec_())
