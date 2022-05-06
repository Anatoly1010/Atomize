#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# a nice numeration of the line number for QPlainTextEdit
# mainly from https://gist.github.com/eyllanesc/e614ea9689e025c16b10fc92b68f0afd
# with a little bit of appearance changes

from PyQt6 import QtGui
from PyQt6.QtCore import QRect, pyqtSlot, Qt, QSize
from PyQt6.QtGui import QColor, QTextFormat, QPainter, QFont
from PyQt6.QtWidgets import QWidget, QPlainTextEdit, QApplication, QTextEdit

class LineNumberArea(QWidget):
    def __init__(self, editor):
        QWidget.__init__(self, parent = editor)
        self.codeEditor = editor

    def sizeHint(self):
        return QSize(self.codeEditor.lineNumberAreaWidth(), 0)

    def paintEvent(self, event):
        self.codeEditor.lineNumberAreaPaintEvent(event)

class CodeEditor(QPlainTextEdit):
    
    def __init__(self, parent=None):
        QPlainTextEdit.__init__(self, parent)
        
        self.top_margin = 0
        self.setTabStopDistance(30)                 # set the tab width
        self.lineNumberArea = LineNumberArea(self)
        self.blockCountChanged.connect(self.updateLineNumberAreaWidth)
        self.updateRequest.connect(self.updateLineNumberArea)
        self.cursorPositionChanged.connect(self.highlightCurrentLine)
        self.updateLineNumberAreaWidth(0)
        self.highlightCurrentLine()
        
    def lineNumberAreaPaintEvent(self, event):
        painter = QPainter(self.lineNumberArea)
        painter.fillRect(event.rect(), QColor(63, 63, 97))   # color of the line column 

        block = self.firstVisibleBlock()
        blockNumber = block.blockNumber();
        top = self.blockBoundingGeometry(block).translated(self.contentOffset()).top()
        bottom = top + self.blockBoundingRect(block).height()

        while block.isValid() and top <= event.rect().bottom():
            if block.isVisible() and bottom >= event.rect().top():
                number = str(blockNumber + 1)
                painter.setPen(QColor(192, 202, 227))
                painter.setFont(QtGui.QFont("Ubuntu", 9.0, QtGui.QFont.Weight.Bold))
                painter.drawText(-4, int(top + 1), self.lineNumberArea.width(), 
                    self.fontMetrics().height(),
                    Qt.AlignmentFlag.AlignRight, number)
            block = block.next()
            top = bottom
            bottom = top + self.blockBoundingRect(block).height() + 0.1
            blockNumber += 1

    def lineNumberAreaWidth(self):
        digits = len(str(self.blockCount()))
        space = 8 + self.fontMetrics().horizontalAdvance('9')*digits
        return space

    def resizeEvent(self, event):
        QPlainTextEdit.resizeEvent(self, event)
        cr = self.contentsRect()
        self.lineNumberArea.setGeometry(QRect(cr.left(), cr.top(), self.lineNumberAreaWidth(), cr.height()))

    @pyqtSlot(int)
    def updateLineNumberAreaWidth(self, newBlockCount):
        self.setViewportMargins(self.lineNumberAreaWidth() + 2, self.top_margin, 0, 0);

    @pyqtSlot()
    def highlightCurrentLine(self):
        extraSelections = []
        if not self.isReadOnly():
            selection = QTextEdit.ExtraSelection()
            lineColor = QColor(48, 48, 75)           #color of the line highlighter QColor(136, 138, 133)  
            selection.format.setBackground(lineColor)
            selection.format.setProperty( 24576, True)
            selection.cursor = self.textCursor()
            selection.cursor.clearSelection()
            extraSelections.append(selection)
        self.setExtraSelections(extraSelections)

    @pyqtSlot(QRect, int)
    def updateLineNumberArea(self, rect, dy):
        if dy:
            self.lineNumberArea.scroll(0, dy)
        else:
            self.lineNumberArea.update(0, rect.y(), self.lineNumberArea.width(), rect.height())
        if rect.contains(self.viewport().rect()):
            self.updateLineNumberAreaWidth(0)


if __name__ == '__main__':
    import sys

    app = QApplication(sys.argv)
    w = CodeEditor()
    w.show()
    sys.exit(app.exec_())