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
import enum
from qgis.PyQt.QtCore import Qt
from qgis.PyQt.QtGui import QIcon, QFont, QColor
from qgis.PyQt.QtWidgets import QDockWidget, QApplication
from qgis.PyQt.QtCore import pyqtSlot, Qt, QTime, QDate
from qgis.PyQt.uic import loadUiType
from qgis.core import Qgis, QgsPointXY, QgsLineString, QgsMultiPolygon, QgsPolygon, QgsGeometry, QgsCoordinateReferenceSystem, QgsCoordinateTransform, QgsProject
from qgis.gui import QgsRubberBand
import dateutil.parser
from dateutil.relativedelta import relativedelta
from datetime import datetime, MINYEAR
from zoneinfo import ZoneInfo, available_timezones
from .settings import epsg4326, tzf_instance
from .jdcal import MJD_0, gcal2jd, jd2gcal
from astral.sun import sun
import astral
import reverse_geocoder as rg
from geographiclib.geodesic import Geodesic
from .captureCoordinate import CaptureCoordinate
from .wintz import win_tz_map
from .util import parseDMSString

# import traceback

FORM_CLASS, _ = loadUiType(os.path.join(
    os.path.dirname(__file__), 'ui/dateTimeConverter.ui'))

@enum.unique
class Update(enum.Enum):
    ALL = -1
    DATE = 0
    TIME = 1
    EPOCH = 2
    EPOCHMS = 3
    UTC = 4
    TIME_ZONE = 5
    JULIAN = 6

geod = Geodesic.WGS84

