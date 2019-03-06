#!/usr/bin/env python3
# coding: utf-8

import sys, time, subprocess

from io import BytesIO
from PySide2 import QtCore, QtWidgets, QtGui
from PySide2.QtWidgets import QMainWindow, QInputDialog
from PySide2.QtCore import QSize

shared = {}
shared['cursor'] = QtGui.QCursor()
shared['curpos'] = None


class SnapWindow(QMainWindow):
    def __init__(self, app, flags):
        self.flag_snapped = False  # Picture snapped or loaded at start.
        self.flag_frame = True     # Window frame toggling.
        self.app = app
        self.winsize = None     # None-Conditional toggle on resize.
                                # Also the size the window should be.

        QMainWindow.__init__(self)
        self.setWindowTitle("Snap")
        self.cliplabel = QtWidgets.QLabel(self)
        self.cliplabel.show()
        self.cliplabel.setScaledContents(True)
        self.clip_pix = self.cliplabel.pixmap()
        self.clipboard = app.clipboard()
        self.clipboard.dataChanged.connect(self.clipboardChanged)
        self.clipboard.clear(mode=self.clipboard.Clipboard)
        p = self.palette()
        p.setColor(self.backgroundRole(), QtCore.Qt.white)
        self.setPalette(p)
        self.hide()
    
    def load_from_image(self):
        self.flag_snapped = True
        im = QtGui.QImage()
        im.load(shared['inputfp'])
        pm = QtGui.QPixmap().fromImage(im)
        self.original_snap = pm.copy()
        self.original_size = pm.width(), pm.height()
        mpos = shared['curpos']
        self.setGeometry(mpos.x(),mpos.y(), pm.width(), pm.height())
        self.cliplabel.resize(pm.width(),pm.height())
        self.cliplabel.setPixmap(pm)
        self.show()
        
    def clipboardChanged(self):
        if self.flag_snapped == False:
            self.clipboard = self.app.clipboard()
            pm = self.clipboard.pixmap()
            self.original_snap = pm.copy()
            self.original_size = pm.width(), pm.height()
            if pm.isNull():
                pass
            else:
                self.flag_snapped = True
                mpos = shared['curpos']
                self.setGeometry(mpos.x()-pm.width(),mpos.y()-pm.height(), pm.width(), pm.height())
                self.cliplabel.resize(pm.width(),pm.height())
                self.cliplabel.setPixmap(pm)
                self.show()
            
    def resizeEvent(self, event):
        super(SnapWindow, self).resizeEvent(event)
        if self.winsize:
            self.cliplabel.resize(self.savesize.width(),self.savesize.height())
            self.resize(self.savesize.width(),self.savesize.height())
            self.winsize = None
        else:
            self.cliplabel.resize(self.width(),self.height())
        
    def scale_ratio(self):
        winsize = QSize(self.width(),self.height())
        new_size = QSize(self.original_size[0],self.original_size[1])
        new_size.scale(winsize, QtCore.Qt.KeepAspectRatio)
        self.cliplabel.resize(new_size)
        self.resize(new_size)
        
    def reset_size(self):
        origsize = QSize(self.original_size[0],self.original_size[1])
        self.cliplabel.resize(origsize)
        self.cliplabel.setPixmap(self.original_snap)
        self.resize(origsize)
        
    def mousePressEvent(self, event):
        super(SnapWindow, self).mousePressEvent(event)
        if event.button() == QtCore.Qt.MouseButton.LeftButton:
            self.scale_ratio()
            
    def contextMenuEvent(self, event):
        menu = QtWidgets.QMenu(self)
        action_rename = menu.addAction("Rename")
        action_save = menu.addAction("Save Original")
        action_reset = menu.addAction("Reset to Original")
        action_frame = menu.addAction("Toggle Frame")        
        action_close = menu.addAction("Close")
        action = menu.exec_(self.mapToGlobal(event.pos()))
        if action == action_save:
            self.save_copy()
        elif action == action_reset:
            self.reset_size()
        elif action == action_frame:
            if self.flag_frame == True:
                self.flag_frame = False
                self.setWindowFlag(QtCore.Qt.FramelessWindowHint, True)
                self.hide()
                self.show()
                self.winsize = self.size()
            else:
                self.flag_frame = True
                self.setWindowFlag(QtCore.Qt.FramelessWindowHint, False)
                self.hide()
                self.show()
                self.winsize = self.size()
            self.reset_size()
        elif action == action_close:
            self.close()
        elif action == action_rename:
            name, tmp = QInputDialog.getText(self, "", "Name this window:")
            self.setWindowTitle(name)
            
    def save_copy(self):
        fd = QtWidgets.QFileDialog()
        fd.setDirectory(QtCore.QDir('~/'))
        savefn = fd.getSaveFileName(self, 'Save File')[0]
        pixmap = self.original_snap
        barray = QtCore.QByteArray()
        qbuffer = QtCore.QBuffer(barray)
        qbuffer.open(QtCore.QIODevice.WriteOnly)
        pixmap.save(qbuffer, "PNG")
        bytesio = BytesIO(barray.data())
        bytesio.seek(0)
        with open(savefn, 'wb') as savefile:
            savefile.write(bytesio.read())


def main():
    app = QtWidgets.QApplication(sys.argv)
    mainWin = SnapWindow(app, flags=None)
    
    if len(sys.argv) < 2:
        subprocess.call(["gnome-screenshot", "-c", "-a"])
        shared['curpos'] = shared['cursor'].pos()
    else:
        shared['curpos'] = shared['cursor'].pos()
        shared['inputfp'] = sys.argv[1]
        print(shared['inputfp'])
        mainWin.load_from_image()

    sys.exit( app.exec_() )

if __name__ == '__main__':
    main()

