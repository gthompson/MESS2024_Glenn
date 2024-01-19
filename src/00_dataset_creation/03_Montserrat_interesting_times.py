#!/usr/bin/env python
# coding: utf-8

import os
import sys
import obspy
sys.path.append('../../src/lib')
import setup_paths
paths = setup_paths.paths
import pipelines

# Montserrat data from Seisan archive
seisandbdir =  '/data/SEISAN_DB/WAV/DSNC_'
net = 'MV'
invfile = os.path.join(paths['RESPONSE_DIR'],f"{net}.xml")
startt = [
    (1997, 12, 24),
    (2000, 3, 19),
    (2001, 2, 25), 
    (2001, 7, 27),
    (2003, 7, 12),
    ]
endt = [
    (1997, 12, 28),
    (2000, 3, 22),
    (2001, 3, 5),
    (2001, 7, 31),
    (2003, 7, 16),
    ]
sampling_interval = 60 # seconds
source = {'lat':16.71111, 'lon':-62.17722}
ext='pickle'
Q=None
for i, s in enumerate(startt):
    s = startt[i]
    e = endt[i]
    dbout = os.path.join(paths['DB_DIR'],f"dbMontserrat{s[0]}")
    pipelines.big_sausage(seisandbdir, paths, obspy.core.UTCDateTime(s[0], s[1], s[2]), obspy.core.UTCDateTime(e[0], e[1], e[2]), sampling_interval=sampling_interval, source=source, invfile=invfile, Q=Q, ext=ext, dbout=dbout, net=net)

