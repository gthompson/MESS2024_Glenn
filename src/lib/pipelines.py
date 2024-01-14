#!/usr/bin/env python
# coding: utf-8

# not for running at MESS2024
# This Jupyter notebook is intended to be run on hal9000 at USF seismic lab.
# It gathers continuous waveform data for Montserrat 2001 that is stored in a Seisan database.
# It uses Antelope tools to create an SDS archive that will be made available at MESS2024.
# It then wraps that in an Antelope/CSS3.0 database.
import os
import sys
#import datetime 
#import pytz
import glob
import numpy as np
import obspy
from obspy.clients.filesystem.sds import Client as sdsclient
from obspy.core.inventory.inventory import read_inventory
import SDS
import InventoryTools
from SAM import RSAM, VSAM, VSEM, DSAM #, VR, VRS, ER, ERS, DR, DRS
secondsPerDay = 60 * 60 * 24

def sds2db(dboutday, SDS_DIR, jday):
    allfiles = glob.glob(os.path.join(SDS_DIR, '*', '*', '*', '*.D', f'*{jday}'))
    allfilesstr = " ".join(allfiles)
    os.system(f"miniseed2db {allfilesstr} {dboutday}")

def seisandb2SDS(seisandbdir, sdsdir, startt, endt, dbout, round_sampling_rate=True):
    sdsobj = SDS.SDSobj(sdsdir)
    mseeddir = 'seisan2mseed'
    if not os.path.isdir(mseeddir):
        os.makedirs(mseeddir)

    #os.system(f"rm -rf {sdsdir}/* {dbout}.*")
    if not os.path.isdir(sdsdir):
        os.makedirs(sdsdir)
    laststarttime=0
    dayt = startt

    while (dayt <= endt):
        print(dayt, end="\n")
        ymd = dayt.strftime("%Y%m%d")
        chuckfile = f"chuckmseedblocks{ymd}.msd"
        #dayepoch = int(start_dt_utc.timestamp())
        dayepoch = int(startt.timestamp)
        endepoch = dayepoch + secondsPerDay
        jday = dayt.strftime("%j")
        
        yyyy = dayt.strftime("%Y")
        mm = dayt.strftime("%m")
        dd = dayt.strftime("%d")
        currentseisandbdir = f"{seisandbdir}/{yyyy}/{mm}"
       
        pdayt = dayt - 86400
        pyyyy = pdayt.strftime("%Y")
        pmm = pdayt.strftime("%m")
        pdd = pdayt.strftime("%d")
        lastseisandbdir = f"{seisandbdir}/{pyyyy}/{pmm}"
    
        allfiles0 = glob.glob(os.path.join(lastseisandbdir, f'{pyyyy}-{pmm}-{pdd}-23[45]*S.MVO___*'))
        allfiles1 = glob.glob(os.path.join(currentseisandbdir, f'{yyyy}-{mm}-{dd}*S.MVO___*'))
        allfiles = sorted(allfiles0 + allfiles1)
        
        print('- Found %d files' % len(allfiles))
        for file in allfiles:
            print(f'- Processing {file}')
            try:
                st = obspy.core.read(file, format='seisan')
            except:
                continue
            thisstarttime = st[0].stats.starttime
            if thisstarttime - laststarttime == 1201.0: # should be 20 * 60 s = 1200 s
                thisstarttime -= 1.0
            elif thisstarttime - laststarttime == 1199.0: # should be 20 * 60 s = 1200 s
                thisstarttime += 1.0
                
            for tr in st:
                tr.stats.starttime = thisstarttime
                tr.stats.sampling_rate = np.round(tr.stats.sampling_rate,0)
                if len(tr.stats.channel)==2 and len(tr.stats.location)==1:
                   tr.stats.channel = tr.stats.channel + tr.stats.location 
                   tr.stats.location =""
                if tr.stats.channel[0:2]=='SB':
                    tr.stats.channel = 'BH' + tr.stats.channel[2:]
                if tr.stats.channel[0:2]=='S ':
                    tr.stats.channel = 'SH' + tr.stats.channel[2:]    
                if tr.stats.channel == 'PRS':
                    tr.stats.channel = 'BDO' # microbarometer, possible an absolute, very-long-period instrument
                tr.stats.location = ""
                if tr.stats.network == "":
                    tr.stats.network = 'MV'
                correct_seed_id(tr)
            laststarttime = thisstarttime
            print(st)
            
            sdsobj.stream = st
            sdsobj.write()
        if dbout:
            dboutday = f"{dbout}{ymd}"
            sds2db(dboutday, sdsdir, jday)
        dayt += secondsPerDay

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

