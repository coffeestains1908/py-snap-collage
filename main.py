import sys
import ctypes
import mss
import mss.tools
from PIL import Image
from PIL.ImageQt import ImageQt
import pyscreenshot as ImageGrab
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtCore import *
from PyQt5 import uic
from PyQt5 import QtCore, QtGui, QtWidgets
import time
from pyrobot import Robot
from SnapCollage import *


robot = Robot()


class MainWindow(QMainWindow):

    show_screenshot = QtCore.pyqtSignal()
    close_screenshot = QtCore.pyqtSignal()

    def __init__(self):
        super().__init__()

        self.title = 'SnapCollage'

        self.images = []
        self.isSnip = False

        self.setWindowTitle(self.title)

        self.tools_ui()
        self.snip_ui()

        # resize & center
        self.setGeometry(0, 0, 400, self.toolbar.height())
        qtRectangle = self.frameGeometry()
        centerPoint = QDesktopWidget().availableGeometry().center()
        qtRectangle.moveCenter(centerPoint)
        self.move(qtRectangle.topLeft())

        self.show()
    
    def tools_ui(self):
        # new snip button
        new_snip = QAction('Add', self)
        new_snip.triggered.connect(self.new_snip)

        # clear button - placeholder
        clear_snaps = QAction('Clear', self)
        clear_snaps.triggered.connect(self.clear_images)

        # copy button - placeholder
        copy_snap = QAction('Copy', self)

        # paste button - placeholder
        paste_image = QAction('Paste', self)

        # toolbar
        toolbar = self.addToolBar('Tools')
        toolbar.addAction(new_snip)
        toolbar.addAction(clear_snaps)
        toolbar.addAction(copy_snap)
        toolbar.addAction(paste_image)

        self.toolbar = toolbar
        
        # sorter - placeholder
        sorter_label = QLabel("Sort Mode:  ")
        sorter_combo = QComboBox(self)
        sorter_combo.addItem("Linear")
        sorter_combo.addItem("Plastique")
        sorter_combo.addItem("Cleanlooks")

        # configurebar
        configurebar = self.addToolBar('Configure')
        configurebar.addWidget(sorter_label)
        configurebar.addWidget(sorter_combo)

        self.configurebar = configurebar
    
    def snip_ui(self):
        # self.root.addWidget(SnapImage())
        snapview = SnapView()

        self.snapview = snapview
        self.snapview.display()
        self.setCentralWidget(snapview)

    def show_image(self):
        self.snapview.display()

    def clear_images(self):
        self.snapview.reset()
    
    def add_image(self, im):
        qim = ImageQt(im)
        self.snapview.add_image(qim)
        
    def new_snip(self):
        if self.isSnip:
            self.isSnip = False
            self.close_screenshot.emit()
        else:
            self.isSnip = True
            self.show_screenshot.emit()


class Screenshot(QWidget):

    on_close = QtCore.pyqtSignal()

    def screenshot(self):
        with mss.mss() as sct:
            filename = sct.shot(mon=-1)
        im = Image.open(filename)
        im = im.convert("RGBA")
        qim = ImageQt(im)
        pix = QtGui.QPixmap.fromImage(qim)
        self.pix = pix

    def __init__(self, x, y):
        super().__init__()

        size = (ctypes.windll.user32.GetSystemMetrics(78), ctypes.windll.user32.GetSystemMetrics(79))

        self.snip = None
        self.drag = None
        self.left = x
        self.top = y
        self.width = size[0]
        self.height = size[1]
        self.largest_rect = QRect(0, 0, self.width, self.height)
        self.clip_rect = QRect(0, 0, 0, 0)

        self.setWindowFlags(
            QtCore.Qt.FramelessWindowHint |
            QtCore.Qt.WindowStaysOnTopHint
        )
        self.setGeometry(self.left, self.top, self.width, self.height)
    
    def paintEvent(self, event):
        painter = QtGui.QPainter(self)
        painter.setClipping(True)

        painter.drawPixmap(event.rect(), self.pix)

        painter.drawRect(self.largest_rect)
        painter.fillRect(self.largest_rect, QBrush(QColor(255, 255, 255, 90)))

        painter.setRenderHint(QPainter.Antialiasing)

        painter.drawRect(self.clip_rect)
        painter.setClipRect(self.clip_rect)

        painter.drawPixmap(self.largest_rect, self.pix)
        painter.end()

    def keyPressEvent(self, event):
        if event.key() == QtCore.Qt.Key_Escape:
            self.on_close.emit()
    
    def mousePressEvent(self, event):
        if self.drag is None:
            self.drag = (event.x(), event.y(), event.globalX(), event.globalY())
    
    def mouseReleaseEvent(self, event):
        x1 = min(self.drag[2], event.globalX())
        y1 = min(self.drag[3], event.globalY())
        x2 = max(self.drag[2], event.globalX())
        y2 = max(self.drag[3], event.globalY())

        coords = (x1, y1, x2, y2)

        img = robot.take_screenshot(coords)

        self.snip = img
        self.on_close.emit()
        self.drag = None
    
    def mouseMoveEvent(self, event):
        if (self.drag is not None):
            width = event.x() - self.drag[0]
            height = event.y() - self.drag[1]
            self.clip_rect = QRect(self.drag[0], self.drag[1], width, height)
            self.repaint()


class Controller:

    def __init__(self, topX, topY):
        self.topPos = (topX, topY)
        self.window = MainWindow()
        self.window.show_screenshot.connect(self.show_screenshot)
        self.window.close_screenshot.connect(self.close_screenshot)

    def show_main(self):
        self.window.setWindowFlags(QtCore.Qt.WindowStaysOnTopHint)
        self.window.showMaximized()
    
    def close_screenshot(self):
        self.window.isSnip = False
        
        if self.screenshot_window.snip is not None:
            self.window.add_image(self.screenshot_window.snip)

        self.screenshot_window.close()
        self.window.show_image()
        self.window.setWindowOpacity(1)

    def show_screenshot(self):
        self.window.setWindowOpacity(0)
        # time.sleep(0.15)

        self.screenshot_window = Screenshot(self.topPos[0], self.topPos[1])
        self.screenshot_window.on_close.connect(self.close_screenshot)
        self.screenshot_window.screenshot()
        self.screenshot_window.show()


def main():
    app = QtWidgets.QApplication(sys.argv)

    # determine coordinate (lowest x & y)
    topX = 0
    topY = 0

    desktop = app.desktop()
    desktop_count = desktop.screenCount()

    for i in range(desktop_count):
        geo = app.desktop().screenGeometry(i)
        _x = geo.x()
        _y = geo.y()
        topX = _x if _x < topX else topX
        topY = _y if _y < topY else topY
    
    controller = Controller(topX, topY)
    controller.show_main()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()