# Date/Time Tools Plugin

The QGIS Date/Time Tools plugin provides date and time conversions between various formats and time zones. Formats include ISO8601 dates and times, Julian dates, and Unix timestamps (Epoch). It can calculate the difference between two different dates. It provides the ability to select a time zone from a list or by clicking on the map. At this point, there is just one tool called the **Date/Time Conversion** tool.

<div style="text-align:center"><img src="doc/datetimeconversion.jpg" alt="Date/Time Conversion"></div>

* <img src="images/CurrentTime.png" width=24 height=24 alt="Update date and time"> ***Update with system time***. Clicking on this button updates the date and time to the current system date, time, and time zone.
* <img src="images/coordCapture.svg" alt="Select location and time zone"> ***Select location and time zone***. Clicking on this button allows the user to click anywhere on the QGIS canvas to snapshot the latitude, longitude, and time zone at that location.
* <img src="doc/check.png" alt="Accept changes"> ***Accept changes***. Clicking on this button accepts the changes in the text box next to it and updates the entire dialog box.
* <img src="doc/copycontents.png" alt="Copy contents"> ***Copy to clipboard***. Clicking on this button copies the associated text onto the clipboard.

A second date and time can be entered for ISO8601_2 in order to calculate the difference between it and ISO8601_1. Once a latitude and longitude has been specified, information about solar times of dawn, sunrise, noon, sunset, and dusk will be displayed as well as the sun azimuth/direction and elevation from the horizon.

## Future development may include the following

* Include lunar information.
* Replace the python astral library with the Skyfield library for more precision.
* Another tool that allows the user to click on a location on the earth, display the time zone, and the time zone polygon on the map.
* Another tool that shows the position of the sun where it appears directly overhead.
* Another tool to display the path of the sun over a 24 hour period with night and day areas.