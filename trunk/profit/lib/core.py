#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright 2007 Troy Melhase
# Distributed under the terms of the GNU General Public License v2
# Author: Troy Melhase <troy@gci.net>

## this module is generally the first to get imported by one of the gui apps,
## so we execute our ugly hack here.

import sys
if 'profit_rc' not in sys.modules:
    import profit.lib.widgets.profit_rc
    sys.modules['profit_rc'] = profit.lib.widgets.profit_rc


## now back to our regularly scheduled programming.

from cPickle import dumps, loads
from PyQt4.QtCore import (QCoreApplication, QPoint, QSettings, QSize,
                          QVariant, Qt, SIGNAL, SLOT)

from profit.lib import logging


class Signals:
    """ Contains SIGNAL attributes for easy and consistent reference.

    """
    activated = SIGNAL('activated(QSystemTrayIcon::ActivationReason)')
    clicked = SIGNAL('clicked()')
    connectedTWS = SIGNAL('connectedTWS')
    createdAccountData = SIGNAL('createdAccountData')
    createdSeries = SIGNAL('createdSeries')
    createdTicker = SIGNAL('createdTicker')
    currentChanged = SIGNAL('currentChanged(int)')
    currentIndexChanged = SIGNAL('currentIndexChanged(int)')
    customContextMenuRequested = SIGNAL(
        'customContextMenuRequested(const QPoint &)')
    dataChanged = SIGNAL(
        'dataChanged(const QModelIndex &, const QModelIndex &)')
    dialogFinished = SIGNAL('finished(int)')
    disconnectedTWS = SIGNAL('disconnectedTWS')
    doubleValueChanged = SIGNAL('valueChanged(double)')
    enableCurve = SIGNAL('enableCurve')
    finished = SIGNAL('finished()')

    highlightSelections = SIGNAL('highlightSelections')
    historicalDataStart = SIGNAL('historicalDataStart')
    historicalDataFinish = SIGNAL('historicalDataFinish')

    iconChanged = SIGNAL('iconChanged()')
    intValueChanged = SIGNAL('valueChanged(int)')
    itemChanged = SIGNAL('itemChanged(QStandardItem *)')
    itemDoubleClicked = SIGNAL('itemDoubleClicked(QTreeWidgetItem *, int)')
    lastWindowClosed = SIGNAL('lastWindowClosed()')
    layoutChanged = SIGNAL('layoutChanged()')
    loadFinished = SIGNAL('loadFinished(bool)')
    modelClicked = SIGNAL('activated (const QModelIndex &)')
    modelDoubleClicked = SIGNAL('doubleClicked (const QModelIndex &)')
    modelReset = SIGNAL('modelReset()')
    modified = SIGNAL('modified')
    openUrl = SIGNAL('openUrl(PyQt_PyObject)')
    processFinished = SIGNAL('finished(int, QProcess::ExitStatus)')
    requestedHistoricalData = SIGNAL('requestedHistoricalData')
    rowsInserted = SIGNAL('rowsInserted(const QModelIndex &, int, int)')
    selectionChanged = SIGNAL(
        'selectionChanged(const QItemSelection &, const QItemSelection &)')
    sessionCreated = SIGNAL('sessionCreated(PyQt_PyObject)')
    sessionItemSelected = SIGNAL('itemSelected (const QModelIndex &)')
    sessionItemActivated = SIGNAL('itemActivated (const QModelIndex &)')
    sessionReference = SIGNAL('sessionReference(PyQt_PyObject)')
    sessionRequest = SIGNAL('sessionRequest')
    sessionStatus = SIGNAL('sessionStatus')
    settingsChanged = SIGNAL('settingsChanged')
    splitterMoved = SIGNAL('splitterMoved(int, int)')
    standardItemChanged = SIGNAL('itemChanged(QStandardItem *)')
    strategyActivated = SIGNAL('strategyActivated(bool)')
    strategyLoaded = SIGNAL('strategyLoaded(PyQt_PyObject)')
    strategyLoadFailed = SIGNAL('strategyLoadFaield(PyQt_PyObject)')
    strategyFileUpdated = SIGNAL('strategyFileUpdated(PyQt_PyObject)')
    terminated = SIGNAL('terminated()')
    textChanged = SIGNAL('textChanged(const QString &)')
    textChangedEditor = SIGNAL('textChanged()')
    tickerClicked = SIGNAL('tickerClicked')
    timeout = SIGNAL('timeout()')
    triggered = SIGNAL('triggered()')
    zoomed = SIGNAL('zoomed(const QwtDoubleRect &)')

    neuralNetworkCreated = SIGNAL('neuralNetworkCreated')
    threadStarted = SIGNAL('started()')
    threadRunning = SIGNAL('running')
    threadFinished = SIGNAL('finished()')
    collectorActivate = SIGNAL('collectorActivate(PyQt_PyObject)')


