#!/usr/bin/env python
# coding: utf-8

import os
import sys
import obspy
sys.path.append('../../src/lib')
import setup_paths
paths = setup_paths.paths
import pipelines

seisandbdir =  '/data/SEISAN_DB/WAV/DSNC_'
net = 'MV'
invfile = os.path.join(paths['RESPONSE_DIR'],f"{net}.xml")
startt = [
#    (1997, 12, 24),
    (2000, 3, 19),
    (2001, 2, 25), 
#    (2003, 7, 12),
    ]
endt = [
#    (1997, 12, 28),
    (2000, 3, 22),
    (2001, 3, 5),
#    (2003, 7, 16),
    ]
sampling_interval = 60 # seconds
source = {'lat':16.71111, 'lon':-62.17722}
ext='pickle'
Q=None
for i, s in enumerate(startt):
    s = startt[i]
    e = endt[i]
    dbout = os.path.join(paths['DB_DIR'],f"dbMontserrat{s[0]}")
    # should potentially check the SDS, SDS_VEL, and SDS_DISP archives here by julian day and determine whether need to run SDS creation routines.
    pipelines.big_sausage(seisandbdir, paths, obspy.core.UTCDateTime(s[0], s[1], s[2]), obspy.core.UTCDateTime(e[0], e[1], e[2]), sampling_interval=sampling_interval, source=source, invfile=invfile, Q=Q, ext=ext, dbout=dbout, net=net)


# old stuff
'''
# not for running at MESS2024
# This Jupyter notebook is intended to be run on hal9000 at USF seismic lab.
# It gathers continuous waveform data for Montserrat 2001 that is stored in a Seisan database.
# It uses Antelope tools to create an SDS archive that will be made available at MESS2024.
# It then wraps that in an Antelope/CSS3.0 database.
import os
import sys
import datetime, pytz
import glob
import obspy
sys.path.append('..')
import setup_paths
paths = setup_paths.paths
sys.path.append('../../src/lib')
import SDS



inputdirroot =  '/data/SEISAN_DB/WAV/DSNC_'
outputdir = paths['SDS_DIR']
dbout = os.path.join(paths['DB_DIR'],"dbMontserrat2001")
sdsobj = SDS.SDSobj(outputdir)
merge = False
def sds2db(SDS_DIR, jday):
    allfiles = glob.glob(os.path.join(SDS_DIR, '*', '*', '*', '*.D', f'*{jday}'))
    allfilesstr = " ".join(allfiles)
    os.system(f"miniseed2db {allfilesstr} {dboutday}")

utc = pytz.timezone('UTC')
start_dt_utc = utc.localize(datetime.datetime(2001, 2, 25, 0, 0, 0))
end_dt_utc = utc.localize(datetime.datetime(2001, 3, 5, 0, 0, 0))
delta = datetime.timedelta(days=1)
mseeddir = 'seisan2mseed'
if not os.path.isdir(mseeddir):
    os.makedirs(mseeddir)
if not merge:
    os.system(f"rm -rf {outputdir}/2001/MV/M*/*.D/*.0?? {dbout}.*")
if not os.path.isdir(outputdir):
    os.makedirs(outputdir)
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
    inputdir = f"{inputdirroot}/{yyyy}/{mm}"
    dboutday = f"{dbout}{ymd}"

    pstart_dt_utc = start_dt_utc - delta
    pyyyy = pstart_dt_utc.strftime("%Y")
    pmm = pstart_dt_utc.strftime("%m")
    pdd = pstart_dt_utc.strftime("%d")
    pinputdir = f"{inputdirroot}/{pyyyy}/{pmm}"
    
    allfiles0 = glob.glob(os.path.join(pinputdir, f'{pyyyy}-{pmm}-{pdd}-23[45]*S.MVO___*'))
    allfiles1 = glob.glob(os.path.join(inputdir, f'{yyyy}-{mm}-{dd}*S.MVO___*'))
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
        laststarttime = thisstarttime
        print(st)
        
        sdsobj.stream = st
        sdsobj.write()
    sds2db(outputdir, jday)
    start_dt_utc += delta
'''
