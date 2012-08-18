#!/usr/bin/env python
import gps, os, time, sys, thread, socket

lat = 0.0
lon = 0.0
lochist = []
kisbssids = {}

def kisthread():
	print "connecting to kismet"
	sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	sock.connect(("127.0.0.1",2501))
	sockfd = sock.makefile()
	sock.send("!0 enable BSSID bssid,bestlat,bestlon,freqmhz\n")
	sock.send("!0 enable SSID ssid,mac\n")
	while 1:
		data = sockfd.readline()
		data = data.split(" ",1)
		if data[0] == "*BSSID:":
			parsedata = data[1][:-1].split(" ")
			bssid = parsedata[0]
			if not bssid == "FF:FF:FF:FF:FF:FF":
				if not bssid in kisbssids: 			
					kisbssids[parsedata[0]] = {}
					kisbssids[parsedata[0]]['ssid'] = ""
				netentry = kisbssids[parsedata[0]]
				netentry['lat'] = parsedata[1]
				netentry['lon'] = parsedata[2]
				netentry['chan'] = parsedata[3]
		elif data[0] == "*SSID:":
			parsedata = data[1][:-1].split("\x01")[1:]
			bssid = parsedata[1][1:-1]
			if not bssid == "FF:FF:FF:FF:FF:FF":
				if not bssid in kisbssids:
					print "BSSID %s not found!" % bssid
				kisbssids[bssid]['ssid'] = parsedata[0]


def outputKML():
	header = """<?xml version="1.0" encoding="UTF-8"?>
<kml xmlns="http://www.opengis.net/kml/2.2" xmlns:gx="http://www.google.com/kml/ext/2.2" xmlns:kml="http://www.opengis.net/kml/2.2" xmlns:atom="http://www.w3.org/2005/Atom">
<Document>
	<Style id="livepos">
		<IconStyle>
			<scale>1.2</scale>
			<Icon>
				<href>http://maps.google.com/mapfiles/kml/shapes/placemark_circle.png</href>
			</Icon>
		</IconStyle>
		<LineStyle>
			<color>ff00ff00</color>
			<width>4</width>
		</LineStyle>
	</Style>
	<Style id="network">
		<IconStyle>
			<color>ff0000ff</color>
			<scale>1.2</scale>
			<Icon>
				<href>http://maps.google.com/mapfiles/kml/shapes/open-diamond.png</href>
			</Icon>
		</IconStyle>
	</Style>"""
	placemark = """	<Placemark>
		<name>Current Location</name>
		<styleUrl>#livepos</styleUrl>
		<Point>
			<altitudeMode>clampToGround</altitudeMode>
			<gx:altitudeMode>clampToSeaFloor</gx:altitudeMode>
			<coordinates>%f,%f,0</coordinates>
		</Point>
	</Placemark>""" % (lon,lat)
	lochist_s = """	<Placemark>
		<name>Location History</name>
		<styleUrl>#livepos</styleUrl>
		<LineString>
			<tessellate>1</tessellate>
			<coordinates>"""
	for loc in lochist:
		lochist_s += "%f,%f,0 " % (loc[1],loc[0])
	lochist_s += """			</coordinates>
		</LineString>
	</Placemark>"""
	networksfolder = """	<Folder>
		<name>Networks</name>"""
	for network in kisbssids.keys():
		networksfolder += """<Placemark>
		<name>%s</name>
		<styleUrl>#network</styleUrl>
		<Point>
			<altitudeMode>clampToGround</altitudeMode>
			<gx:altitudeMode>clampToSeaFloor</gx:altitudeMode>
			<coordinates>%s,%s,0</coordinates>
		</Point>
	</Placemark>
		""" % (kisbssids[network]['ssid'], kisbssids[network]['lon'], kisbssids[network]['lat'])
	networksfolder += """
	</Folder>
	"""

	footer = """</Document>
</kml>"""
	return header + placemark + lochist_s + networksfolder + footer

session = gps.gps()
session.stream(gps.WATCH_ENABLE|gps.WATCH_NEWSTYLE)
thread.start_new_thread(kisthread,())
for report in session:
	if 'lat' in report:
		lat = report['lat']
		lon = report['lon']
		lochist += [(lat,lon)]
		kmldata = outputKML()
		f = open("/tmp/livemap.kml",'w')
		f.write(kmldata)
		f.close()