class Slots:
    """ Contains SLOT attributes for easy and consistent reference.

    """
    scrollToBottom = SLOT('scrollToBottom()')
    expandItem = SLOT('expandItem(const QTreeWidgetItem *)')


class Settings(QSettings):
    """ Convenient replacement for QSettings.

    """
    class keys:
        """ Attributes are setting keys.

        """
        account = 'Account'
        app = 'Profit Workbench'
        appearance = 'Appearance'
        connection = 'Connection'
        designer = 'StrategyDesigner'
        main = 'MainWindow'
        maximized = 'Maximized'
        messages = 'Messages'
        org = 'ProfitPy'
        plots = 'Plots'
        position = 'Position'
        session = 'Session'
        size = 'Size'
        splitstate  = 'SplitterState'
        strategy = 'Strategy'
        tickerurls = 'TickerUrls'
        urls = 'Urls'
        strategy = 'Strategy'
        winstate = 'State'
        ctabstate = 'CentralTabState'
        externalbrowser = 'ExternalBrowser'

    def __init__(self):
        """ Constructor.

        """
        QSettings.__init__(self, self.keys.org, self.keys.app)

    def setValue(self, key, value):
        """ Sets value of setting

        @param key setting key as string
        @param value anything supported by QVariant constructor
        @return None
        """
        QSettings.setValue(self, key, QVariant(value))

    def setValueDump(self, key, value):
        self.setValue(key, dumps(value))

    def valueLoad(self, key, default=None):
        v = self.value(key, default=default)
        if v:
            try:
                v = loads(str(v.toString()))
            except:
                v = default
        return v

    def value(self, key, default=None):
        """ Returns value for key, or default if key doesn't exist.

        @param key setting key as string
        @param default value returned if key does not exist
        @return value of key or default
        """
        if default is None:
            default = QVariant()
        else:
            default = QVariant(default)
        return QSettings.value(self, key, default)


def roleId():
    i = Qt.UserRole
    while True:
        yield i
        i += 1
nextRoleId = roleId().next


class DataRoles:
    tickerId = nextRoleId()
    histDataReqId = nextRoleId()

    typeMap = {
        tickerId:int,
        histDataReqId:int,
        }


##
valueAlign = Qt.AlignRight | Qt.AlignVCenter


def nameIn(*names):
    def check(obj):
        try:
            return obj.typeName in names
        except (AttributeError, ):
            return False
    return check


instance = QCoreApplication.instance


class SessionHandler(object):
    """ Mixin to provide Qt objects and widgets basic session handling.

    Clients of this class should include it as a base class, then call
    'requestSession' to retrieve an existing session and connect to
    the 'sessionCreated' signal.
    """
    sessionRef = None

    def sessionGetter(self):
        return self.sessionRef

    def sessionSetter(self, value):
        session = self.sessionRef
        if session:
            for child in self.children() + [self, ]:
                session.deregisterMeta(child)
                try:
                    child.unsetSession()
                except (AttributeError, ):
                    pass
        logging.debug('Session set for %s to %s' % (self.objectName(), value))
        self.sessionRef = value

    session = property(sessionGetter, sessionSetter)

    def existingSession(self, session):
        """ Connects this object to an existing session instance.

        This method is provided so classes that mix in SessionHandler
        do not have to call the base class implementation of
        setSession.

        @param session Session instance
        @return None
        """
        self.disconnect(
            instance(), Signals.sessionReference, self.existingSession)
        if not session is self.session:
            self.setSession(session)

    def requestSession(self):
        """ Sends request for existing session.

        @return None
        """
        app = instance()
        connect = self.connect
        connect(app, Signals.sessionCreated, self.setSession)
        connect(app, Signals.sessionReference, self.existingSession)
        connect(self, Signals.sessionRequest, app, Signals.sessionRequest)
        self.emit(Signals.sessionRequest)

    def setSession(self, session):
        """ Default implementation sets session as attribute.

        Subclasses should reimplement this method.
        """
        self.session = session


class SettingsHandler(object):
    """ Provies late and automatic access to 'settings' attribute.

    """
    settingsRef = None

    def settingsGetter(self):
         settingsRef = self.settingsRef
         if not settingsRef:
             self.settingsRef = settingsRef = Settings()
         return settingsRef

    def settingsSetter(self, value):
        self.settingsRef = value

    settings = property(settingsGetter, settingsSetter)
