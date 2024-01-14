#!/usr/bin/env python
import os
import sys
sys.path.append('../lib')
import setup_paths
paths=setup_paths.paths
import obspy
from urllib.request import urlretrieve
lat = 60 + 29/60 + 4.19/3600
lon = - (152 + 44/60 + 20.99/3600)
source = {'lat':lat, 'lon':lon}
maxRadius = 0.5
net = 'RD'
invfile = os.path.join(paths['RESPONSE_DIR'],f"{net}.xml")
sdate = obspy.core.UTCDateTime(2008,1,1)
edate = obspy.core.UTCDateTime(2010,1,1)

'''
server = "service.iris.edu"
url = f"https://{server}/fdsnws/station/1/query?starttime={sdate.isoformat() }&endtime={edate.isoformat() }&latitude={source['lat']}&longitude={source['lon']}&maxradius={maxRadius}"
print(url)
urlretrieve(url=url, filename=invfile)
'''

from obspy.clients.fdsn.client import Client
client = Client("IRIS")
inv = client.get_stations( \
    starttime=sdate, endtime=edate, \
    latitude="%.4f" % source['lat'], longitude="%.4f" % source['lon'], maxradius="%.1f" % maxRadius, \
    level="response")
inv.write(invfile, format = 'stationxml')

import pipelines
startt = obspy.core.UTCDateTime(2009, 3, 20, 0, 0, 0)
endt = obspy.core.UTCDateTime(2009, 3, 24, 0, 0, 0)
#dbout = os.path.join(paths['DB_DIR'],f"dbWhakaari{startt.year}")
sampling_interval = 60 # seconds
Q=None
ext='pickle'
pipelines.small_sausage(paths, startt, endt, sampling_interval=sampling_interval, source=source, invfile=invfile, Q=Q, ext=ext, net=net)

