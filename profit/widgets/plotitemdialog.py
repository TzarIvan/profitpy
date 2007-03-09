#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright 2007 Troy Melhase <troy@gci.net>
# Distributed under the terms of the GNU General Public License v2

from PyQt4.QtCore import QVariant, Qt, pyqtSignature
from PyQt4.QtGui import QBrush, QColor, QColorDialog, QDialog, QIcon, QPixmap
from PyQt4.QtGui import QPainter, QPen
from PyQt4.Qwt5 import QwtPlot, QwtPlotCurve, QwtSymbol

from profit.lib.core import Settings
from profit.lib.gui import colorIcon, complementColor
from profit.widgets.ui_plotitemdialog import Ui_PlotItemDialog

## include plot samples


penStyles = [
    (Qt.SolidLine, 'Solid'),
    (Qt.DashLine, 'Dash'),
    (Qt.DotLine, 'Dot'),
    (Qt.DashDotLine, 'Dash Dot'),
    (Qt.DashDotDotLine, 'Dash Dot Dot'),
]


lineStyles = [
    (QwtPlotCurve.NoCurve, 'No Line'),
    (QwtPlotCurve.Lines, 'Line'),
    (QwtPlotCurve.Sticks, 'Sticks'),
    (QwtPlotCurve.Steps, 'Steps'),
    (QwtPlotCurve.Dots, 'Dots'),
]


symbolStyles = [
    (QwtSymbol.NoSymbol, 'No Symbol'),
    (QwtSymbol.Ellipse, 'Ellipse'),
    (QwtSymbol.Rect, 'Rectangle'),
    (QwtSymbol.Diamond, 'Diamond'),
    (QwtSymbol.Triangle, 'Triangle'),
    (QwtSymbol.DTriangle, 'Triangle Down'),
    (QwtSymbol.UTriangle, 'Triangle Up'),
    (QwtSymbol.LTriangle, 'Triangle Left'),
    (QwtSymbol.RTriangle, 'Triangle Right'),
    (QwtSymbol.Cross, 'Cross'),
    (QwtSymbol.XCross, 'Cross Diagonal'),
    (QwtSymbol.HLine, 'Line Horizontal'),
    (QwtSymbol.VLine, 'Line Vertical'),
    (QwtSymbol.Star1, 'Star 1'),
    (QwtSymbol.Star2, 'Star 2'),
    (QwtSymbol.Hexagon, 'Hexagon'),
]


brushStyles = [
    (Qt.NoBrush, 'None'),
    (Qt.SolidPattern, 'Solid'),
    (Qt.Dense1Pattern, 'Extremely Dense'),
    (Qt.Dense2Pattern, 'Very Dense'),
    (Qt.Dense3Pattern, 'Somewhat Dense'),
    (Qt.Dense4Pattern, 'Half Dense'),
    (Qt.Dense5Pattern, 'Somewhat Sparse'),
    (Qt.Dense6Pattern, 'Very Sparse'),
    (Qt.Dense7Pattern, 'Extremely Sparse'),
    (Qt.HorPattern, 'Horizontal Lines'),
    (Qt.VerPattern, 'Vertical Lines'),
    (Qt.CrossPattern, 'Crossing Horizontal and Vertical Lines'),
    (Qt.BDiagPattern, 'Backward Diagonal Lines'),
    (Qt.FDiagPattern, 'Forward Diagonal Lines'),
    (Qt.DiagCrossPattern, 'Crossing Diagonal Lines'),
]


class PenStylePixmap(QPixmap):
    def __init__(self):
        QPixmap.__init__(self, 32, 18)
        self.fill(QColor('white'))

    def drawStyle(self, style, painter):
        painter.begin(self)
        pen = QPen(style)
        pen.setWidth(2)
        painter.setPen(pen)
        ymid = self.height()/2
        painter.drawLine(0, ymid, self.width(), ymid)
        painter.end()


class BrushStylePixmap(QPixmap):
    def __init__(self):
        QPixmap.__init__(self, 32, 18)
        self.fill(QColor('black'))

    def drawStyle(self, style, painter):
        white = QColor('white')
        brush = QBrush(style)
        brush.setColor(white)
        pen = QPen(white)
        pen.setWidth(2)
        painter.begin(self)
        painter.setBrush(brush)
        painter.setPen(pen)
        painter.drawRect(0, 0, self.width(), self.height())
        painter.end()


class SymbolStylePixmap(QPixmap):
    def __init__(self):
        QPixmap.__init__(self, 18, 18)
        self.fill(QColor('white'))

    def drawStyle(self, style, painter):
        brush = QBrush(QColor('white'))
        pen = QPen(QColor('black'))
        size = self.size()
        symbol = QwtSymbol(style, brush, pen, size)
        painter.begin(self)
        rect = self.rect()
        rect.adjust(2, 2, -2, -2)
        symbol.draw(painter, rect)
        painter.end()


