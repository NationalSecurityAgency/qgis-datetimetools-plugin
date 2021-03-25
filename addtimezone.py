import os
import math
from datetime import datetime
from pytz import timezone
import pytz

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

class AddTimezoneAlgorithm(QgsProcessingAlgorithm):
    """
    Algorithm to time zone attribute.
    """

    PrmInputLayer = 'InputLayer'
    PrmOutputLayer = 'OutputLayer'
    PrmDate = 'Date'
    PrmAddOffset = 'AddOffset'

    def initAlgorithm(self, config):
        self.addParameter(
            QgsProcessingParameterFeatureSource(
                self.PrmInputLayer,
                'Input point layer',
                [QgsProcessing.TypeVectorPoint])
        )
        self.addParameter(
            QgsProcessingParameterBoolean(
                self.PrmAddOffset,
                'Add optional time zone offset for a particular date',
                False,
                optional=True)
        )
        self.addParameter(
            QgsProcessingParameterDateTime(
                self.PrmDate,
                'Select date for time zone offset calculation',
                type=QgsProcessingParameterDateTime.Date,
                optional=True,
                )
        )
        self.addParameter(
            QgsProcessingParameterFeatureSink(
                self.PrmOutputLayer,
                'Output layer')
        )

    def processAlgorithm(self, parameters, context, feedback):
        source = self.parameterAsSource(parameters, self.PrmInputLayer, context)
        add_offset = self.parameterAsBool(parameters, self.PrmAddOffset, context)
        dt = self.parameterAsDateTime(parameters, self.PrmDate, context)
        qdate = dt.date()
        if add_offset and not qdate.isValid():
            raise QgsProcessingException('Use a proper date and rerun algorithm')
        
        fields = source.fields()
        src_crs = source.sourceCrs()
        if fields.append(QgsField("tzid", QVariant.String)) is False:
            raise QgsProcessingException("Field names must be unique. There is already a field named 'tzid'")
        if add_offset:
            if fields.append(QgsField("tz_offset", QVariant.String)) is False:
                raise QgsProcessingException("Field names must be unique. There is already a field named 'tz_offset'")

        (sink, dest_id) = self.parameterAsSink(
            parameters, self.PrmOutputLayer, context, fields,
            source.wkbType(), src_crs)

        if src_crs != epsg4326:
            transform = QgsCoordinateTransform(src_crs, epsg4326, QgsProject.instance())
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
                msg = tzf.timezone_at(lng=pt.x(), lat=pt.y())
            except Exception:
                msg = None
            if not msg:
                msg = ''
            if add_offset:
                if msg:
                    tz = timezone(msg)
                    loc_dt = tz.localize(datetime(qdate.year(), qdate.month(), qdate.day()))
                    offset = loc_dt.strftime('%z')
                else:
                    offset = ''
                f.setAttributes(feature.attributes() + [msg, offset])
            else:
                f.setAttributes(feature.attributes() + [msg])
            sink.addFeature(f)

            if cnt % 100 == 0:
                feedback.setProgress(int(cnt * total))

        return {self.PrmOutputLayer: dest_id}

    def name(self):
        return 'addtimezoneattributes'

    '''def icon(self):
        return QIcon(os.path.join(os.path.dirname(__file__), 'images/rose.png'))'''

    def displayName(self):
        return 'Add time zone attributes'

    def group(self):
        return 'Tools'

    def groupId(self):
        return 'tools'

    def helpUrl(self):
        file = os.path.dirname(__file__) + '/index.html'
        if not os.path.exists(file):
            return ''
        return QUrl.fromLocalFile(file).toString(QUrl.FullyEncoded)

    def createInstance(self):
        return AddTimezoneAlgorithm()
