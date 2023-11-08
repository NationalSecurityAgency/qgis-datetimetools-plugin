"""
/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
"""
import os
import re

from qgis.PyQt.uic import loadUiType
from qgis.PyQt.QtGui import QIcon
from qgis.PyQt.QtWidgets import QDockWidget

from datetime import datetime
from dateutil.tz import tzlocal
from qgis.PyQt.QtCore import QDate

# import traceback

FORM_CLASS, _ = loadUiType(os.path.join(
    os.path.dirname(__file__), 'ui/copyModeSettings.ui'))


class CopyModeSettings(QDockWidget, FORM_CLASS):

    def __init__(self, iface, parent):
        super(CopyModeSettings, self).__init__(parent)
        self.setupUi(self)
        self.comboBox.addItems(['Time zone & offset', 'Time zone', 'Offset'])
        self.dateEdit.setCalendarPopup(True)
        tz = tzlocal()
        dt = datetime.now(tz)
        self.dateEdit.setDate(QDate(dt.year, dt.month, dt.day))

    def mode(self):
        mode = int(self.comboBox.currentIndex())
        return(mode)
        
    def date(self):
        return(self.dateEdit.date())