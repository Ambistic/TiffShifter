import sys
import os

from PySide2.QtUiTools import QUiLoader
from PySide2.QtWidgets import QApplication, QPushButton, QLineEdit, \
        QLabel, QAction, QFileDialog, QSlider, QProgressBar, QSpinBox
from PySide2.QtCore import QFile, QObject, Qt
from PySide2 import QtGui
from threading import RLock

from Stack import Tif

class Interface(QObject):

    def __init__(self, ui_file="main.ui", parent=None):
        self.__stack = None
        super(Interface, self).__init__(parent)
        ui_file = QFile(ui_file)
        ui_file.open(QFile.ReadOnly)

        loader = QUiLoader()
        self.window = loader.load(ui_file)
        ui_file.close()

        self.open = self.window.findChild(QAction, "actionOpen")
        self.open.triggered.connect(self._open)

        self.save = self.window.findChild(QAction, "actionSave")
        self.save.triggered.connect(self._save)

        self.slider_c = self.window.findChild(QSlider, "slider_c")
        self.slider_z = self.window.findChild(QSlider, "slider_z")
        self.slider_t = self.window.findChild(QSlider, "slider_t")

        self.label_c = self.window.findChild(QLabel, "label_c")
        self.label_z = self.window.findChild(QLabel, "label_z")
        self.label_t = self.window.findChild(QLabel, "label_t")

        self.slider_c.sliderMoved.connect(self.update_c)
        self.slider_z.sliderMoved.connect(self.update_z)
        self.slider_t.sliderMoved.connect(self.update_t)

        self.__image = self.window.findChild(QLabel, "main_image")
        self._access = RLock()

        # self.line = self.window.findChild(QLineEdit, 'lineEdit')
        self.up = self.window.findChild(QPushButton, "up")
        self.down = self.window.findChild(QPushButton, "down")
        self.right = self.window.findChild(QPushButton, "right")
        self.left = self.window.findChild(QPushButton, "left")
        self.prev = self.window.findChild(QPushButton, "prev")
        self.next = self.window.findChild(QPushButton, "next")
        self.runner = self.window.findChild(QPushButton, "run")

        self.up.clicked.connect(self.update_up)
        self.down.clicked.connect(self.update_down)
        self.right.clicked.connect(self.update_right)
        self.left.clicked.connect(self.update_left)
        self.prev.clicked.connect(self.update_prev)
        self.next.clicked.connect(self.update_next)
        self.runner.clicked.connect(self.run)

        self.shift_range = self.window.findChild(QSpinBox, "spinBox")
        self.shift_range.valueChanged.connect(self.change_shift_range)

        self.progress = self.window.findChild(QProgressBar, "run_progress")
        self.label_shift = self.window.findChild(QLabel, "shift_label")
        # btn = self.window.findChild(QPushButton, 'pushButton')
        # btn.clicked.connect(self.ok_handler)
        self._open()
        self.window.show()

    def change_shift_range(self, value):
        with self._access:
            if self.__stack is None:
                return
            self.__stack.set_shift_range(value)

    def get_modifier_value(self):
        modifiers = QApplication.keyboardModifiers()
        if modifiers == Qt.ShiftModifier:
            return 5
        elif modifiers == Qt.ControlModifier:
            return 20
        else:
            return 1

    def _open(self):
        fileName = QFileDialog.getOpenFileName(self.window, "Open File",
                ".",
                "Images (*.tif *.tiff)")

        if not os.path.isfile(fileName[0]):
            return

        self.__stack = Tif(fileName[0])
        # reset sliders and labels
        c, z, t = self.get_slider_values()
        self._set_sliders(c, z, t)
        self._set_labels(c, z, t)
        with self._access:
            self.__stack.set_shift_range(self.shift_range.value())

        self.show_image()

    def _set_sliders(self, c, z, t):
        self.slider_c.setMaximum(c)
        self.slider_c.setValue(1)
        self.slider_z.setMaximum(z)
        self.slider_z.setValue(1)
        self.slider_t.setMaximum(t)
        self.slider_t.setValue(1)

    def _set_labels(self, c, z, t):
        self.label_c.setText("1 / " + str(c))
        self.label_z.setText("1 / " + str(z))
        self.label_t.setText("1 / " + str(t))

    def update_c(self, value):
        self.__stack.set_index(c=value - 1)
        self.label_c.setText(str(value) + " / "
                + str(self.slider_c.maximum()))
        self.show_image()

    def update_z(self, value):
        self.__stack.set_index(z=value - 1)
        self.label_z.setText(str(value) + " / "
                + str(self.slider_z.maximum()))
        self.show_image()

    def update_t(self, value):
        self.__stack.set_index(t=value - 1)
        self.label_t.setText(str(value) + " / "
                + str(self.slider_t.maximum()))
        self.show_image()

    def _save(self):
        self.__stack.save()

    def show_image(self):
        with self._access:
            if self.__stack is None:
                return
            # fileName = "/home/nathan/Bureau/ENS/Thèse/TiffShifter/transfer_" \
            #     "878689_files_f4dc9905/BB431_acq1-35_B7-S9gfp_zp2.tif"
            # self.__stack = Tif(fileName)


            img_file = self.__stack.get_image_file()

            pixmap = img_file
            # img = QtGui.QImage(img_file.tobytes(), *img_file.size,
            #         QtGui.QImage.Format_Indexed8)
            # pixmap = QtGui.QPixmap.fromImage(img)
            # pixmap = QtGui.QPixmap(img_file)
            self.__image.setPixmap(pixmap)
            self.__image.adjustSize()
            current_shift = self.__stack.get_current_shift()
            self.label_shift.setText(str(current_shift[0]) + ", "
                + str(current_shift[1]))



    def get_slider_values(self):
        return (self.__stack.get_channels(),
                self.__stack.get_z(),
                self.__stack.get_t())


    def update_right(self, event):
        value = self.get_modifier_value()
        self.__stack.delta_shift((value, 0))
        self.show_image()

    def update_left(self, event):
        value = self.get_modifier_value()
        self.__stack.delta_shift((-value, 0))
        self.show_image()

    def update_up(self, event):
        value = self.get_modifier_value()
        self.__stack.delta_shift((0, -value))
        self.show_image()

    def update_down(self, event):
        value = self.get_modifier_value()
        self.__stack.delta_shift((0, value))
        self.show_image()

    def update_next(self, value):
        value = self.slider_t.value() + 1
        if value < 1 or value > self.slider_t.maximum():
            return
        self.slider_t.setValue(value)
        self.__stack.set_index(t=value - 1)
        self.label_t.setText(str(value) + " / "
                + str(self.slider_t.maximum()))
        self.show_image()

    def update_prev(self, value):
        value = self.slider_t.value() - 1
        if value < 1 or value > self.slider_t.maximum():
            return
        self.slider_t.setValue(value)
        self.__stack.set_index(t=value - 1)
        self.label_t.setText(str(value) + " / "
                + str(self.slider_t.maximum()))
        self.show_image()

    def run(self, value):
        self.progress.setValue(0)
        self.__stack.run_from_here()
        self.progress.setValue(100)
