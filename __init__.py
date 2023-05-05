def classFactory(iface):
    if iface:
        from .datetimetools import DateTimeTools
        return DateTimeTools(iface)
    else:
        # This is used when the plugin is loaded from the command line command qgis_process
        from .datetimetoolsprocessing import DateTimeTools
        return DateTimeTools()
