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