def compute_raw_metrics(paths, startTime, endTime, sampling_interval=60, do_RSAM=True, net=None):
    # read SDS, write RSAM data
    #rawSDSclient = sdsclient(paths['SDS_DIR'])
    rawSDSclient = SDS.SDSobj(paths['SDS_DIR'], sds_type='D', format='MSEED')
    numDays = (endTime-startTime)/secondsPerDay
    daytime = startTime
    if do_RSAM:
        while daytime < endTime:
            print(f'Loading Stream data for {daytime}')
            rawSDSclient.read(daytime, daytime+secondsPerDay)
            st = rawSDSclient.stream
            #st = rawSDSclient.get_waveforms("MV", "*", "*", "[SBEHCD]*", daytime, daytime+secondsPerDay)
            print(f'- got {len(st)} Trace ids') 
            print(f'Computing RSAM metrics for {daytime}, and saving to pickle files')
            if net:
            	st = st.select(network=net)            	
            if isinstance(sampling_interval, list):
            	for delta in sampling_interval:
            	    rsam24h = RSAM(stream=st, sampling_interval=delta)
            	    rsam24h.write(paths['SAM_DIR'], ext='pickle')   
            else:
            	rsam24h = RSAM(stream=st, sampling_interval=sampling_interval)
            	rsam24h.write(paths['SAM_DIR'], ext='pickle')                	
            daytime += secondsPerDay
    del rawSDSclient

def compute_SDS_VEL(paths, startTime, endTime, invfile=None):
    print(f"compute_SDS_VEL: invfile = {invfile}")
    compute_SDS_corrected(paths, startTime, endTime, invfile=invfile, kind='VEL')
    
def compute_SDS_DISP(paths, startTime, endTime, invfile=None):
    compute_SDS_corrected(paths, startTime, endTime, invfile=invfile, kind='DISP')
    
def compute_SDS_corrected(paths, startTime, endTime, invfile=None, kind='VEL'):
    print(f"compute_SDS_corrected: invfile = {invfile}")
    if kind!='VEL' and kind!='DISP':
        print('must specify whether to correct to VEL or DISP')
        return
    #rawSDSclient = sdsclient(paths['SDS_DIR'])
    rawSDSclient = SDS.SDSobj(paths['SDS_DIR'], sds_type='D', format='MSEED')
    outSDSclient = SDS.SDSobj(paths['SDS_%s_DIR' % kind], sds_type='D', format='MSEED')
    pre_filt = (0.01, 0.02, 18.0, 36.0)
    inv = read_inventory(invfile, format='stationxml')  
    #print(inv) 
    inv_ids = InventoryTools.inventory2traceid(inv, force_location_code='')
    #print(f"inv_ids = {inv_ids}")
    smalltime = 0.01
    daytime = startTime
    taperSecs = 1800
    while daytime < endTime:     
        print(f'Loading Stream data for {daytime}')
        #st = mySDSreadClient.get_waveforms("MV", "*", "*", "[SBEHCD]*", daytime-taperSecs, daytime+secondsPerDay+taperSecs)
        rawSDSclient.read(daytime, daytime+secondsPerDay)
        st = rawSDSclient.stream
        st.merge(method=0, fill_value=0)
        print(st)    
        #vel_st = obspy.core.Stream()
        print(f"seed IDs in {invfile} are {inv_ids}")
        for tr in st:
            print('Processing ',tr)
            non_loc_id = '.'.join((tr.stats.network, tr.stats.station, '', tr.stats.channel))
            if tr.id in inv_ids or non_loc_id in inv_ids:
                print(tr.id,' is valid')
                try: 
                    this_tr = tr.copy()
                    this_tr.remove_response(inventory=inv, pre_filt=pre_filt, output=kind)
                    this_st = obspy.core.Stream(traces=this_tr)
                    this_st.trim(starttime=daytime, endtime=daytime+secondsPerDay-smalltime)
                    outSDSclient.stream = this_st
                    print('Saving to SDS: ', outSDSclient.stream)
                    outSDSclient.write(overwrite=False, merge=False)
                    outSDSclient.stream = obspy.core.Stream() # wipe it for next time, just in case
                except Exception as e:
                    print(e)
        daytime += secondsPerDay 

               
