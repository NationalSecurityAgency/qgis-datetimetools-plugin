PLUGINNAME = datetimetools
PLUGINS = "$(HOME)"/AppData/Roaming/QGIS/QGIS3/profiles/default/python/plugins/$(PLUGINNAME)
PY_FILES = datetimetools.py __init__.py conversionDialog.py copyTimezoneTool.py captureCoordinate.py jdcal.py util.py wintz.py settings.py provider.py addtimezone.py copyModeSettings.py
EXTRAS = metadata.txt icon.png

deploy:
	mkdir -p $(PLUGINS)
	cp -vf $(PY_FILES) $(PLUGINS)
	cp -vf $(EXTRAS) $(PLUGINS)
	cp -vrf images $(PLUGINS)
	cp -vrf ui $(PLUGINS)
#	cp -vrf libs $(PLUGINS)
