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
import sorter
from pyrobot import Robot


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
        new_snip.triggered.connect(self.on_click)

        # clear button - placeholder
        clear_snaps = QAction('Clear', self)

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
        pass

    def show_image(self):
        scene = QGraphicsScene(self)
        view = QGraphicsView(scene)
        self.scene = scene
        self.view = view
        self.setCentralWidget(view)

        if len(self.images):
            sorted = sorter.sort(self.images)
            images = sorted[0]

            for item in images:
                self.qim = item.image
                pix = QtGui.QPixmap.fromImage(self.qim)

                pos = item.pos
                size = item.size

                pixmap = QGraphicsPixmapItem(pix)
                pixmap.setOffset(pos[0], pos[1])
                scene.addItem(pixmap)

            # view.fitInView(scene.sceneRect(), Qt.KeepAspectRatio)
            view.show()

        
    @pyqtSlot()
    def on_click(self):
        if self.isSnip:
            self.close_screenshot.emit()
        else:
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
        left = self.drag[2]
        top = self.drag[3]
        width = event.globalX()
        height = event.globalY()
        coords = (left, top, width, height)
        print(coords)
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
        self.window.show()
    
    def close_screenshot(self):
        self.window.isSnip = False
        
        if self.screenshot_window.snip is not None:
            im = self.screenshot_window.snip
            qim = ImageQt(im)
            self.window.images.append(qim)

        self.screenshot_window.close()
        self.window.show_image()
        self.window.show()

    def show_screenshot(self):
        self.screenshot_window = Screenshot(self.topPos[0], self.topPos[1])
        self.screenshot_window.on_close.connect(self.close_screenshot)
        self.window.isSnip = True

        self.window.hide()
        time.sleep(0.18)

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
        print(i, geo)
        _x = geo.x()
        _y = geo.y()
        topX = _x if _x < topX else topX
        topY = _y if _y < topY else topY
    
    controller = Controller(topX, topY)
    controller.show_main()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()