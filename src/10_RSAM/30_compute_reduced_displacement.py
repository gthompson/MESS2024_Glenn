#!/usr/bin/env python
# coding: utf-8

# # Reduced Displacement calculation tutorial
# 
# # 1. Header


import os
import sys
import time
import obspy
from obspy.clients.filesystem.sds import Client as sdsclient
from obspy.core.inventory.inventory import read_inventory

PROJECT_DIR = os.path.join('..','..')
LIB_DIR = os.path.join(PROJECT_DIR,'src','lib')
sys.path.append(LIB_DIR)
from SAM import DSAM, DRS
import InventoryTools

CONTINUOUS_DATA_DIR = os.path.join(PROJECT_DIR, 'data', 'continuous')
SAM_DIR = os.path.join(CONTINUOUS_DATA_DIR, 'SAM')

#####################################################################################

startTime = obspy.core.UTCDateTime(2001,2,25,0,0,0)
endTime = obspy.core.UTCDateTime(2001,3,6,0,0,0)
secondsPerDay = 60 * 60 * 24
numDays = (endTime-startTime)/secondsPerDay


# # 2. Read DSAM archive and plot

dsamMV = DSAM.read(startTime, endTime, SAM_DIR=SAM_DIR, sampling_interval=60, ext='pickle')
'''
#dsamMV.plot(metrics='median', kind='stream', outfile='plots/DSAM_median.png')
for metric in ['mean', 'min', 'max', 'std', 'VLP', 'LP', 'VT', 'fratio']:
    dsamMV.plot(metrics=metric, kind='stream', outfile=f'plots/DSAM.png') # metric added by plot
'''

# # 3. Compute DRS

invMVO = read_inventory('../../data/response/MV.xml')
source = {'lat':16.71111, 'lon':-62.17722}

DRmv = dsamMV.reduce(invMVO, source, surfaceWaves=False, Q=None)
DRmv.write(SAM_DIR=SAM_DIR, overwrite=True)
DRmvHourly = DRmv.downsample(new_sampling_interval=3600)
DRmvHourly.iceweb_plot(outfile='plots/DR_Hourly.png')

DRSmv = dsamMV.reduce(invMVO, source, surfaceWaves=True, Q=None)
DRSmv.write(SAM_DIR=SAM_DIR, overwrite=True)
DRSmvHourly = DRSmv.downsample(new_sampling_interval=3600)
DRSmvHourlyZ = DRSmvHourly.select(component='Z')
DRSmvHourlyZ.iceweb_plot(outfile='plots/DRS_Hourly.png', linestyle='.')
for metric in ['median', 'mean', 'min', 'max', 'std', 'VLP', 'LP', 'VT', 'fratio']:
    DRSmvHourlyZ.iceweb_plot(metric=metric, outfile=f'plots/DRS_hourly_{metric}.png', linestyle='.')

medians, station_corrections = DRSmv.examine_spread()
