import sys
import ctypes
from mss.windows import MSS as mss
from PIL import Image
from PIL.ImageQt import ImageQt
import pyscreenshot as ImageGrab
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtCore import *
from PyQt5 import QtCore, QtGui, QtWidgets
import time
import sorter


def screenshot(coords=None):
    """returns PIL image of whole screen
    :param coords (x1, y1, x2, y2)
    """
    if coords is None:
        with mss() as sct:
            filename = sct.shot(mon=-1)
        im = Image.open(filename)
        im = im.convert("RGBA")
        return im
    else:
        return ImageGrab.grab(bbox=(coords))


class MainWindow(QWidget):

    show_screenshot = QtCore.pyqtSignal()
    close_screenshot = QtCore.pyqtSignal()

    def __init__(self):
        super().__init__()
        self.title = 'JABS'
        self.left = 0
        self.top = 0
        self.width = 800
        self.height = 600
        self.images = []
        self.initUI()
        self.isSnip = False

    def initUI(self):
        self.setWindowTitle(self.title)
        
        qtRectangle = self.frameGeometry()
        centerPoint = QDesktopWidget().availableGeometry().center()
        qtRectangle.moveCenter(centerPoint)
        self.move(qtRectangle.topLeft())
        
        root = QVBoxLayout(self)
        self.layout = root
        
        topbar = QHBoxLayout()
        root.addLayout(topbar)

        button = QPushButton('Add New Snap')
        button.setStyleSheet("padding: 20px 40px")
        button.clicked.connect(self.on_click)
        topbar.addWidget(button)

        button = QPushButton('Clear All')
        button.setStyleSheet("padding: 20px 40px")
        topbar.addWidget(button)
        
        topbar.addStretch(1)

        image_cont = QStackedLayout()
        self.image_cont = image_cont
        root.addLayout(image_cont)

        self.show()
    
    def draw_images(self):
        sorted = sorter.sort(self.images)

        for item in sorted:
            self.qim = item.image
            pix = QtGui.QPixmap.fromImage(self.qim)

            pos = item.pos
            size = item.size

            lbl = QLabel()
            lbl.setPixmap(pix)
            lbl.move(pos[0], pos[1])
            
            self.image_cont.addWidget(lbl)
        
    @pyqtSlot()
    def on_click(self):
        if self.isSnip:
            self.close_screenshot.emit()
        else:
            self.show_screenshot.emit()

class Screenshot(QWidget):

    on_close = QtCore.pyqtSignal()

    def screenshot(self):
        im = screenshot()
        qim = ImageQt(im)
        pix = QtGui.QPixmap.fromImage(qim)
        self.pix = pix

    def __init__(self):
        super().__init__()

        self.snip = None
        self.dragstart = None

        self.setWindowFlags(
            QtCore.Qt.FramelessWindowHint |
            QtCore.Qt.WindowStaysOnTopHint
        )
        size = (ctypes.windll.user32.GetSystemMetrics(78), ctypes.windll.user32.GetSystemMetrics(79))
        self.left = 0
        self.top = 0
        self.width = size[0]
        self.height = size[1]
        self.setGeometry(self.left, self.top, self.width, self.height)

        self.largest_rect = QRect(0, 0, self.width, self.height)
        self.clip_rect = QRect(0, 0, 0, 0)
    
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
        if self.dragstart is None:
            self.dragstart = event.pos()
    
    def mouseReleaseEvent(self, event):
        coords = (self.dragstart.x(), self.dragstart.y(), event.x(), event.y())
        print(coords)
        img = screenshot(coords)
        self.snip = img
        self.on_close.emit()
        self.dragstart = None
    
    def mouseMoveEvent(self, event):
        if (self.dragstart is not None):
            width = event.x() - self.dragstart.x()
            height = event.y() - self.dragstart.y()
            self.clip_rect = QRect(self.dragstart.x(), self.dragstart.y(), width, height)
            self.repaint()


class Controller:

    def __init__(self):
        self.window = MainWindow()
        self.window.show_screenshot.connect(self.show_screenshot)
        self.window.close_screenshot.connect(self.close_screenshot)

    def show_main(self):
        self.window.setWindowFlags(QtCore.Qt.WindowStaysOnTopHint)
        self.window.show()
    
    def close_screenshot(self):
        self.window.isSnip = False
        
        if self.screenshot_window.snip is not None:
            print("New image")
            im = self.screenshot_window.snip
            qim = ImageQt(im)
            self.window.images.append(qim)

        self.screenshot_window.close()
        self.window.draw_images()

    def show_screenshot(self):
        self.screenshot_window = Screenshot()
        self.screenshot_window.on_close.connect(self.close_screenshot)
        self.window.isSnip = True

        self.window.hide()
        time.sleep(0.18)

        self.screenshot_window.screenshot()
        self.screenshot_window.show()

        self.window.show()


def main():
    app = QtWidgets.QApplication(sys.argv)
    controller = Controller()
    controller.show_main()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()