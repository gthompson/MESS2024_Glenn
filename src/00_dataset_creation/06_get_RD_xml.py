#!/usr/bin/env python
import os
from obspy import UTCDateTime
from urllib.request import urlretrieve
paths = {}
paths['RESPONSE_DIR'] = "."
lat = 60 + 29/60 + 4.19/3600
lon = - (152 + 44/60 + 20.99/3600)
sdate = UTCDateTime(2008,1,1).strftime('%Y-%m-%d') 
edate = UTCDateTime(2010,1,1).strftime('%Y-%m-%d') 
url = f"https://service.iris.edu/fdsnws/station/1/query?startafter={sdate}&endbefore={edate}&minlatitude={lat-1}&maxlatitude={lat+1}&minlongitude={lon-1}&maxlongitude={lon+1}"
urlretrieve(url=url, filename=os.path.join(paths['RESPONSE_DIR'],'RD.xml'))