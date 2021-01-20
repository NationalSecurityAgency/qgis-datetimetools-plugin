# -*- coding: utf-8 -*-
"""
/***************************************************************************
 KMLTools
    A QGIS plugin for importing KML into simple points, lines, and polygons.
    It ignores KML styling.
                              -------------------
        begin                : 2020-11-06
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
"""
from qgis.PyQt.QtCore import QUrl
from qgis.PyQt.QtGui import QIcon
from qgis.PyQt.QtWidgets import QAction
from qgis.core import QgsApplication

import os

class DateTimeTools(object):
    def __init__(self, iface):
        self.iface = iface
        self.canvas = iface.mapCanvas()
        self.conversionDialog = None
        self.toolbar = self.iface.addToolBar('Date/Time Tools Toolbar')
        self.toolbar.setObjectName('DateTimeToolsToolbar')

    def initGui(self):
        """Create the menu & tool bar items within QGIS"""
        icon = QIcon(os.path.dirname(__file__) + "/images/dateTime.png")
        self.conversionAction = QAction(icon, "Date/Time Conversion", self.iface.mainWindow())
        self.conversionAction.triggered.connect(self.showConversionDialog)
        self.conversionAction.setCheckable(False)
        self.iface.addPluginToMenu("Date/Time Tools", self.conversionAction)
        self.toolbar.addAction(self.conversionAction)

    def unload(self):
        """Remove the plugin menu item and icon from QGIS GUI."""
        self.iface.removePluginMenu('Date/Time Tools', self.conversionAction)
        self.iface.removeToolBarIcon(self.conversionAction)
        del self.toolbar
        if self.conversionDialog:
            self.iface.removeDockWidget(self.conversionDialog)
            conversionDialog = None
            

    def showConversionDialog(self):
        """Display the KML Dialog window."""
        if not self.conversionDialog:
            from .conversionDialog import ConversionDialog
            self.conversionDialog = ConversionDialog(self.iface, self.iface.mainWindow())
            self.conversionDialog.setFloating(True)
        self.conversionDialog.show()
