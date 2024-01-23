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
import math
import datetime
from datetime import timezone
import dateutil.parser
import traceback

from qgis.core import (
    QgsPointXY, QgsFeature, QgsGeometry, QgsField,
    QgsProject, QgsWkbTypes)

from qgis.core import (
    QgsProcessing,
    QgsProcessingFeatureBasedAlgorithm,
    QgsProcessingException,
    QgsProcessingParameterBoolean,
    QgsProcessingParameterEnum,
    QgsProcessingParameterString,
    QgsProcessingParameterField
    )

from qgis.PyQt.QtGui import QIcon
from qgis.PyQt.QtCore import QVariant, QUrl, QDateTime, QDate

from .settings import epsg4326, tzf_instance

class ConvertDateTimeAlgorithm(QgsProcessingFeatureBasedAlgorithm):
    """
    Algorithm to time zone attribute.
    """

    PrmDateTimeField = 'DateTimeField'
    PrmInputDateTimeType = 'InputDateTimeType'
    PrmHintDayFirst = 'HintDayFirst'
    PrmHintYearFirst = 'HintYearFirst'
    PrmOutputDateTimeType = 'OutputDateTimeType'
    PrmAttributeName = 'AttributeName'
    PrmOutputLayer = 'OutputLayer'
    PrmTimezoneOptions = 'TimezoneOptions'
    PrmTimezones = 'Timezones'

    def createInstance(self):
        return ConvertDateTimeAlgorithm()

    def name(self):
        return 'convertdatetime'

    '''def icon(self):
        return QIcon(os.path.join(os.path.dirname(__file__), 'images/tzAttributes.svg'))'''

    def displayName(self):
        return 'Convert Date/Time'

    def outputName(self):
        return 'Converted layer'

    def helpUrl(self):
        file = os.path.dirname(__file__) + '/index.html'
        if not os.path.exists(file):
            return ''
        return QUrl.fromLocalFile(file).toString(QUrl.FullyEncoded)

    def inputLayerTypes(self):
        return [QgsProcessing.TypeVector]

    def outputWkbType(self, input_wkb_type):
        return (input_wkb_type)

    def outputFields(self, input_fields):
        if self.dt_output_type == 0:
            input_fields.append(QgsField(self.dt_name, QVariant.DateTime))
        elif self.dt_output_type == 1 or self.dt_output_type == 4:  # Either a datetime or date string
            input_fields.append(QgsField(self.dt_name, QVariant.String))
        elif self.dt_output_type == 2:
            input_fields.append(QgsField(self.dt_name, QVariant.Double))
        elif self.dt_output_type == 3:
            input_fields.append(QgsField(self.dt_name, QVariant.Date))
        return(input_fields)

    def supportInPlaceEdit(self, layer):
        return False

    def initParameters(self, config=None):
        self.addParameter(
            QgsProcessingParameterField(
                self.PrmDateTimeField,
                'Input date/time attribute field',
                parentLayerParameterName='INPUT',
                type=QgsProcessingParameterField.Any,
                optional=False)
        )
        self.addParameter(
            QgsProcessingParameterEnum(
                self.PrmInputDateTimeType,
                'Input date/time type',
                options=['Date/time or date object or string', 'Epoch (UNIX timestamp)'],
                defaultValue=0,
                optional=False)
        )
        self.addParameter(
            QgsProcessingParameterBoolean(
                self.PrmHintDayFirst,
                'String date/time hint: Day first',
                False,
                optional=True)
        )
        self.addParameter(
            QgsProcessingParameterBoolean(
                self.PrmHintYearFirst,
                'String date/time hint: Year first',
                False,
                optional=True)
        )
        '''self.addParameter(
            QgsProcessingParameterEnum(
                self.PrmTimezoneOptions,
                'Timezone options',
                options=['Ignore Timezone', 'UTC', 'Extract timezone from coordinate', 'Use one of the timezones below'],
                defaultValue=0,
                optional=False)
        )
        self.addParameter(
            QgsProcessingParameterEnum(
                self.PrmTimezones,
                'Optional timezones',
                options=all_timezones,
                defaultValue=0,
                optional=True)
        )'''
        self.addParameter(
            QgsProcessingParameterEnum(
                self.PrmOutputDateTimeType,
                'Output date/time type',
                options=['Date/time object', 'ISO8601 String', 'Epoch (UNIX timestamp)', 'Date object', 'Date string'],
                defaultValue=0,
                optional=False)
        )
        self.addParameter(
            QgsProcessingParameterString(
                self.PrmAttributeName,
                'Output date/time attribute name',
                defaultValue='datetime',
                optional=False)
        )

    def prepareAlgorithm(self, parameters, context, feedback):
        self.date_field = self.parameterAsString(parameters, self.PrmDateTimeField, context)
        feedback.pushInfo('Date Field: {}'.format(self.date_field))
        self.dt_input_type = self.parameterAsInt(parameters, self.PrmInputDateTimeType, context)
        self.dt_output_type = self.parameterAsInt(parameters, self.PrmOutputDateTimeType, context)
        self.hint_day_first = self.parameterAsBool(parameters, self.PrmHintDayFirst, context)
        self.hint_year_first = self.parameterAsBool(parameters, self.PrmHintYearFirst, context)
        self.dt_name = self.parameterAsString(parameters, self.PrmAttributeName, context)
        return True
        
    def processFeature(self, feature, context, feedback):
        dt = feature[self.date_field]
        try:
            if isinstance(dt, QDateTime):
                newdt = dt.toPyDateTime()
                dt_resolution = 4
            elif isinstance(dt, QDate):
                newdt = datetime(dt.year(), dt.month(), dt.day())
                dt_resolution = 3
            elif self.dt_input_type == 1:  # User has specified this is UNIX timestamp
                 newdt = datetime.fromtimestamp(float(dt), timezone.utc)
            elif isinstance(dt, str):
                d1 = dateutil.parser.parse(dt, dayfirst=self.hint_day_first, yearfirst=self.hint_year_first,
                    default=datetime.datetime(datetime.MINYEAR, 1, 1, hour=0, minute=0, second=0, microsecond=0, tzinfo=timezone.utc))
                d2 = dateutil.parser.parse(dt, dayfirst=self.hint_day_first, yearfirst=self.hint_year_first,
                    default=datetime.datetime(datetime.MINYEAR, 2, 2, hour=1, minute=1, second=1, microsecond=1, tzinfo=timezone.utc))
                dt_resolution = self.checkDateTime(d1, d2)
                newdt = d1
            else:
                newdt = None
                dt_resolution = 0
        except Exception:
            s = traceback.format_exc()
            feedback.pushInfo(s)
            newdt = None
            dt_resolution = 0

        attr = feature.attributes()
        if newdt == None:
            attr.append(None)
        elif self.dt_output_type == 0:
            qdt = QDateTime(newdt) 
            attr.append(qdt)
        elif self.dt_output_type == 1:  # ISO
            if newdt.tzinfo.utcoffset(newdt).total_seconds() == 0:
                s = newdt.strftime('%Y-%m-%dT%H:%M:%SZ')
            else:
                s = newdt.strftime('%Y-%m-%dT%H:%M:%S%z')
            # s = '{:04d}-{:02d}-{:02d}T{:02d}:{:02d}:{:02d}'.format(newdt.year, newdt.month, newdt.day, newdt.hour, newdt.minute, newdt.second)
            attr.append(s)
        elif self.dt_output_type == 2:  # UNIX Timestamp
            utc = newdt.astimezone(timezone.utc)
            dval = utc.timestamp()
            attr.append(dval)  # This will be a double floating point number
        elif self.dt_output_type == 3:  # Date object
            qdate = QDate(newdt.date())
            attr.append(qdate)
        elif self.dt_output_type == 4:  # Date string
            s = newdt.strftime('%Y-%m-%d')
            attr.append(s)
        feature.setAttributes(attr)
        
        return [feature]


    def checkDateTime(self, d1, d2):
        if d1.year == datetime.MINYEAR:
            return(0)
        dt_resolution = 1
        if d1.month != d2.month:
            return(dt_resolution)
        dt_resolution += 1
        if d1.day != d2.day:
            return(dt_resolution)
        dt_resolution += 1
        if d1.hour != d2.hour:
            return(dt_resolution)
        # We have a valid date and time
        dt_resolution += 1
        return(dt_resolution)
