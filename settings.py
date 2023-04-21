import os
from qgis.core import QgsCoordinateReferenceSystem
from timezonefinder.timezonefinder import TimezoneFinder


class InitTimeZoneFinder():
    tzf = None
    def getTZF(self):
        if not self.tzf:
            self.tzf = TimezoneFinder()
        return( self.tzf )
        
tzf_instance = InitTimeZoneFinder()


epsg4326 = QgsCoordinateReferenceSystem('EPSG:4326')
