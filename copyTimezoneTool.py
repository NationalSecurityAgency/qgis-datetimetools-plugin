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
from qgis.PyQt.QtCore import Qt
from qgis.PyQt.QtGui import QColor
from qgis.PyQt.QtWidgets import QApplication
from qgis.core import Qgis, QgsCoordinateTransform, QgsPointXY, QgsProject, QgsSettings, QgsPolygon, QgsMultiPolygon, QgsLineString, QgsGeometry
from qgis.gui import QgsMapToolEmitPoint, QgsVertexMarker, QgsRubberBand
from datetime import datetime
from zoneinfo import ZoneInfo
from pytz import timezone

from .settings import epsg4326, tzf_instance
# import traceback

class CopyTimeZoneTool(QgsMapToolEmitPoint):
    '''Class to interact with the map canvas to capture the coordinate
    when the mouse button is pressed and to display the coordinate in
    in the status bar.'''
    tzf = None
    last_tz = None

    def __init__(self, settings, iface):
        QgsMapToolEmitPoint.__init__(self, iface.mapCanvas())
        self.iface = iface
        self.settings = settings
        self.canvas = iface.mapCanvas()

        # Set up a polygon rubber band
        self.rubber = QgsRubberBand(self.canvas)
        self.rubber.setColor(QColor(255, 70, 0, 200))
        self.rubber.setWidth(3)
        self.rubber.setBrushStyle(Qt.NoBrush)

    def activate(self):
        '''When activated set the cursor to a crosshair.'''
        self.canvas.setCursor(Qt.CrossCursor)
        self.tzf = tzf_instance.getTZF()
        self.settings.show()

    def deactivate(self):
        self.last_tz = None
        self.rubber.reset()

    def formatMessage(self, pt):
        '''Format the coordinate string according to the settings from
        the settings dialog.'''
        # Make sure the coordinate is transformed to EPSG:4326
        canvasCRS = self.canvas.mapSettings().destinationCrs()
        if canvasCRS == epsg4326:
            pt4326 = pt
        else:
            transform = QgsCoordinateTransform(canvasCRS, epsg4326, QgsProject.instance())
            pt4326 = transform.transform(pt.x(), pt.y())
        try:
            tz_name = self.tzf.timezone_at(lng=pt4326.x(), lat=pt4326.y())
            mode = self.settings.mode()
            if mode == 1:
                msg = tz_name
            else:
                tz = ZoneInfo(tz_name)
                date = self.settings.date()
                loc_dt = datetime(date.year(), date.month(), date.day(), tzinfo=tz)
                offset = loc_dt.strftime('%z')
                if mode == 0:
                    msg = '{} ({})'.format(tz_name, offset)
                else:
                    msg = offset
        except Exception:
            # traceback.print_exc()
            msg = ''
            tz_name = ''
        if not msg:
            msg = ''
            tz_name = ''

        return (tz_name, msg)

    def canvasMoveEvent(self, event):
        '''Capture the coordinate as the user moves the mouse over
        the canvas. Show it in the status bar.'''
        pt = event.mapPoint()
        tz_name, msg = self.formatMessage(pt)
        if tz_name != self.last_tz:
            self.rubber.reset()
            self.last_tz = tz_name
            if tz_name != '':
                polygon = self.tzf.get_geometry(tz_name=tz_name)
                qgs_poly = tzf_to_qgis_polygon(polygon)
                canvasCRS = self.canvas.mapSettings().destinationCrs()
                if epsg4326 != canvasCRS:
                    to_canvas_crs = QgsCoordinateTransform(epsg4326, canvasCRS, QgsProject.instance())
                    qgs_poly.transform(to_canvas_crs)
                self.rubber.addGeometry(qgs_poly, None)
                self.rubber.show()
        self.iface.statusBarIface().showMessage(msg, 4000)

    def canvasReleaseEvent(self, event):
        '''Capture the coordinate when the mouse button has been released,
        format it, and copy it to the clipboard. pt is QgsPointXY'''
        pt = event.mapPoint()

        tz_name, msg = self.formatMessage(pt)
        if msg:
            clipboard = QApplication.clipboard()
            clipboard.setText(msg)
            self.iface.messageBar().pushMessage("", "'{}' copied to the clipboard".format(msg), level=Qgis.Info, duration=2)

def tzf_to_qgis_polygon(tzdata):
    if not tzdata or len(tzdata) < 1:
        return None
    multi_poly = QgsMultiPolygon()
    for tzpoly in tzdata:
        holes = []
        poly = QgsPolygon()
        for x, part in enumerate(tzpoly):
            if x == 0:
                outer_ls = QgsLineString(part[0], part[1])
                poly.setExteriorRing(outer_ls)
            else:
                hole_ls = QgsLineString(part[0], part[1])
                holes.append(hole_ls)
        poly.setInteriorRings(holes)
        multi_poly.addGeometry(poly)
    return(QgsGeometry(multi_poly))
