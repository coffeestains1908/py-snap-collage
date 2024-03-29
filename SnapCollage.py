import sys
from PyQt5.QtCore import Qt, QPointF
from PyQt5.QtWidgets import *
from PyQt5 import QtCore, QtGui, QtWidgets
import sorter


class SnapView(QGraphicsView):
    def __init__(self):
        super().__init__()
        self.scene = QGraphicsScene()
        self.setScene(self.scene)

        self.images = []
        self.currentZ = 0
    
    def reset(self):
        self.images = []
        self.scene.clear()
    
    def add_image(self, img):
        self.images.append(img)
        self.display()
    
    def display(self):
        self.scene.clear()
        
        if len(self.images):
            sorted = sorter.sort(self.images)
            images = sorted[0]

            for item in images:
                self.qim = item.image
                pix = QtGui.QPixmap.fromImage(self.qim)

                pos = item.pos
                size = item.size

                snapimage = SnapImage(self, pix, pos[0], pos[1])
                self.scene.addItem(snapimage)
    
    def mousePressEvent(self, event):
        if event.button() == Qt.MidButton: # or Qt.MiddleButton
            self.__prevMousePos = event.pos()
        else:
            super(SnapView, self).mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.MidButton: # or Qt.MiddleButton
            offset = self.__prevMousePos - event.pos()
            self.__prevMousePos = event.pos()

            self.verticalScrollBar().setValue(self.verticalScrollBar().value() + offset.y())
            self.horizontalScrollBar().setValue(self.horizontalScrollBar().value() + offset.x())
        else:
            super(SnapView, self).mouseMoveEvent(event)
        
    def wheelEvent(self,event):
        y = event.angleDelta().y()
        adj = (y/120) * 0.1
        self.scale(1+adj, 1+adj)


class SnapImage(QGraphicsPixmapItem):
    def __init__(self, parent, pix, x, y):
        super().__init__(pix)
        self.setPos(x, y)
        self.setAcceptHoverEvents(True)
        self.setZValue(0)
        self.setTransformationMode(Qt.SmoothTransformation)
        
        self.parent = parent

    def hoverEnterEvent(self, event: 'QGraphicsSceneHoverEvent'):
        QApplication.instance().setOverrideCursor(Qt.OpenHandCursor)

    def hoverLeaveEvent(self, event: 'QGraphicsSceneHoverEvent'):
        QApplication.instance().restoreOverrideCursor()

    def mouseMoveEvent(self, event: 'QGraphicsSceneMouseEvent'):
        new_curs_pos = event.scenePos()
        old_curs_pos = event.lastScenePos()
        
        self_pos = self.scenePos()

        x = new_curs_pos.x() - old_curs_pos.x() + self_pos.x()
        y = new_curs_pos.y() - old_curs_pos.y() + self_pos.y()
        
        self.setPos(QPointF(x, y))

    def mousePressEvent(self, event: 'QGraphicsSceneMouseEvent'):
        self.parent.currentZ += 1
        self.setZValue(self.parent.currentZ)

    def mouseDoubleClickEvent(self, event: 'QGraphicsSceneMouseEvent'): pass

    def mouseReleaseEvent(self, event: 'QGraphicsSceneMouseEvent'): pass