class LineStyleIconPlot(QwtPlot):
    y = [0, 1, 0.5, 1.5]
    x = range(len(y))

    def __init__(self):
        QwtPlot.__init__(self)
        self.enableAxis(self.yLeft, False)
        self.enableAxis(self.xBottom, False)
        self.setCanvasBackground(QColor(Qt.white))
        canvas = self.canvas()
        canvas.setFrameStyle(canvas.NoFrame)

    def setStyle(self, style, size):
        self.curve = QwtPlotCurve()
        self.resize(size)
        self.curve.attach(self)
        self.curve.setStyle(style)
        self.curve.setData(self.x, self.y)
        pen = QPen(Qt.black)
        pen.setWidth(0)
        self.curve.setPen(pen)
        self.replot()


class LineStylePixmap(QPixmap):
    def __init__(self):
        QPixmap.__init__(self, 18, 18)
        self.fill(QColor('white'))

    def drawStyle(self, style, painter):
        widget = LineStyleIconPlot()
        widget.setStyle(style, self.size())
        widget.print_(self)


def comboCurrentData(combo, cast):
    data = combo.itemData(combo.currentIndex()).toInt()[0]
    return cast(data)


def fillStyleFunction(pixmapType, stylesDefault):
    def fillFunction(combo, current, styles=stylesDefault):
        painter = QPainter()
        for index, (style, name) in enumerate(styles):
            pixmap = pixmapType()
            pixmap.drawStyle(style, painter)
            combo.addItem(QIcon(pixmap), name, QVariant(style))
            if style == current:
                combo.setCurrentIndex(index)
        combo.setIconSize(pixmap.size())
    return fillFunction


fillLineStyles = fillStyleFunction(LineStylePixmap, lineStyles)
fillPenStyles = fillStyleFunction(PenStylePixmap, penStyles)
fillBrushStyles = fillStyleFunction(BrushStylePixmap, brushStyles)
fillSymbolStyles = fillStyleFunction(SymbolStylePixmap, symbolStyles)


