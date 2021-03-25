import os
from qgis.core import QgsCoordinateReferenceSystem
from timezonefinder import TimezoneFinder


class InitTimeZoneFinder():
    tzf = None
    def getTZF(self):
        if not self.tzf:
            self.tzf = TimezoneFinder(bin_file_location=os.path.join(os.path.dirname(__file__), 'libs/timezonefinder'))
        return( self.tzf )
        
tzf_instance = InitTimeZoneFinder()


epsg4326 = QgsCoordinateReferenceSystem('EPSG:4326')
