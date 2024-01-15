#!/usr/bin/env python
# coding: utf-8

import os
import sys
import glob
import obspy
sys.path.append('..')
import setup_paths
paths = setup_paths.paths
sys.path.append('../../src/lib')
from SAM import RSAM, VSEM

startTime = obspy.core.UTCDateTime(2001,7,29,18,0,0)
endTime = obspy.core.UTCDateTime(2001,7,29,23,59,59)
secondsPerDay = 60 * 60 * 24
numDays = (endTime-startTime)/secondsPerDay

rsamMV = RSAM.read(startTime, endTime, SAM_DIR=paths['SAM_DIR'], sampling_interval=10)
print(rsamMV)
rsamMV_Z = rsamMV.select(component='Z')
rsamMV_Z.plot(metrics=['energy'], outfile='RSAM.MV.Z.20010729.png')

inv = read_inventory(os.path.join(paths['RESPONSE_DIR'],'MV.xml'), format='stationxml')  
source = {'lat':16.71111, 'lon':-62.17722}
rsamMV_Z.sum_energy(startTime, endTime, inv, source)

