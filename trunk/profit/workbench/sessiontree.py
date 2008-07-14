#!/usr/bin/env pythno
# -*- coding: utf-8 -*-

# Copyright 2007 Troy Melhase
# Distributed under the terms of the GNU General Public License v2
# Author: Troy Melhase <troy@gci.net>

from functools import partial
from string import Template

from PyQt4.QtCore import Qt, QVariant, pyqtSignature
from PyQt4.QtGui import (QAction, QApplication, QDesktopServices,
                         QFrame, QIcon, QMenu, QStandardItem,
                         QStandardItemModel)

from profit.lib import defaults, logging
from profit.lib.gui import UrlAction, UrlRequestor
from profit.lib.core import SessionHandler, SettingsHandler
from profit.lib.core import Settings, Signals, DataRoles
from profit.workbench.widgets.ui_sessiontree import Ui_SessionTree


iconNameMap = {
    'account':'identity',
    'connection':'server',
    'historical data':'log',
    'messages':'view_text',
    'orders':'klipper_dock',
    'portfolio':'bookcase',
    'strategy':'services',
    'tickers':'view_detailed',
}


class SessionTreeItem(QStandardItem):
    """ Session tree item.

    """
    def __init__(self, text):
        """ Initializer.

        @param text value for item display
        """
        QStandardItem.__init__(self, text)
        self.setEditable(False)
        self.setIcon(self.lookupIcon(text))
        hint = self.sizeHint()
        hint.setHeight(20)
        self.setSizeHint(hint)

    def lookupIcon(self, key):
        """ Locates icon for given key.

        @param key item text
        @return QIcon instance
        """
        try:
            name = iconNameMap[key]
            icon = QIcon(':images/icons/%s.png' % name)
        except (KeyError, ):
            style = QApplication.style()
            icon = style.standardIcon(style.SP_DirIcon)
        return icon

    def contextActions(self, index):
        """ Sequence of context menu actions for this tree item.

        """
        return []


class SessionTreeTickerItem(SessionTreeItem):
    """ Specalized session tree item for ticker symbols.

    """
    def lookupIcon(self, symbol):
        """ Locates icon for given symbol.

        @param symbol ticker symbol
        @return QIcon instance
        """
        return QIcon(':images/tickers/%s.png' % symbol.lower())

    def setTickerId(self, tickerId):
        """ Sets item data for ticker id.

        @param tickerId id for ticker as integer
        @return None
        """
        self.setData(QVariant(tickerId), DataRoles.tickerId)

    def contextActions(self, index):
        """ Sequence of actions for this tree item.

        """
        data = index.data()
        symbol = data.toString()
        icon = QIcon(index.data(Qt.DecorationRole))
        actions = [QAction(icon, symbol, None), ]
        actions += self.urlActions(symbol)
        for act in actions:
            if not str(act.data().toString()):
                act.setData(data)
        return actions

    def urlActions(self, symbol):
        settings = Settings()
        settings.beginGroup(settings.keys.urls)
        urls = settings.value(settings.keys.tickerurls, defaults.tickerUrls())
        settings.endGroup()
        urls = [str(s) for s in defaults.tickerUrls()]
        actions = []
        for url in urls: #urls.toStringList():
            try:
                name, url = str(url).split(':', 1)
                url = Template(url).substitute(symbol=symbol)
            except (KeyError, ValueError, ):
                continue
            actions.append(UrlAction(name+'...', url, '%s %s' % (symbol, name)))
        return actions


class SessionTreeHistReqItem(SessionTreeItem):
    """ Specalized session tree item for historical data requests.

    """
    def __init__(self, text, reqId, reqData):
        SessionTreeItem.__init__(self, text)
        self.reqId = reqId
        self.reqData = reqData

    def lookupIcon(self, key):
        return QIcon(':images/icons/log.png')


class SessionTreeModel(QStandardItemModel):
    """

    """
    def __init__(self, session, parent=None):
        """ Constructor.

        @param session Session instance
        @param parent ancestor object
        """
        QStandardItemModel.__init__(self)
        self.session = session
        root = self.invisibleRootItem()
        for key, values in session.items():
            item = SessionTreeItem(key)
            root.appendRow(item)
            for value in values:
                ## FIXME:  load tickers on demand; shouldn't need
                ## to switch on item type during tree init
                if key == 'tickers':
                    subitem = SessionTreeTickerItem(value)
                    subitem.setTickerId(values[value])
                else:
                    subitem = SessionTreeItem(value)
                item.appendRow(subitem)