DOW = ['Monday','Tuesday','Wednesday','Thursday','Friday','Saturday','Sunday']
class ConversionDialog(QDockWidget, FORM_CLASS):
    def __init__(self, iface, parent):
        super(ConversionDialog, self).__init__(parent)
        self.setupUi(self)
        self.iface = iface
        self.canvas = iface.mapCanvas()
        self.savedMapTool = None
        
        # Set up a polygon rubber band
        self.rubber = QgsRubberBand(self.canvas)
        self.rubber.setColor(QColor(255, 70, 0, 200))
        self.rubber.setWidth(3)
        self.rubber.setBrushStyle(Qt.NoBrush)
        
        self.tf = tzf_instance.getTZF()
        self.timeEdit.setDisplayFormat("HH:mm:ss")

        self.clipboard = QApplication.clipboard()
        font = self.sunTextEdit.font()
        font.setFamily("Courier New")
        self.sunTextEdit.setFont(font)

        # Set up a connection with the coordinate capture tool
        self.captureCoordinate = CaptureCoordinate(self.canvas)
        self.captureCoordinate.capturePoint.connect(self.capturedPoint)
        self.captureCoordinate.captureStopped.connect(self.stopCapture)
        self.coordCaptureButton.clicked.connect(self.startCapture)

        self.timezoneComboBox.view().setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.timezoneComboBox.addItems(sorted(available_timezones()))
        self.timezoneComboBox.currentIndexChanged.connect(self.timezone_changed)
        
        self.dateEdit.setCalendarPopup(True)
        self.coordCaptureButton.setIcon(QIcon(os.path.dirname(__file__) + "/images/coordCapture.svg"))
        self.currentDateTimeButton.setIcon(QIcon(os.path.dirname(__file__) + "/images/CurrentTime.png"))

        icon = QIcon(':/images/themes/default/algorithms/mAlgorithmCheckGeometry.svg')
        self.epochCommitButton.setIcon(icon)
        self.epochmsCommitButton.setIcon(icon)
        self.julianCommitButton.setIcon(icon)
        self.iso8601CommitButton.setIcon(icon)
        self.iso8601_2_CommitButton.setIcon(icon)
        self.coordCommitButton.setIcon(icon)

        icon = QIcon(':/images/themes/default/mActionEditCopy.svg')
        self.epochCopyButton.setIcon(icon)
        self.epochmsCopyButton.setIcon(icon)
        self.julianCopyButton.setIcon(icon)
        self.iso8601CopyButton.setIcon(icon)
        self.iso8601_2_CopyButton.setIcon(icon)
        self.dateDifferenceCopyButton.setIcon(icon)
        self.coordCopyButton.setIcon(icon)
        self.timezoneCopyButton.setIcon(icon)
        self.sunCopyButton.setIcon(icon)
        self.sunAzimuthCopyButton.setIcon(icon)
        self.sunElevationCopyButton.setIcon(icon)

        self.coordLineEdit.returnPressed.connect(self.on_coordCommitButton_pressed)
        self.epochLineEdit.returnPressed.connect(self.on_epochCommitButton_pressed)
        self.epochmsLineEdit.returnPressed.connect(self.on_epochmsCommitButton_pressed)
        self.julienLineEdit.returnPressed.connect(self.on_julianCommitButton_pressed)
        self.iso8601LineEdit.returnPressed.connect(self.on_iso8601CommitButton_pressed)
        self.iso8601_2_LineEdit.returnPressed.connect(self.on_iso8601_2_CommitButton_pressed)

    def showEvent(self, e):
        self.initSystemTime()
        self.updateDateTime()

    def closeEvent(self, e):
        if self.savedMapTool:
            self.canvas.setMapTool(self.savedMapTool)
            self.savedMapTool = None
        self.rubber.reset()
        QDockWidget.closeEvent(self, e)

    def initSystemTime(self):
        # print('initSystemTime')
        dt = datetime.now()
        dt = dt.astimezone()  # This returns the local timezone
        name = dt.tzname()
        if name in win_tz_map:
            name = win_tz_map[name]
        id = self.timezoneComboBox.findText(name,Qt.MatchExactly)
        if id == -1:
            offset = int(dt.utcoffset().total_seconds()/3600.0)
            name = 'Etc/GMT{:+d}'.format(-offset)
        self.dt_utc = datetime.now(ZoneInfo('UTC'))
        self.tz = ZoneInfo(name)

    def getLocalDateTime(self):
        # print('getLocalDateTime')
        dt = self.dt_utc.astimezone(self.tz)
        return(dt)

    def startCapture(self):
        # print('startCapture')
        if self.coordCaptureButton.isChecked():
            self.savedMapTool = self.canvas.mapTool()
            self.canvas.setMapTool(self.captureCoordinate)
        else:
            if self.savedMapTool:
                self.canvas.setMapTool(self.savedMapTool)
                self.savedMapTool = None

    @pyqtSlot(QgsPointXY)
    def capturedPoint(self, pt):
        if self.isVisible() and self.coordCaptureButton.isChecked():
            coord = '{}, {}'.format(pt.y(), pt.x())
            self.coordLineEdit.setText(coord)
            if self.setCoordinateTimezone(pt.y(), pt.x()):
                self.updateDateTime()

    @pyqtSlot()
    def stopCapture(self):
        self.coordCaptureButton.setChecked(False)
        self.rubber.reset()

    def setCoordinateTimezone(self, lat, lon):
        # print('setCorrdinateTimezone')
        tzname = self.tf.timezone_at(lng=lon, lat=lat)
        if tzname != None:
            polygon = self.tf.get_geometry(tz_name=tzname)
            qgs_poly = tzf_to_qgis_polygon(polygon)
            canvas_crs = self.canvas.mapSettings().destinationCrs()
            if epsg4326 != canvas_crs:
                to_canvas_crs = QgsCoordinateTransform(epsg4326, canvas_crs, QgsProject.instance())
                qgs_poly.transform(to_canvas_crs)
            self.rubber.reset()
            self.rubber.addGeometry(qgs_poly, None)
            self.rubber.show()
            
        if tzname:
            self.tz = ZoneInfo(tzname)
            dt = self.getLocalDateTime()
            self.dt_utc = dt.astimezone(ZoneInfo('UTC'))
            return(True)
        return(False)

    def updateDateTime(self, id=Update.ALL):
        # print('updateDateTime')
        if self.hourModeCheckBox.isChecked():
            self.timeEdit.setDisplayFormat("HH:mm:ss")
        else:
            self.timeEdit.setDisplayFormat("hh:mm:ss AP")
        dt = self.getLocalDateTime()
        # offset = int(dt.tzinfo.utcoffset(dt).total_seconds()/3600.0)
        offset = dt.strftime('%z')
        if id != Update.DATE:
            self.dateEdit.blockSignals(True)
            self.dateEdit.setDate(QDate(dt.year, dt.month, dt.day))
            self.dateEdit.blockSignals(False)
        if id != Update.TIME:
            self.timeEdit.blockSignals(True)
            self.timeEdit.setTime(QTime(dt.hour, dt.minute, dt.second, int(dt.microsecond / 1000)))
            self.timeEdit.blockSignals(False)
        if id != Update.EPOCH:
            try:
                sec = int((self.dt_utc - datetime.fromtimestamp(0,ZoneInfo('UTC'))).total_seconds())
            except Exception:
                sec = 'Undefined'
            self.epochLineEdit.setText('{}'.format(sec))
        if id != Update.EPOCHMS:
            try:
                msec = int((self.dt_utc - datetime.fromtimestamp(0,ZoneInfo('UTC'))).total_seconds()*1000.0)
            except Exception:
                msec = 'Undefined'
            self.epochmsLineEdit.setText('{}'.format(msec))
        if id != Update.TIME_ZONE:
            # This should always be true because we have forced the timezone to adhear to the list
            name = str(dt.tzinfo)
            id = self.timezoneComboBox.findText(name,Qt.MatchExactly)
            self.timezoneComboBox.blockSignals(True)
            self.timezoneComboBox.setCurrentIndex(id)
            self.timezoneComboBox.blockSignals(False)
        if id != Update.JULIAN:
            (val1, val2) = gcal2jd(dt.year,dt.month, dt.day)
            self.julienLineEdit.setText('{}'.format(val1 + val2))
            
        if id != Update.UTC:
            if dt.microsecond == 0:
                self.iso8601LineEdit.setText(self.dt_utc.strftime('%Y-%m-%dT%H:%M:%SZ'))
            else:
                self.iso8601LineEdit.setText(self.dt_utc.strftime('%Y-%m-%dT%H:%M:%S.%fZ'))

        tinfo = dt.timetuple()
        self.dayOfWeekLineEdit.setText(DOW[tinfo.tm_wday])
        self.doyLineEdit.setText('{}'.format(tinfo.tm_yday))

        # self.timezoneOffsetLineEdit.setText('{:+d}'.format(offset))
        self.timezoneOffsetLineEdit.setText(offset)
        
        self.updateTimeDelta()
        self.updateSunMoon()
        self.updateReverseGeo()
    
    def updateSunMoon(self):
        # print('updateSunMoon')
        try:
            (lat, lon) = parseDMSString(self.coordLineEdit.text().strip())
        except Exception:
            self.clearSun()
            return
        locl = astral.LocationInfo('','','',lat, lon)
        dt = self.getLocalDateTime()
        try:
            if self.displaySunUtcCheckBox.isChecked():
                s = sun(locl.observer, date=dt, tzinfo=ZoneInfo('UTC'))
            else:
                s = sun(locl.observer, date=dt, tzinfo=dt.tzinfo)
        except Exception:
            self.clearSun()
            return
        msg = []
        if self.displaySunUtcCheckBox.isChecked():
            fmt = '%Y-%m-%dT%H:%M:%SZ'
        else:
            fmt = '%Y-%m-%dT%H:%M:%S%z'
        for k,v in s.items():
            msg.append('{:>7}, {}'.format(k, v.strftime(fmt)))
        sunstr = '\n'.join(msg)
        self.sunTextEdit.clear()
        self.sunTextEdit.insertPlainText(sunstr)
        
        azimuth = astral.sun.azimuth(locl.observer, dt) 
        elev = astral.sun.elevation(locl.observer, dt) 
        
        self.sunAzimuthLineEdit.setText('{:.8f}'.format(azimuth))
        self.sunElevationLineEdit.setText('{:.8f}'.format(elev))
        
    def updateReverseGeo(self):
        try:
            (lat, lon) = parseDMSString(self.coordLineEdit.text().strip())
        except Exception:
            self.clearReverseGeo()
            return
        results = rg.search(((lat,lon)), mode=1)
        
        self.clearReverseGeo()
        str = '{}, {}, {}'.format(
            results[0]['cc'],
            results[0]['admin1'],
            results[0]['admin2'])
        self.reverseGeoLinedit.setText(str)
        
        # Get the azimuth and distance to the nearest know location
        l = geod.Inverse(lat, lon, float(results[0]['lat']), float(results[0]['lon']))
        heading = l['azi1']
        dist = l['s12'] / 1000.0 # put it in kilometers
        str = '{} {:.1f}° / {:.1f} km'.format(
            results[0]['name'],
            heading,
            dist)
        self.headingDistLineEdit.setText(str)

    def clearReverseGeo(self):
        self.reverseGeoLinedit.setText('')
        self.headingDistLineEdit.setText('')

    def clearSun(self):
        self.sunTextEdit.clear()
        self.sunAzimuthLineEdit.setText('')
        self.sunElevationLineEdit.setText('')
    
    def timezone_changed(self, index):
        tz_name = str(self.timezoneComboBox.itemText(index))
        self.tz = ZoneInfo(tz_name)
        dt = self.getLocalDateTime()
        self.dt_utc = dt.astimezone(ZoneInfo('UTC'))
        self.updateDateTime(Update.TIME_ZONE)
        
    def on_currentDateTimeButton_pressed(self):
        self.initSystemTime()
        self.coordLineEdit.setText('')
        self.updateDateTime()

    def on_hourModeCheckBox_stateChanged(self, state):
        if self.hourModeCheckBox.isChecked():
            self.timeEdit.setDisplayFormat("HH:mm:ss")
        else:
            self.timeEdit.setDisplayFormat("hh:mm:ss AP")

    def on_displaySunUtcCheckBox_stateChanged(self, state):
        self.updateSunMoon()
    
    def on_dateEdit_dateChanged(self, date):
        olddt = self.getLocalDateTime()
        dt = datetime(date.year(), date.month(), date.day(), olddt.hour, olddt.minute, olddt.second, olddt.microsecond, tzinfo=olddt.tzinfo)
        self.dt_utc = dt.astimezone(ZoneInfo('UTC'))
        self.updateDateTime(Update.DATE)
    
    def on_timeEdit_timeChanged(self, time):
        # print('on_timeEdit_timeChanged')
        olddt = self.getLocalDateTime()
        dt = datetime(olddt.year, olddt.month, olddt.day, time.hour(), time.minute(), time.second(), time.msec()*1000, tzinfo=olddt.tzinfo)
        self.dt_utc = dt.astimezone(ZoneInfo('UTC'))
        self.updateDateTime(Update.TIME)

    def on_coordCommitButton_pressed(self):
        # print('coordCommitButton Pressed')
        try:
            coord = self.coordLineEdit.text().strip()
            if not coord:
                self.clearSun()
                self.clearReverseGeo()
                return
            (lat, lon) = parseDMSString(coord)
            self.setCoordinateTimezone(lat, lon)
            self.updateDateTime()
        except Exception:
            self.iface.messageBar().pushMessage("", "Invalid 'latitude, longitude'", level=Qgis.Warning, duration=2)
            return

    def on_epochCommitButton_pressed(self):
        # print('epochCommitButton Pressed')
        try:
            epoch = long(self.epochLineEdit.text().strip())
        except Exception:
            return
        self.dt_utc = datetime.fromtimestamp(epoch, ZoneInfo('UTC'))
        self.updateDateTime(Update.EPOCH)
        
    def on_epochmsCommitButton_pressed(self):
        # print('epochmsCommitButton Pressed')
        try:
            epoch = long(self.epochmsLineEdit.text().strip()) / 1000.0
        except Exception:
            return
        self.dt_utc = datetime.fromtimestamp(epoch, ZoneInfo('UTC'))
        self.updateDateTime(Update.EPOCHMS)
        
    def on_julianCommitButton_pressed(self):
        # print('on_julianCommitButton_pressed Pressed')
        try:
            julian = float(self.julienLineEdit.text().strip()) - MJD_0
            date = jd2gcal(MJD_0, julian)
        except Exception:
            self.iface.messageBar().pushMessage("", "Invalid julian date", level=Qgis.Warning, duration=2)
            return
        olddt = self.getLocalDateTime()
        dt = datetime(date[0], date[1], date[2], olddt.hour, olddt.minute, olddt.second, olddt.microsecond)
        self.dt_utc = dt.astimezone(ZoneInfo('UTC'))
        self.updateDateTime(Update.JULIAN)
        
    def on_iso8601CommitButton_pressed(self):
        str = self.iso8601LineEdit.text().strip()
        if not str:
            return
        try:
            dt = dateutil.parser.parse(str, default=datetime(MINYEAR, 1, 1, hour=0, minute=0, second=0, microsecond=0, tzinfo=ZoneInfo('UTC')))
        except Exception:
            self.iface.messageBar().pushMessage("", "Invalid ISO8601 date and time", level=Qgis.Warning, duration=2)
            return
        self.dt_utc = dt.astimezone(ZoneInfo('UTC'))
        self.updateDateTime(Update.UTC)

    def on_iso8601_2_CommitButton_pressed(self):
        self.updateTimeDelta()
    
    def updateTimeDelta(self):
        str = self.iso8601_2_LineEdit.text().strip()
        if not str:
            return
        try:
            dt_delta = dateutil.parser.parse(str, default=datetime(MINYEAR, 1, 1, hour=0, minute=0, second=0, microsecond=0, tzinfo=ZoneInfo('UTC')))
        except Exception:
            self.iface.messageBar().pushMessage("", "Invalid ISO8601 date and time", level=Qgis.Warning, duration=2)
            return
        diff = relativedelta(dt_delta, self.dt_utc)
        msg = '{}y {}m {}d {}h {}m {}s {}uS'.format(diff.years, diff.months, diff.days, diff.hours, diff.minutes, diff.seconds, diff.microseconds)
        self.dtDeltaLineEdit.setText(msg)
        
    def on_timezoneCopyButton_pressed(self):
        s = str(self.timezoneComboBox.currentText())
        self.clipboard.setText(s)
        self.iface.messageBar().pushMessage("", "{} copied to the clipboard".format(s), level=Qgis.Info, duration=3)
        
    def on_coordCopyButton_pressed(self):
        s = self.coordLineEdit.text().strip()
        self.clipboard.setText(s)
        self.iface.messageBar().pushMessage("", "{} copied to the clipboard".format(s), level=Qgis.Info, duration=3)
        
    def on_epochCopyButton_pressed(self):
        s = self.epochLineEdit.text().strip()
        self.clipboard.setText(s)
        self.iface.messageBar().pushMessage("", "{} copied to the clipboard".format(s), level=Qgis.Info, duration=3)
        
    def on_epochmsCopyButton_pressed(self):
        s = self.epochmsLineEdit.text().strip()
        self.clipboard.setText(s)
        self.iface.messageBar().pushMessage("", "{} copied to the clipboard".format(s), level=Qgis.Info, duration=3)
        
    def on_julianCopyButton_pressed(self):
        s = self.julienLineEdit.text().strip()
        self.clipboard.setText(s)
        self.iface.messageBar().pushMessage("", "{} copied to the clipboard".format(s), level=Qgis.Info, duration=3)
        
    def on_iso8601CopyButton_pressed(self):
        s = self.iso8601LineEdit.text().strip()
        self.clipboard.setText(s)
        self.iface.messageBar().pushMessage("", "{} copied to the clipboard".format(s), level=Qgis.Info, duration=3)

    def on_iso8601_2_CopyButton_pressed(self):
        s = self.iso8601_2_LineEdit.text().strip()
        self.clipboard.setText(s)
        self.iface.messageBar().pushMessage("", "{} copied to the clipboard".format(s), level=Qgis.Info, duration=3)

    def on_dateDifferenceCopyButton_pressed(self):
        s = self.dtDeltaLineEdit.text().strip()
        self.clipboard.setText(s)
        self.iface.messageBar().pushMessage("", "{} copied to the clipboard".format(s), level=Qgis.Info, duration=3)
        
    def on_sunCopyButton_pressed(self):
        s = self.sunTextEdit.toPlainText().strip()
        self.clipboard.setText(s)
        self.iface.messageBar().pushMessage("", "Sun information copied to the clipboard", level=Qgis.Info, duration=3)
        
    def on_sunAzimuthCopyButton_pressed(self):
        s = self.sunAzimuthLineEdit.text().strip()
        self.clipboard.setText(s)
        self.iface.messageBar().pushMessage("", "{} copied to the clipboard".format(s), level=Qgis.Info, duration=3)
        
    def on_sunElevationCopyButton_pressed(self):
        s = self.sunElevationLineEdit.text().strip()
        self.clipboard.setText(s)
        self.iface.messageBar().pushMessage("", "{} copied to the clipboard".format(s), level=Qgis.Info, duration=3)

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
