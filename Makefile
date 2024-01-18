PLUGINNAME = datetimetools
PLUGINS = "$(HOME)"/AppData/Roaming/QGIS/QGIS3/profiles/default/python/plugins/$(PLUGINNAME)
PY_FILES = __init__.py addastronomical.py addtimezone.py captureCoordinate.py conversionDialog.py copyModeSettings.py copyTimezoneTool.py datetimetoolsprocessing.py datetimetools.py jdcal.py provider.py settings.py util.py wintz.py
EXTRAS = metadata.txt icon.png LICENSE

deploy:
	mkdir -p $(PLUGINS)
	cp -vf $(PY_FILES) $(PLUGINS)
	cp -vf $(EXTRAS) $(PLUGINS)
	cp -vrf images $(PLUGINS)
	cp -vrf ui $(PLUGINS)
	cp -vfr doc $(PLUGINS)
	cp -vf helphead.html index.html
	python -m markdown -x extra readme.md >> index.html
	echo '</body>' >> index.html
	cp -vf index.html $(PLUGINS)/index.html