def mkHistDataFormatter(t):
    def formatter(i, d):
        args = (i, d['contract'].m_symbol, d['contract'].m_secType, )
        return t % args
    return formatter
formatHistDataStart  = mkHistDataFormatter('request %s (%s/%s) (started)')
formatHistDataFinish = mkHistDataFormatter('request %s (%s/%s) (finished)')
formatHistDataError  = mkHistDataFormatter('request %s (%s/%s) (error)')


class SessionTree(QFrame, Ui_SessionTree, SessionHandler,
                  SettingsHandler, UrlRequestor):
    """ Tree view of a Session object.

    """
    def __init__(self, parent=None):
        """ Initializer.

        @param parent ancestor of this widget
        """
        QFrame.__init__(self, parent)
        self.setupUi(self)
        self.histDataReqMap = {}
        tree = self.treeView
        tree.header().hide()
        tree.setAnimated(True)
        app = QApplication.instance()
        connect = self.connect
        connect(self, Signals.openUrl, app, Signals.openUrl)
        connect(self, Signals.sessionItemActivated,
                app, Signals.sessionItemActivated)
        self.requestSession()

    def on_treeView_doubleClicked(self, index):
        print '### index:', index
        ## set more data
        self.emit(Signals.sessionItemActivated, index)

    def histDataItem(self):
        """ returns the 'historical data' item or None

        """
        itms = self.treeView.model().findItems('historical data')
        return itms[0] if itms else None

    def histDataReqItems(self):
        """ returns the children of thie 'historical data' item or []

        """
        itm = self.histDataItem()
        return [itm.child(i) for i in range(itm.rowCount())] if itm else []

    def on_session_Error(self, msg):
        """ Called when error messages are received; we check for hist
            data codes in the message.
        """
        reqId, errorCode, errorMsg = msg.id, msg.errorCode, msg.errorMsg
        if reqId in self.histDataReqMap:
            data, item = self.histDataReqMap[reqId]
            if errorCode == 162:
                item.setText(formatHistDataError(reqId, data))
                item.setIcon(QIcon(':images/icons/stop.png'))

    def on_session_historicalDataStart(self, reqId, reqData):
        """ Called when a historical data response has started.

        """
        item = self.histDataItem()
        if item:
            newItem = SessionTreeHistReqItem(
                formatHistDataStart(reqId, reqData),
                reqId, reqData
            )
            item.appendRow(newItem)
            self.treeView.setExpanded(item.index(), True)
            self.histDataReqMap[reqId] = (reqData, newItem)

    def on_session_historicalDataFinish(self, reqId):
        """ Called when a historical data response has finished.

        """
        if reqId in self.histDataReqMap:
            data, item = self.histDataReqMap[reqId]
            item.setText(formatHistDataFinish())
            item.setIcon(QIcon(':images/icons/services.png'))

    def setSession(self, session):
        """ Signal handler called when new Session object is created.

        @param session new Session instance
        @return None
        """
        self.session = session
        self.dataModel = model = SessionTreeModel(session, self)
        view = self.treeView
        view.setModel(model)
        session.registerMeta(self)
        if not session.messages:
            settings = self.settings
            settings.beginGroup(settings.keys.main)
            tabstate = settings.valueLoad(settings.keys.ctabstate, [])
            settings.endGroup()
            connection = 'connection'
            if connection not in tabstate:
                tabstate.append(connection)
            for tabname in tabstate:
                try:
                    item = model.findItems(tabname)[0]
                except (IndexError, ):
                    pass
                else:
                    view.emit(Signals.modelDoubleClicked, item.index())

    def contextMenuEvent(self, event):
        """ Called when context menu is requested on the tree.

        """
        pos = event.pos()
        index = self.treeView.indexAt(pos)
        item = self.dataModel.itemFromIndex(index)
        if not item:
            return
        actions = item.contextActions(index)
        event.accept()
        if not actions:
            return
        for act in actions:
            if isinstance(act, UrlAction):
                handler = partial(self.on_urlAction, action=act)
                self.connect(act, Signals.triggered, handler)
        QMenu.exec_(actions, self.treeView.viewport().mapToGlobal(pos))

