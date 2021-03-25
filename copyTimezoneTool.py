from qgis.PyQt.QtCore import Qt
from qgis.PyQt.QtGui import QColor
from qgis.PyQt.QtWidgets import QApplication
from qgis.core import Qgis, QgsCoordinateTransform, QgsPointXY, QgsProject, QgsSettings, QgsPolygon, QgsMultiPolygon, QgsLineString, QgsGeometry
from qgis.gui import QgsMapToolEmitPoint, QgsVertexMarker, QgsRubberBand

from .settings import epsg4326, tzf_instance
# import traceback

class CopyTimeZoneTool(QgsMapToolEmitPoint):
    '''Class to interact with the map canvas to capture the coordinate
    when the mouse button is pressed and to display the coordinate in
    in the status bar.'''
    tzf = None
    last_tz = None

    def __init__(self, iface):
        QgsMapToolEmitPoint.__init__(self, iface.mapCanvas())
        self.iface = iface
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
        print('x {} y {}'.format(pt4326.x(), pt4326.y()))
        try:
            msg = self.tzf.timezone_at(lng=pt4326.x(), lat=pt4326.y())
        except Exception:
            msg = ''
        if not msg:
            msg = ''

        return msg

    def canvasMoveEvent(self, event):
        '''Capture the coordinate as the user moves the mouse over
        the canvas. Show it in the status bar.'''
        pt = event.mapPoint()
        msg = self.formatMessage(pt)
        if msg != self.last_tz:
            self.rubber.reset()
            self.last_tz = msg
            if msg != '':
                polygon = self.tzf.get_geometry(tz_name=msg)
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

        msg = self.formatMessage(pt)
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
