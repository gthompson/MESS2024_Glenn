#!/usr/bin/env python
# coding: utf-8

# not for running at MESS2024
# This Jupyter notebook is intended to be run on hal9000 at USF seismic lab.
# It gathers continuous waveform data for Montserrat 2001 that is stored in a Seisan database.
# It uses Antelope tools to create an SDS archive that will be made available at MESS2024.
# It then wraps that in an Antelope/CSS3.0 database.
import os
import sys
import datetime 
import pytz
import glob
import obspy
sys.path.append('..')
import setup_paths
paths = setup_paths.paths
sys.path.append('../../src/lib')
import SDS
from SAM import RSAM, VSAM, VSEM, DSAM, DR, DRS, EMAG

def sds2db(SDS_DIR, jday):
    allfiles = glob.glob(os.path.join(SDS_DIR, '*', '*', '*', '*.D', f'*{jday}'))
    allfilesstr = " ".join(allfiles)
    os.system(f"miniseed2db {allfilesstr} {dboutday}")

def seisandb2SDS(seisandbdir, sdsdir, start_dt_utc, end_dt_utc, dbout):
    sdsobj = SDS.SDSobj(sdsdir)
    delta = datetime.timedelta(days=1)
    mseeddir = 'seisan2mseed'
    if not os.path.isdir(mseeddir):
        os.makedirs(mseeddir)

    os.system(f"rm -rf {sdsdir}/* {dbout}.*")
    if not os.path.isdir(sdsdir):
        os.makedirs(sdsdir)
    laststarttime=0

    while (start_dt_utc <= end_dt_utc):
        print(start_dt_utc, end="\n")
        ymd = start_dt_utc.strftime("%Y%m%d")
        chuckfile = f"chuckmseedblocks{ymd}.msd"
        startepoch = int(start_dt_utc.timestamp())
        endepoch = startepoch + 86400
        jday = start_dt_utc.strftime("%j")
        
        yyyy = start_dt_utc.strftime("%Y")
        mm = start_dt_utc.strftime("%m")
        dd = start_dt_utc.strftime("%d")
        currentseisandbdir = f"{seisandbdir}/{yyyy}/{mm}"
        dboutday = f"{dbout}{ymd}"

        pstart_dt_utc = start_dt_utc - delta
        pyyyy = pstart_dt_utc.strftime("%Y")
        pmm = pstart_dt_utc.strftime("%m")
        pdd = pstart_dt_utc.strftime("%d")
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
                tr.stats.sampling_rate = 75.0
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
        sds2db(sdsdir, jday)
        start_dt_utc += delta

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



