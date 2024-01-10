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
from SAM import DSAM
import InventoryTools
import SDS

CONTINUOUS_DATA_DIR = os.path.join(PROJECT_DIR, 'data', 'continuous')
SDS_DIR = os.path.join(CONTINUOUS_DATA_DIR, 'SDS')
SDS_DIR2 = os.path.join(CONTINUOUS_DATA_DIR, 'SDS_displacement')
SAM_DIR = os.path.join(CONTINUOUS_DATA_DIR, 'SAM')

#####################################################################################

startTime = obspy.core.UTCDateTime(2001,2,25,0,0,0)
endTime = obspy.core.UTCDateTime(2001,3,6,0,0,0)
secondsPerDay = 60 * 60 * 24
numDays = (endTime-startTime)/secondsPerDay


# # 2. Write SDS_Displacement archive
# - Read files from SDS_raw
# - Correct to Displacement
# - Write files to SDS_Displacement


'''
def correct_seed_id(tr):
    net, sta, loc, chan = tr.id.split('.')
    Fs = tr.stats.sampling_rate
    code0 = chan[0]
    if Fs < 80.0 and Fs > 20.0:
        if chan[0] == 'E': 
            code0 = 'S'
        elif chan[0] == 'H': 
            code0 = 'B'
    elif Fs > 80.0 and Fs < 250.0:
        if chan[0] == 'B': 
            code0 = 'H'
        elif chan[0] == 'S': 
            code0 = 'E'
    chan = code0 + chan[1:] 

mySDSreadClient = sdsclient(SDS_DIR)
mySDSwriteClient = SDS.SDSobj(SDS_DIR2, sds_type='D', format='MSEED')

pre_filt = (0.01, 0.02, 18.0, 36.0)
invMVO = read_inventory('../../data/response/MV.xml', format='stationxml')   
inv_ids = InventoryTools.inventory2traceid(invMVO, force_location_code='')

smalltime = 0.01
daytime = startTime
taperSecs = 1800
while daytime < endTime:
    
    print(f'Loading Stream data for {daytime}')
    stMV = mySDSreadClient.get_waveforms("MV", "*", "*", "[SBEHCD]*", daytime-taperSecs, daytime+secondsPerDay+taperSecs)
    stMV.merge(method=0, fill_value=0)
    print(f'- got {len(stMV)} Trace ids') 
    for tr in stMV:

        correct_seed_id(tr)
        
        if tr.id in inv_ids:
            time1 = time.time()
            tr.remove_response(inventory=invMVO, pre_filt=pre_filt, output="DISP")
            this_st = obspy.core.Stream(traces=tr)
            this_st.trim(starttime=daytime, endtime=daytime+secondsPerDay-smalltime)
            mySDSwriteClient.stream = this_st
            mySDSwriteClient.write(overwrite=False, merge=False)
            time2 = time.time()
            print(this_st,' took ',time2-time1,' s')
        else:
            print(f"{tr.id} not found in MV.xml")

        print(' ')

    daytime += secondsPerDay
del mySDSreadClient
del mySDSwriteClient
'''

# # 3. Write DSAM archive
# - read data from SDS_Displacement
# - compute DSAM data
# - write to DSAM files



mySDSreadClient = sdsclient(SDS_DIR2)
daytime = startTime
while daytime < endTime:
    time1 = time.time()
    print(f'Loading Stream data for {daytime}')
    stMV = mySDSreadClient.get_waveforms("MV", "*", "*", "[SBEHCD]*", daytime, daytime+secondsPerDay)
    print(f'- got {len(stMV)} Trace ids') 
    print(f'Computing DSAM metrics for {daytime}, and saving to pickle files')
    for tr in stMV:
        tr.stats['units'] = 'm'
    dsamMV24h = DSAM(stream=stMV, sampling_interval=60)
    dsamMV24h.write(SAM_DIR, ext='pickle')
    
    daytime += secondsPerDay

    time2=time.time()
    print(f"- day took {time2-time1} seconds")

del mySDSreadClient






