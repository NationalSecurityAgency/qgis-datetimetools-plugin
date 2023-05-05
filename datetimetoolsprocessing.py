# -*- coding: utf-8 -*-
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

