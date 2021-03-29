import os
from qgis.core import QgsProcessingProvider
from qgis.PyQt.QtGui import QIcon
from .addtimezone import AddTimezoneAlgorithm
from .addastronomical import AddAstronomicalAlgorithm

class DateTimeToolsProvider(QgsProcessingProvider):

    def unload(self):
        QgsProcessingProvider.unload(self)

    def loadAlgorithms(self):
        self.addAlgorithm(AddAstronomicalAlgorithm())
        self.addAlgorithm(AddTimezoneAlgorithm())

    def icon(self):
        return QIcon(os.path.dirname(__file__) + '/images/DateTime.svg')

    def id(self):
        return 'datetimetools'

    def name(self):
        return 'Date/Time tools'

    def longName(self):
        return self.name()