def SDS2SAM_sausage(paths, startTime, endTime, sampling_interval=60):

    # read SDS, write RSAM data
    mySDSreadClient = sdsclient(paths['SDS_DIR'])
    secondsPerDay = 60 * 60 * 24
    numDays = (endTime-startTime)/secondsPerDay
    daytime = startTime
    while daytime < endTime:

        print(f'Loading Stream data for {daytime}')
        stMV = mySDSreadClient.get_waveforms("MV", "*", "*", "[SBEHCD]*", daytime, daytime+secondsPerDay)
        print(f'- got {len(stMV)} Trace ids') 

        print(f'Computing RSAM metrics for {daytime}, and saving to pickle files')
        rsamMV24h = RSAM(stream=stMV, sampling_interval=sampling_interval)
        rsamMV24h.write(paths['SAM_DIR'], ext='pickle')
        
        daytime += secondsPerDay


    SDSvelWriteClient = SDS.SDSobj(paths['SDS_VEL'], sds_type='D', format='MSEED')
    SDSdispWriteClient = SDS.SDSobj(paths['SDS_DISP'], sds_type='D', format='MSEED')

    pre_filt = (0.01, 0.02, 18.0, 36.0)
    inv = read_inventory(os.path.join(paths['RESPONSE_DIR'],'MV.xml'), format='stationxml')   
    inv_ids = InventoryTools.inventory2traceid(inv, force_location_code='')

    smalltime = 0.01
    daytime = startTime
    taperSecs = 1800
    while daytime < endTime:
        
        print(f'Loading Stream data for {daytime}')
        stMV = mySDSreadClient.get_waveforms("MV", "*", "*", "[SBEHCD]*", daytime-taperSecs, daytime+secondsPerDay+taperSecs)
        stMV.merge(method=0, fill_value=0)
        print(f'- got {len(stMV)} Trace ids') 

        print(f'Computing RSAM metrics for {daytime}, and saving to pickle files')
        rsamMV24h = RSAM(stream=stMV, sampling_interval=SAMPLING_INTERVAL)
        rsamMV24h.write(paths['SAM_DIR'], ext='pickle')

        vel_st = obspy.core.Stream()
        disp_st = obspy.core.Stream()

        for tr in stMV:

            if tr.id in inv_ids:

                this_tr = tr.copy()
                this_tr.remove_response(inventory=inv, pre_filt=pre_filt, output="VEL")
                this_st = obspy.core.Stream(traces=this_tr)
                this_st.trim(starttime=daytime, endtime=daytime+secondsPerDay-smalltime)
                SDSvelWriteClient.stream = this_st
                SDSvelWriteClient.write(overwrite=False, merge=False)
                this_tr.stats['units'] = 'm/s'
                vel_st.append(this_tr)

                this_tr = tr.copy()
                this_tr.remove_response(inventory=inv, pre_filt=pre_filt, output="DISP")
                this_st = obspy.core.Stream(traces=this_tr)
                this_st.trim(starttime=daytime, endtime=daytime+secondsPerDay-smalltime)
                SDSdispWriteClient .stream = this_st
                SDSdispWriteClient.write(overwrite=False, merge=False)
                this_tr.stats['units'] = 'm'
                disp_st.append(this_st)

            else:
                print(f"{tr.id} not found in MV.xml")

            print(' ')

        # VSAM
        vsamMV24h = VSAM(stream=vel_st, sampling_interval=sampling_interval)
        vsamMV24h.write(SAM_DIR, ext='pickle')
        
        # VSEM
        vsemMV24h = VSEM(stream=vel_st, sampling_interval=sampling_interval)
        vsemMV24h.write(SAM_DIR, ext='pickle')

        # DSAM
        dsamMV24h = DSAM(stream=disp_st, sampling_interval=sampling_interval)
        dsamMV24h.write(SAM_DIR, ext='pickle')
            
        # DR
        source = {'lat':16.71111, 'lon':-62.17722}
        DRmv = dsamMV.reduce(inv, source, surfaceWaves=False, Q=None)
        DRmv.write(SAM_DIR=SAM_DIR, overwrite=True)

        # DRS
        DRSmv = dsamMV.reduce(invMVO, source, surfaceWaves=True, Q=None)
        DRSmv.write(SAM_DIR=SAM_DIR, overwrite=True)

        # EMAG
        emagMV24h = vsemMV24.compute_emag()
        emagMV24h.write(SAM_DIR=SAM_DIR, overwrite=True)

        daytime += secondsPerDay



    del mySDSreadClient
    del SDSvelWriteClient 
    del SDSdispWriteClient 



def main(seisandbdir, paths, startt, endt):
    dbout = os.path.join(paths['DB_DIR'],f"dbMontserrat{startt.year}")
    seisan2SDS(seisandbdir, paths['SDS_DIR'], startt, endt, dbout)
    SDS2SAM_sausage(paths, startt, endt, sampling_interval=10)

if __name__ == "__main__":
    seisandbdir =  '/data/SEISAN_DB/WAV/DSNC_'
    sdsdir = paths['SDS_DIR']
    #utc = pytz.timezone('UTC')
    #startt = utc.localize(datetime.datetime(2001, 2, 25, 0, 0, 0))
    #endt = utc.localize(datetime.datetime(2001, 3, 5, 0, 0, 0))
    #startt = obspy.core.UTCDateTime(2001, 2, 25, 0, 0, 0)
    #endt = obspy.core.UTCDateTime(2001, 2, 25, 0, 0, 0)
    startt = obspy.core.UTCDateTime(2001, 7, 28, 0, 0, 0)
    endt = obspy.core.UTCDateTime(2001, 7, 31, 0, 0, 0)   
    main(seisandbdir, paths, startt, endt)