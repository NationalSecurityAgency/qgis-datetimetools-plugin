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
from qgis.PyQt.QtCore import QUrl, Qt
from qgis.PyQt.QtGui import QIcon
from qgis.PyQt.QtWidgets import QAction, QMessageBox
from qgis.core import QgsApplication
import processing

import os

try:
    from timezonefinder import TimezoneFinder
    from astral.sun import sun
    import reverse_geocoder
    from .provider import DateTimeToolsProvider
    libraries_found = True
except Exception:
    libraries_found = False

class DateTimeTools(object):
    captureTzTool = None
    copyModeSettings = None
    def __init__(self, iface):
        self.iface = iface
        self.canvas = iface.mapCanvas()
        self.conversionDialog = None
        if libraries_found:
            self.provider = DateTimeToolsProvider()

    def initGui(self):
        if libraries_found:
            self.toolbar = self.iface.addToolBar('Date/Time Tools Toolbar')
            self.toolbar.setObjectName('DateTimeToolsToolbar')
            """Create the menu & tool bar items within QGIS"""
            icon = QIcon(os.path.dirname(__file__) + "/images/DateTime.svg")
            self.conversionAction = QAction(icon, "Date/Time Conversion", self.iface.mainWindow())
            self.conversionAction.triggered.connect(self.showConversionDialog)
            self.conversionAction.setCheckable(False)
            self.iface.addPluginToMenu("Date/Time Tools", self.conversionAction)
            self.toolbar.addAction(self.conversionAction)

            # Add Interface for Time Zone Capturing
            icon = QIcon(os.path.dirname(__file__) + "/images/tzCapture.svg")
            self.copyTZAction = QAction(icon, "Copy/Display Time Zone", self.iface.mainWindow())
            self.copyTZAction.triggered.connect(self.startTZCapture)
            self.copyTZAction.setCheckable(True)
            self.toolbar.addAction(self.copyTZAction)
            self.iface.addPluginToMenu("Date/Time Tools", self.copyTZAction)

            icon = QIcon(os.path.dirname(__file__) + "/images/sun.svg")
            self.addSunAction = QAction(icon, 'Add sun attributes', self.iface.mainWindow())
            self.addSunAction.triggered.connect(self.addSunAttributes)
            self.toolbar.addAction(self.addSunAction)
            self.iface.addPluginToMenu('Date/Time Tools', self.addSunAction)

            icon = QIcon(os.path.dirname(__file__) + "/images/tzAttributes.svg")
            self.addTZAction = QAction(icon, 'Add time zone attributes', self.iface.mainWindow())
            self.addTZAction.triggered.connect(self.addTimeZoneAttributes)
            self.toolbar.addAction(self.addTZAction)
            self.iface.addPluginToMenu('Date/Time Tools', self.addTZAction)
        else:
            icon = QIcon(":images/themes/default/mIndicatorBadLayer.svg")
            self.requirementsActions = QAction(icon, "Required python libraries not installed", self.iface.mainWindow())
            self.requirementsActions.triggered.connect(self.requirements)
            self.iface.addPluginToMenu("Date/Time Tools", self.requirementsActions)
        
        # Help
        icon = QIcon(os.path.dirname(__file__) + '/images/help.svg')
        self.helpAction = QAction(icon, "Help", self.iface.mainWindow())
        self.helpAction.triggered.connect(self.help)
        self.iface.addPluginToMenu('Date/Time Tools', self.helpAction)

        if libraries_found:
            self.canvas.mapToolSet.connect(self.resetTools)

            # Add the processing provider
            QgsApplication.processingRegistry().addProvider(self.provider)

    def unload(self):
        """Remove the plugin menu item and icon from QGIS GUI."""
        if libraries_found:
            self.iface.removePluginMenu('Date/Time Tools', self.conversionAction)
            self.iface.removeToolBarIcon(self.conversionAction)
            self.iface.removePluginMenu('Date/Time Tools', self.copyTZAction)
            self.iface.removeToolBarIcon(self.copyTZAction)
            self.iface.removePluginMenu('Date/Time Tools', self.addSunAction)
            self.iface.removeToolBarIcon(self.addSunAction)
            self.iface.removePluginMenu('Date/Time Tools', self.addTZAction)
            self.iface.removeToolBarIcon(self.addTZAction)
            del self.toolbar
            QgsApplication.processingRegistry().removeProvider(self.provider)
        else:
            self.iface.removePluginMenu('Date/Time Tools', self.requirementsActions)

        self.iface.removePluginMenu('Date/Time Tools', self.helpAction)
        if self.conversionDialog:
            self.iface.removeDockWidget(self.conversionDialog)
            self.conversionDialog = None
        self.captureTzTool = None
        if self.copyModeSettings:
            self.iface.removeDockWidget(self.copyModeSettings)
        self.copyModeSettings = None
            

    def requirements(self):
        message = '''
        <p>This plugin requires <a href="https://timezonefinder.readthedocs.io/en/latest/">TimeZoneFinder</a>, <a href="https://sffjunkie.github.io/astral/">Astral</a>, and <a href="https://pypi.org/project/reverse_geocoder/">reverse_geocoder</a> libraries.<br/><br/>
        These libraries can be installed by running the OSGeo4W shell and running 'pip install timezonefinder astral' and then 'pip install reverse_geocoder' or whatever method you use to install python packages. To avoid some problems 'pip install reverse_geocoder' separately. If you run the OSGeo4W shell as a system administrator the libraries will installed in the core OSGeo4W Python distribution; otherwise, they will be installed locally.<p>
        <p>Once the libraries are installed, please restart QGIS.</p>
        '''
        QMessageBox.information(self.iface.mainWindow(), 'Plugin Requirements not Satisfied', message)

    def resetTools(self, newtool, oldtool):
        '''Uncheck the Copy Lat Lon tool'''
        try:
            if self.captureTzTool and (oldtool is self.captureTzTool):
                self.copyTZAction.setChecked(False)
            if newtool is self.captureTzTool:
                self.copyTZAction.setChecked(True)
        except Exception:
            pass

    def addSunAttributes(self):
        processing.execAlgorithmDialog('datetimetools:addsunattributes', {})

    def addTimeZoneAttributes(self):
        processing.execAlgorithmDialog('datetimetools:addtimezoneattributes', {})

    def showConversionDialog(self):
        """Display the KML Dialog window."""
        if not self.conversionDialog:
            from .conversionDialog import ConversionDialog
            self.conversionDialog = ConversionDialog(self.iface, self.iface.mainWindow())
            self.conversionDialog.setFloating(True)
            self.iface.addDockWidget(Qt.RightDockWidgetArea, self.conversionDialog)
        self.conversionDialog.show()

    def startTZCapture(self):
        if self.copyModeSettings is None:
            from .copyModeSettings import CopyModeSettings
            self.copyModeSettings = CopyModeSettings(self.iface, self.iface.mainWindow())
            self.iface.addDockWidget(Qt.LeftDockWidgetArea, self.copyModeSettings)
        if self.captureTzTool is None:
            from .copyTimezoneTool import CopyTimeZoneTool
            self.captureTzTool = CopyTimeZoneTool(self.copyModeSettings, self.iface)
        self.canvas.setMapTool(self.captureTzTool)

    def help(self):
        '''Display a help page'''
        import webbrowser
        url = QUrl.fromLocalFile(os.path.dirname(__file__) + "/index.html").toString()
        webbrowser.open(url, new=2)


