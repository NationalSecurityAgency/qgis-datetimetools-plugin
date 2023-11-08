# -*- coding: utf-8 -*-
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
from qgis.core import QgsApplication

try:
    from timezonefinder import TimezoneFinder
    from astral.sun import sun
    import reverse_geocoder
    from .provider import DateTimeToolsProvider
    libraries_found = True
except Exception:
    libraries_found = False

class DateTimeTools(object):
    def __init__(self):
        self.provider = None

    def initProcessing(self):
        if libraries_found:
            self.provider = DateTimeToolsProvider()
            QgsApplication.processingRegistry().addProvider(self.provider)

    def initGui(self):
        self.initProcessing()

    def unload(self):
        if libraries_found:
            QgsApplication.processingRegistry().removeProvider(self.provider)

