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
from datetime import datetime
from zoneinfo import ZoneInfo
from astral.sun import sun
from astral.location import LocationInfo

from qgis.core import (
    QgsPointXY, QgsFeature, QgsGeometry, QgsField,
    QgsProject, QgsWkbTypes, QgsCoordinateTransform)

from qgis.core import (
    QgsProcessing,
    QgsProcessingAlgorithm,
    QgsProcessingException,
    QgsProcessingParameterBoolean,
    QgsProcessingParameterDateTime,
    QgsProcessingParameterFeatureSource,
    QgsProcessingParameterFeatureSink)

from qgis.PyQt.QtGui import QIcon
from qgis.PyQt.QtCore import QVariant, QUrl

from .settings import epsg4326, tzf_instance

class AddAstronomicalAlgorithm(QgsProcessingAlgorithm):
    """
    Algorithm to time zone attribute.
    """

    PrmInputLayer = 'InputLayer'
    PrmUseUTC = 'UseUTC'
    PrmOutputLayer = 'OutputLayer'
    PrmDate = 'Date'
    PrmUseISO = 'UseISO'

    def initAlgorithm(self, config):
        self.addParameter(
            QgsProcessingParameterFeatureSource(
                self.PrmInputLayer,
                'Input point layer',
                [QgsProcessing.TypeVectorPoint])
        )
        self.addParameter(
            QgsProcessingParameterBoolean(
                self.PrmUseUTC,
                'Use UTC for date and time',
                True,
                optional=True)
        )
        self.addParameter(
            QgsProcessingParameterBoolean(
                self.PrmUseISO,
                'Use ISO8601 timestamps',
                False,
                optional=True)
        )
        self.addParameter(
            QgsProcessingParameterDateTime(
                self.PrmDate,
                'Select date for solar calculations',
                type=QgsProcessingParameterDateTime.Date,
                optional=False,
                )
        )
        self.addParameter(
            QgsProcessingParameterFeatureSink(
                self.PrmOutputLayer,
                'Output layer')
        )

    def processAlgorithm(self, parameters, context, feedback):
        source = self.parameterAsSource(parameters, self.PrmInputLayer, context)
        use_utc = self.parameterAsBool(parameters, self.PrmUseUTC, context)
        use_iso = self.parameterAsBool(parameters, self.PrmUseISO, context)
        dt = self.parameterAsDateTime(parameters, self.PrmDate, context)
        qdate = dt.date()
        if not qdate.isValid():
            raise QgsProcessingException('Use a proper date and rerun algorithm')
        date = datetime(qdate.year(), qdate.month(), qdate.day())
        
        fields = source.fields()
        src_crs = source.sourceCrs()
        if fields.append(QgsField("dawn", QVariant.String)) is False:
            raise QgsProcessingException("Field names must be unique. There is already a field named 'dawn'")
        if fields.append(QgsField("sunrise", QVariant.String)) is False:
            raise QgsProcessingException("Field names must be unique. There is already a field named 'sunrise'")
        if fields.append(QgsField("noon", QVariant.String)) is False:
            raise QgsProcessingException("Field names must be unique. There is already a field named 'noon'")
        if fields.append(QgsField("sunset", QVariant.String)) is False:
            raise QgsProcessingException("Field names must be unique. There is already a field named 'sunset'")
        if fields.append(QgsField("dusk", QVariant.String)) is False:
            raise QgsProcessingException("Field names must be unique. There is already a field named 'dusk'")

        (sink, dest_id) = self.parameterAsSink(
            parameters, self.PrmOutputLayer, context, fields,
            source.wkbType(), src_crs)

        if src_crs != epsg4326:
            transform = QgsCoordinateTransform(src_crs, epsg4326, QgsProject.instance())
        if use_iso:
            if use_utc:
                fmt = '%Y-%m-%dT%H:%M:%SZ'
            else:
                fmt = '%Y-%m-%dT%H:%M:%S%z'
        else:
            fmt = '%Y-%m-%d %H:%M:%S %Z%z'
        tzf = tzf_instance.getTZF()
        total = 100.0 / source.featureCount() if source.featureCount() else 0

        iterator = source.getFeatures()
        for cnt, feature in enumerate(iterator):
            if feedback.isCanceled():
                break
            f = QgsFeature()
            f.setGeometry(feature.geometry())
            pt = feature.geometry().asPoint()
            if src_crs != epsg4326:
                pt = transform.transform(pt)
            
            try:
                locl = LocationInfo('','','',pt.y(), pt.x())
                if use_utc:
                    s = sun(locl.observer, date=date)
                else:
                    tz_name = tzf.timezone_at(lng=pt.x(), lat=pt.y())
                    tz = ZoneInfo(tz_name)
                    loc_dt = date.replace(tzinfo=tz)
                    s = sun(locl.observer, date=date, tzinfo=tz)
                dawn = s["dawn"].strftime(fmt)
                sunrise = s["sunrise"].strftime(fmt)
                noon = s["noon"].strftime(fmt)
                sunset = s["sunset"].strftime(fmt)
                dusk = s["dusk"].strftime(fmt)
            except Exception:
                dawn = ""
                sunrise = ""
                noon = ""
                sunset = ""
                dusk = ""
            f.setAttributes(feature.attributes() + [dawn, sunrise, noon, sunset, dusk])
            sink.addFeature(f)

            if cnt % 100 == 0:
                feedback.setProgress(int(cnt * total))

        return {self.PrmOutputLayer: dest_id}

    def name(self):
        return 'addsunattributes'

    def displayName(self):
        return 'Add sun attributes'

    def icon(self):
        return QIcon(os.path.dirname(__file__) + '/images/sun.svg')

    def helpUrl(self):
        file = os.path.dirname(__file__) + '/index.html'
        if not os.path.exists(file):
            return ''
        return QUrl.fromLocalFile(file).toString(QUrl.FullyEncoded)

    def createInstance(self):
        return AddAstronomicalAlgorithm()