def compute_velocity_metrics(paths, startt, endt, sampling_interval=60, do_VSAM=True, do_VSEM=True, net=None):       
    # read SDS_VEL, write VSAM, VSEM data
    #velSDSclient = sdsclient(paths['SDS_DIR'])
    velSDSclient = SDS.SDSobj(paths['SDS_VEL_DIR'], sds_type='D', format='MSEED')
    numDays = (endt-startt)/secondsPerDay
    daytime = startt
    if do_VSAM or do_VSEM:
        while daytime < endt:
            print(f'Loading Stream data for {daytime}')
            velSDSclient.read(daytime, daytime+secondsPerDay)
            st = velSDSclient.stream
            for tr in st:
                if tr.stats.channel[1]=='H':
                    tr.stats['units'] = 'm/s'
            if net:
            	st = st.select(network=net)
            if len(st)>0:
                if do_VSAM:
            	    print(f'Computing VSAM metrics for {daytime}, and saving to pickle files')
            	    if isinstance(sampling_interval, list):
            	        for delta in sampling_interval:
            	            vsam24h = VSAM(stream=st, sampling_interval=delta)
            	            vsam24h.write(paths['SAM_DIR'], ext='pickle')   
            	    else:
            	        vsam24h = VSAM(stream=st, sampling_interval=sampling_interval)
            	        vsam24h.write(paths['SAM_DIR'], ext='pickle')       
                if do_VSEM:
            	    print(f'Computing VSEM metrics for {daytime}, and saving to pickle files') 
            	    if isinstance(sampling_interval, list):
            	        for delta in sampling_interval:
            	            vsem24h = VSEM(stream=st, sampling_interval=delta)
            	            vsem24h.write(paths['SAM_DIR'], ext='pickle')   
            	    else:
            	        vsem24h = VSAM(stream=st, sampling_interval=sampling_interval)
            	        vsem24h.write(paths['SAM_DIR'], ext='pickle')                	              	
            daytime += secondsPerDay
    del velSDSclient
    
def compute_displacement_metrics(paths, startt, endt, sampling_interval=60, do_DSAM=True, net=None):       
    # read SDS_DISP, write DSAM
    #dispSDSclient = sdsclient(paths['SDS_DIR'])
    dispSDSclient = SDS.SDSobj(paths['SDS_DISP_DIR'], sds_type='D', format='MSEED')
    numDays = (endt-startt)/secondsPerDay
    daytime = startt
    if do_DSAM:
        while daytime < endt:
            print(f'Loading Stream data for {daytime}')
            dispSDSclient.read(daytime, daytime+secondsPerDay)
            st = dispSDSclient.stream
            for tr in st:
                if tr.stats.channel[1]=='H':
                    tr.stats['units'] = 'm'
            if net:
            	st = st.select(network=net)
            if len(st)>0 and do_DSAM:            
            	print(f'Computing DSAM metrics for {daytime}, and saving to pickle files')
            	if isinstance(sampling_interval, list):
            	    for delta in sampling_interval:
            	        dsam24h = DSAM(stream=st, sampling_interval=delta)
            	        dsam24h.write(paths['SAM_DIR'], ext='pickle')   
            	else:
            	    dsam24h = DSAM(stream=st, sampling_interval=sampling_interval)
            	    dsam24h.write(paths['SAM_DIR'], ext='pickle')               	            	
            daytime += secondsPerDay
    del dispSDSclient    


def reduce_to_1km(paths, year, do_VR=False, do_VRS=False, do_ER=True, do_ERS=True, do_DR=True, do_DRS=True, sampling_interval=60, invfile=None, source=None, Q=None, ext='pickle'):
    startTime = obspy.core.UTCDateTime(year,1,1)
    endTime = obspy.core.UTCDateTime(year,12,31,23,59,59.9)

    if do_VR or do_VRS:
        vsamObj = VSAM.read(startTime, endTime, SAM_DIR=paths['SAM_DIR'], sampling_interval=sampling_interval, ext=ext)
        if do_VR:
            VRobj = vsamObj.reduce(invMVO, source, surfaceWaves=False, Q=Q)
            VRobj.write(SAM_DIR=paths['SAM_DIR'], overwrite=True)
        if do_VRS:
            VRSobj = vsamObj.reduce(invMVO, source, surfaceWaves=True, Q=Q)
            VRSobj.write(SAM_DIR=paths['SAM_DIR'], overwrite=True)        

    if do_ER or do_ERS:
        vsemObj = VSEM.read(startTime, endTime, SAM_DIR=paths['SAM_DIR'], sampling_interval=sampling_interval, ext=ext)
        if do_ER:
            ERobj = vsemObj.reduce(invMVO, source, surfaceWaves=False, Q=Q)
            ERobj.write(SAM_DIR=paths['SAM_DIR'], overwrite=True)
        if do_ER:
            ERSobj = vsemObj.reduce(invMVO, source, surfaceWaves=True, Q=Q)
            ERSobj.write(SAM_DIR=paths['SAM_DIR'], overwrite=True)
            
    if do_DR or do_DRS:
        dsamObj = DSAM.read(startTime, endTime, SAM_DIR=paths['SAM_DIR'], sampling_interval=sampling_interval, ext=ext)
        if do_DR:
            DRobj = dsamObj.reduce(invMVO, source, surfaceWaves=False, Q=Q)
            DRobj.write(SAM_DIR=paths['SAM_DIR'], overwrite=True)
        if do_DRS:
            DRSobj = dsamObj.reduce(invMVO, source, surfaceWaves=True, Q=Q)
            DRSobj.write(SAM_DIR=paths['SAM_DIR'], overwrite=True)        

