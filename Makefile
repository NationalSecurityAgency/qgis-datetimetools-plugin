PLUGINNAME = datetimetools
PLUGINS = "$(HOME)"/AppData/Roaming/QGIS/QGIS3/profiles/default/python/plugins/$(PLUGINNAME)
PY_FILES = datetimetools.py __init__.py conversionDialog.py copyTimezoneTool.py captureCoordinate.py jdcal.py util.py wintz.py settings.py provider.py addtimezone.py copyModeSettings.py addastronomical.py
EXTRAS = metadata.txt icon.png

deploy:
	mkdir -p $(PLUGINS)
	cp -vf $(PY_FILES) $(PLUGINS)
	cp -vf $(EXTRAS) $(PLUGINS)
	cp -vrf images $(PLUGINS)
	cp -vrf ui $(PLUGINS)
	cp -vfr doc $(PLUGINS)
#	cp -vrf libs $(PLUGINS)
	cp -vf helphead.html index.html
	python -m markdown -x extra readme.md >> index.html
	echo '</body>' >> index.html
	cp -vf index.html $(PLUGINS)/index.html
