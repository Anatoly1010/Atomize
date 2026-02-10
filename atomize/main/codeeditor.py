#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# a nice numeration of the line number for QPlainTextEdit
# mainly from https://gist.github.com/eyllanesc/e614ea9689e025c16b10fc92b68f0afd
# with a little bit of appearance changes

from PyQt6 import QtGui
from PyQt6.QtCore import QRect, pyqtSlot, Qt, QSize
from PyQt6.QtGui import QColor, QTextFormat, QPainter, QFont, QKeyEvent, QTextOption, QTextCursor, QKeySequence, QShortcut
from PyQt6.QtWidgets import QWidget, QPlainTextEdit, QApplication, QTextEdit, QInputDialog, QSpinBox

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
        self.setTabStopDistance(30) # set the tab width
        self.lineNumberArea = LineNumberArea(self)
        self.blockCountChanged.connect(self.updateLineNumberAreaWidth)
        self.updateRequest.connect(self.updateLineNumberArea)
        self.cursorPositionChanged.connect(self.highlightCurrentLine)
        self.updateLineNumberAreaWidth(0)
        self.highlightCurrentLine()
        self.selectionChanged.connect(self.update_whitespace_visibility)

        self.last_search_term = ""

    def update_whitespace_visibility(self):
        doc = self.document()
        options = doc.defaultTextOption()
        if self.textCursor().hasSelection():
            options.setFlags(options.flags() | QTextOption.Flag.ShowTabsAndSpaces)
        else:
            options.setFlags(options.flags() & ~QTextOption.Flag.ShowTabsAndSpaces)
        
        doc.setDefaultTextOption(options)

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
                painter.setFont(QtGui.QFont("Ubuntu", 9, QtGui.QFont.Weight.Bold))
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

    def keyPressEvent(self, event: QKeyEvent):
        if event.key() == Qt.Key.Key_Tab:
            self.insertPlainText("    ")
            event.accept()
        elif event.modifiers() == Qt.KeyboardModifier.ControlModifier and event.key() == Qt.Key.Key_G:
            self.show_styled_dialog()
            return
        elif event.modifiers() == Qt.KeyboardModifier.ControlModifier and event.key() == Qt.Key.Key_F:
            self.trigger_search()
            return
        elif event.modifiers() == Qt.KeyboardModifier.ControlModifier and event.key() == Qt.Key.Key_N:
            self.find_next()
            return
        else:
            super().keyPressEvent(event)

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
        #if not self.isReadOnly():
        selection = QTextEdit.ExtraSelection()
        lineColor = QColor(48, 48, 75)
        selection.format.setBackground(lineColor)
        selection.format.setProperty(QTextFormat.Property.FullWidthSelection, True)
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

    def show_styled_dialog(self):
        dialog = QInputDialog(self)
        dialog.setWindowTitle("Go to Line")
        dialog.setLabelText("Enter line number:")
        dialog.setInputMode(QInputDialog.InputMode.IntInput)
        dialog.setIntRange(1, self.document().blockCount())
        
        # Set stylesheet directly on the instance
        dialog.setStyleSheet("background-color: rgb(42, 42, 64); color: rgb(211, 194, 78);")
        
        spinbox = dialog.findChild(QSpinBox)
        if spinbox:
            spinbox.setButtonSymbols(QSpinBox.ButtonSymbols.PlusMinus)

        if dialog.exec():
            line_num = dialog.intValue()
            self.jump_to_line(line_num)

    def jump_to_line(self, line_number):
        # findBlockByLineNumber uses 0-based indexing
        block = self.document().findBlockByLineNumber(line_number - 1)
        if block.isValid():
            cursor = QTextCursor(block)
            self.setTextCursor(cursor)
            self.ensureCursorVisible() # Ensure the line is in view

    def trigger_search(self):
        self.setStyleSheet("""background-color: rgb(42, 42, 64); color: rgb(211, 194, 78);  selection-background-color: rgb(211, 197, 78); selection-color: rgb(63, 63, 97); """)
        
        text, ok = QInputDialog.getText(
            self, "Find Text", "Search for:", text=self.last_search_term
        )

        if ok and text:
            self.last_search_term = text
            self.find_text(text)

    def find_text(self, text):
        # Standard forward search
        found = self.find(text)

        if not found:
            self.moveCursor(QTextCursor.MoveOperation.Start)
            if not self.find(text):
                pass
                #print(f"'{text}' not found in document")

    def find_next(self):
        if self.last_search_term:
            self.find_text(self.last_search_term)

if __name__ == '__main__':
    import sys

    app = QApplication(sys.argv)
    w = CodeEditor()
    w.show()
    sys.exit(app.exec_())