# need to ensure there is a reduce method for VSAM, VSEM, DSAM. Should be different for VSEM - use Boatwright formulas.
# Can eliminate EMAG class.
# when loading SDS_VEL or SDS_DISP should probably fix units for "?H?" to m/s or m respectively, or "Pa" for "?D?"


def small_sausage(paths, startt, endt, sampling_interval=60, source=None, invfile=None, Q=None, ext='pickle', net=None):
    compute_raw_metrics(paths, startt, endt, sampling_interval=sampling_interval, do_RSAM=True, net=net)
    print(f"invfile={invfile}")
    if invfile and os.path.isfile(invfile):
        print('Calling compute_SDS_VEL')
        compute_SDS_VEL(paths, startt, endt, invfile=invfile)
        print('Calling compute_SDS_DISP')
        compute_SDS_DISP(paths, startt, endt, invfile=invfile)
        print('Calling compute_velocity_metrics')
        compute_velocity_metrics(paths, startt, endt, sampling_interval=sampling_interval, do_VSAM=True, do_VSEM=True, net=net) 
        print('Calling compute_displacement_metrics')    
        compute_displacement_metrics(paths, startt, endt, sampling_interval=sampling_interval, do_DSAM=True, net=net) 
        if source:   
            pass
            if isinstance(sampling_interval, list):
            	for delta in sampling_interval:
                    reduce_to_1km(paths, year, do_VR=False, do_VRS=False, do_ER=True, do_ERS=True, do_DR=True, do_DRS=True, sampling_interval=delta, invfile=invfile, source=source, Q=Q, ext=ext)
            else:
                reduce_to_1km(paths, year, do_VR=False, do_VRS=False, do_ER=True, do_ERS=True, do_DR=True, do_DRS=True, sampling_interval=sampling_interval, invfile=invfile, source=source, Q=Q, ext=ext)


def big_sausage(seisandbdir, paths, startt, endt, sampling_interval=60, source=None, invfile=None, Q=None, ext='pickle', dbout=None, round_sampling_rate=True, net=None):
    # includes everything in small sausage, but with a Seisan to SDS conversion first
    seisandb2SDS(seisandbdir, paths['SDS_DIR'], startt, endt, dbout, round_sampling_rate=round_sampling_rate)
     
    # small sauage stuff
    small_sausage(paths, startt, endt, sampling_interval=sampling_interval, source=source, invfile=invfile, Q=Q, ext=ext, net=net)
   
if __name__ == "__main__":
    import setup_paths
    paths = setup_paths.paths
    #sys.path.append('../../src/lib')
    seisandbdir =  '/data/SEISAN_DB/WAV/DSNC_'
    net = 'MV'
    invfile = os.path.join(paths['RESPONSE_DIR'],f"{net}.xml")
    startt = obspy.core.UTCDateTime(2001, 7, 28, 0, 0, 0)
    endt = obspy.core.UTCDateTime(2001, 7, 31, 0, 0, 0)
    sampling_interval= 10 # seconds # can also be a list of different sampling rates, e.g. [2.56, 60, 600] to mimic original RSAM system. 
    # For VT band (4-18 Hz), 2.56s is fine (10 cycles+)
    # For LP band (0.5 - 4 Hz), 2.56s might work (1.25 cycles+), but 10s might be better (5 cycles+), and 60s would be amazing (30 cycles+)
    # For VLP band (0.02 - ?), 60-s might work (1.2 cycles+), but 600s would be better (12 cycles+)
    # So best compromise might be [2.56, 10, 60, 600] then we have everything we need for RSAM bar graph simulator, detecting VTs (2.56s), LPs (2.56s or 10s), and VLPs (60s or 600s), and 10s for ASL.
    source = {'lat':16.71111, 'lon':-62.17722}
    dbout = os.path.join(paths['DB_DIR'],f"dbMontserrat{startt.year}")
    Q = None
    ext = 'pickle'

    big_sausage(seisandbdir, paths, startt, endt, sampling_interval=sampling_interval, source=source, invfile=invfile, Q=Q, ext=ext, dbout=dbout, round_sampling_rate=True, net=net)
    # looks like MBLY supposed to be 100 Hz, so by forcing it to 75 Hz, I am messing it up. So replacing 75.0 with np.round(tr.stats.sampling_rate, 0) should fix this.