class PlotItemDialog(QDialog, Ui_PlotItemDialog):
    def __init__(self, pen=None, curve=None, parent=None):
        QDialog.__init__(self, parent)
        self.setupUi(self)
        if pen is None and curve is not None:
            self.setWindowTitle('Edit Plot Curve')
            pen = curve.pen()
        self.setupPenPage(pen)
        self.setupCurvePage(curve)
        self.setupSymbolPage(curve)


    def applyToCurve(self, curve):
        """ Reconfigures curve to match dialog selections.

        """
        curve.setPen(QPen(self.selectedPen))
        linestyle = comboCurrentData(self.lineStyle, curve.CurveStyle)
        curve.setStyle(linestyle)

        brush = QBrush()
        if self.areaFill.isChecked():
            style = comboCurrentData(self.areaFillStyle, Qt.BrushStyle)
            brush.setStyle(style)
            brush.setColor(self.areaFillColor.color)
        curve.setBrush(brush)

        if linestyle == QwtPlotCurve.Steps:
            curve.setCurveAttribute(curve.Inverted,
                self.curveAttributeInverted.checkState()==Qt.Checked)
        elif linestyle == QwtPlotCurve.Lines:
            curve.setCurveAttribute(curve.Fitted,
                self.curveAttributeFitted.checkState()==Qt.Checked)
        curve.setPaintAttribute(curve.PaintFiltered,
            self.paintAttributeFiltered.checkState()==Qt.Checked)
        curve.setPaintAttribute(curve.ClipPolygons,
            self.paintAttributeClipPolygons.checkState()==Qt.Checked)

        symbol = QwtSymbol()
        style = comboCurrentData(self.symbolStyle, symbol.Style)
        symbol.setStyle(style)
        if style != QwtSymbol.NoSymbol:
            symbol.setSize(
                self.symbolWidth.value(), self.symbolHeight.value())
            pen = QPen()
            pen.setStyle(comboCurrentData(self.symbolPenStyle, Qt.PenStyle))
            pen.setColor(self.symbolPenColor.color)
            pen.setWidth(self.symbolPenWidth.value())
            symbol.setPen(pen)

            brush = QBrush()
            if self.symbolFill.isChecked():
                style = comboCurrentData(self.symbolFillStyle, Qt.BrushStyle)
                brush.setStyle(style)
                brush.setColor(self.symbolFillColor.color)
            symbol.setBrush(brush)
        curve.setSymbol(symbol)

    def setupPenPage(self, pen):
        self.selectedPen = pen or QPen()
        fillPenStyles(self.penStyle, pen.style())
        self.penColor.color = color = pen.color()
        self.penColor.setIcon(colorIcon(color))
        self.penWidth.setValue(pen.width())
        self.penSample.installEventFilter(self)

    def setupCurvePage(self, curve):
        self.sectionList.item(1).setHidden(not bool(curve))
        if not curve:
            return
        brush = curve.brush()
        current = brush.style()
        fillLineStyles(self.lineStyle, curve.style())
        fillBrushStyles(self.areaFillStyle, current)
        self.areaFill.setChecked(current != Qt.NoBrush)
        self.areaFillColor.color = color = curve.brush().color()
        self.areaFillColor.setIcon(colorIcon(color))
        self.curveAttributeInverted.setChecked(
            curve.testCurveAttribute(curve.Inverted))
        self.curveAttributeFitted.setChecked(
            curve.testCurveAttribute(curve.Fitted))
        self.paintAttributeFiltered.setChecked(
            curve.testPaintAttribute(curve.PaintFiltered))
        self.paintAttributeClipPolygons.setChecked(
            curve.testPaintAttribute(curve.ClipPolygons))

    def setupSymbolPage(self, curve):
        self.sectionList.item(2).setHidden(not bool(curve))
        if not curve:
            return
        symbol = curve.symbol()
        brush = symbol.brush()
        pen = symbol.pen()
        fillSymbolStyles(self.symbolStyle, symbol.style())
        fillBrushStyles(self.symbolFillStyle, brush.style())
        self.symbolFillColor.color = color = brush.color()
        self.symbolFillColor.setIcon(colorIcon(color))
        self.symbolFill.setChecked(brush != Qt.NoBrush)
        fillPenStyles(self.symbolPenStyle, pen.style())
        self.symbolPenColor.color = color = pen.color()
        self.symbolPenColor.setIcon(colorIcon(color))
        self.symbolPenWidth.setValue(pen.width())
        size = symbol.size()
        w = size.width()
        h = size.height()
        self.symbolWidth.setValue(w)
        self.symbolHeight.setValue(h)
        self.symbolSyncSize.setChecked(w==h)
        havesymbol = symbol.style() != QwtSymbol.NoSymbol
        self.symbolFill.setEnabled(havesymbol)
        self.symbolSizeGroup.setEnabled(havesymbol)
        self.symbolOutlineGroup.setEnabled(havesymbol)

    @pyqtSignature('int')
    def on_penStyle_activated(self, index):
        value, okay = self.penStyle.itemData(index).toInt()
        if okay:
            self.selectedPen.setStyle(Qt.PenStyle(value))
            self.penSample.update()

    @pyqtSignature('int')
    def on_penWidth_valueChanged(self, value):
        self.selectedPen.setWidth(value)
        self.penSample.update()

    @pyqtSignature('')
    def on_penColor_clicked(self):
        color = self.selectColor(self.penColor)
        if color:
            self.selectedPen.setColor(color)
            self.penSample.update()

    @pyqtSignature('')
    def on_areaFillColor_clicked(self):
        self.selectColor(self.areaFillColor)

    @pyqtSignature('')
    def on_symbolFillColor_clicked(self):
        self.selectColor(self.symbolFillColor)

    @pyqtSignature('')
    def on_symbolPenColor_clicked(self):
        self.selectColor(self.symbolPenColor)

    def selectColor(self, widget):
        color = QColorDialog.getColor(widget.color, self)
        if color.isValid():
            widget.color = color
            widget.setIcon(colorIcon(color))
            return color

    def on_symbolSyncSize_stateChanged(self, state):
        if state == Qt.Checked:
            value = max(self.symbolWidth.value(), self.symbolHeight.value())
            self.symbolWidth.setValue(value)
            self.symbolHeight.setValue(value)

    @pyqtSignature('int')
    def on_symbolWidth_valueChanged(self, value):
        if self.symbolSyncSize.checkState() == Qt.Checked:
            self.symbolHeight.setValue(value)

    @pyqtSignature('int')
    def on_symbolHeight_valueChanged(self, value):
        if self.symbolSyncSize.checkState() == Qt.Checked:
            self.symbolWidth.setValue(value)

    @pyqtSignature('int')
    def on_symbolStyle_currentIndexChanged(self, index):
        value, okay = self.symbolStyle.itemData(index).toInt()
        if okay:
            havesymbol = value != QwtSymbol.NoSymbol
            self.symbolFill.setEnabled(havesymbol)
            self.symbolSizeGroup.setEnabled(havesymbol)
            self.symbolOutlineGroup.setEnabled(havesymbol)

    @pyqtSignature('int')
    def on_lineStyle_currentIndexChanged(self, index):
        value, okay = self.lineStyle.itemData(index).toInt()
        if okay:
            self.curveAttributeInverted.setEnabled(value==QwtPlotCurve.Steps)
            self.curveAttributeFitted.setEnabled(value==QwtPlotCurve.Lines)
            hascurve = value != QwtPlotCurve.NoCurve
            self.areaFill.setEnabled(hascurve)
            self.curveAttributesGroup.setEnabled(hascurve)

    def eventFilter(self, obj, event):
        if obj == self.penSample:
            if event.type() == event.Paint:
                obj.paintEvent(event)
                rect = obj.rect()
                painter = QPainter()
                painter.begin(obj)
                comp = complementColor(self.selectedPen.color())
                painter.fillRect(rect, QBrush(comp))
                x1 = y1 = y2 = rect.height()/2
                x2 = rect.width() - y1
                painter.setPen(self.selectedPen)
                painter.drawLine(x1, y1, x2, y2)
                painter.end()
                return True
            else:
                return False
        else:
            return QDialog.eventFilter(self, obj, event)