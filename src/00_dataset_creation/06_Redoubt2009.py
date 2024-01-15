#!/usr/bin/env python

# not for running at MESS2024
# This script is intended to be run on hal9000 at USF seismic lab.
# It gathers continuous waveform data for Redoubt 2009 that is stored in an Antelope/CSS3.0 database.
# It uses Antelope tools to create an SDS archive that will be made available at MESS2024.
# It then wraps that in an Antelope/CSS3.0 database. 

import os
import sys
#import datetime, pytz
import glob
import obspy
sys.path.append('../lib')
import setup_paths
paths = setup_paths.paths
import pipelines

# could add different routines here to get data from Antelope DB, Seisan DB, or FDSN server

def antelope2sds(startt, endt, inputdirroot, outputdir, dbout=None, remove_all=False):
    secondsPerDay = 86400
    if remove_all:
        os.system(f"rm -rf {outputdir}/* {dbout}.*")

    #lastallfilesstr = ''
    if not os.path.isdir(outputdir):
        os.makedirs(outputdir)

    dayt = startt
    while (dayt <= endt):
        print(startt, end="\n")
        ymd = dayt.strftime("%Y%m%d")
        dboutymd = f"{dbout}{ymd}"
        chuckfile = f"chuckmseedblocks{ymd}.msd"
        dayepoch = int(dayt.timestamp)
        dayendepoch = dayepoch + secondsPerDay
        jday = dayt.strftime("%j")
        inputdir = os.path.join(inputdirroot, '%4d' % dayt.year, jday)
        print("inputdir = ",inputdir)
        allfiles1 = sorted(glob.glob(os.path.join(inputdir,"R[DES]*")))
        allfiles2 = sorted(glob.glob(os.path.join(inputdir,"NCT*")))
        allfiles3 = sorted(glob.glob(os.path.join(inputdir,"DFR*")))
        allfiles = allfiles1 + allfiles2 + allfiles3
        if len(allfiles)>0:
            allfilesstr = " ".join(allfiles)
            #os.system(f"miniseed2days -U -w '%Y/%{{net}}/%{{sta}}/%{{chan}}.D/%{{net}}.%{{sta}}.%{{loc}}.%{{chan}}.D.%Y.%j' -S {outputdir} -C {chuckfile} -s {startepoch} -e {endepoch} -d {dbout} {lastallfilesstr} {allfilesstr}")
            if dbout:
                os.system(f"miniseed2days -U -w '%Y/%{{net}}/%{{sta}}/%{{chan}}.D/%{{net}}.%{{sta}}.%{{loc}}.%{{chan}}.D.%Y.%j' -S {outputdir} -C {chuckfile} -s {startepoch} -e {endepoch} -d {dboutymd} {allfilesstr}")
            else:    
                os.system(f"miniseed2days -U -w '%Y/%{{net}}/%{{sta}}/%{{chan}}.D/%{{net}}.%{{sta}}.%{{loc}}.%{{chan}}.D.%Y.%j' -S {outputdir} -C {chuckfile} -s {startepoch} -e {endepoch} {allfilesstr}")
            file_stats = os.stat(chuckfile)
            if file_stats.st_size == 0:
                os.remove(chuckfile)
        #lastallfilesstr = allfilesstr
        dayt += secondsPerDay




'''
utc = pytz.timezone('UTC')
start_dt_utc = utc.localize(datetime.datetime(2009, 3, 1, 0, 0, 0))
end_dt_utc = utc.localize(datetime.datetime(2009, 5, 1, 0, 0, 0))
delta = datetime.timedelta(days=1)

os.system(f"rm -rf {outputdir}/* {dbout}.*")
lastallfilesstr = ''
if not os.path.isdir(outputdir):
    os.makedirs(outputdir)
while (start_dt_utc <= end_dt_utc):
    print(start_dt_utc, end="\n")
    ymd = start_dt_utc.strftime("%Y%m%d")

    chuckfile = f"chuckmseedblocks{ymd}.msd"
    startepoch = int(start_dt_utc.timestamp())
    endepoch = startepoch + 86400
    jday = start_dt_utc.strftime("%j")
    inputdir = f"{inputdirroot}/{jday}"
    print("inputdir = ",inputdir)
    allfiles1 = sorted(glob.glob(f"{inputdir}/R[DES]*"))
    allfiles2 = sorted(glob.glob(f"{inputdir}/NCT*"))
    allfiles3 = sorted(glob.glob(f"{inputdir}/DFR*"))
    allfiles = allfiles1 + allfiles2 + allfiles3
    if len(allfiles)>0:
        allfilesstr = " ".join(allfiles)
        os.system(f"miniseed2days -U -w '%Y/%{{net}}/%{{sta}}/%{{chan}}.D/%{{net}}.%{{sta}}.%{{loc}}.%{{chan}}.D.%Y.%j' -S {outputdir} -C {chuckfile} -s {startepoch} -e {endepoch} -d {dbout} {lastallfilesstr} {allfilesstr}")
        file_stats = os.stat(chuckfile)
        if file_stats.st_size == 0:
            os.remove(chuckfile)
        lastallfilesstr = allfilesstr
    start_dt_utc += delta
'''

# create inventory XML
net = 'RD'
lat = 60 + 29/60 + 4.19/3600
lon = - (152 + 44/60 + 20.99/3600)
source = {'lat':lat, 'lon':lon}
maxRadius = 0.5
invfile = os.path.join(paths['RESPONSE_DIR'],f"{net}.xml")
if not os.path.isfile(invfile):
    sdate = obspy.core.UTCDateTime(2008,1,1)
    edate = obspy.core.UTCDateTime(2010,1,1)
    from obspy.clients.fdsn.client import Client
    client = Client("IRIS")
    inv = client.get_stations( \
        starttime=sdate, endtime=edate, \
        latitude="%.4f" % source['lat'], longitude="%.4f" % source['lon'], maxradius="%.1f" % maxRadius, \
        level="response")
    inv.write(invfile, format = 'stationxml')

# Make raw SDS from Antelope archive
inputdirroot =  '/data/RedoubtCSS3.0/2009'
outputdir = paths['SDS_DIR']
dbout = os.path.join(paths['DB_DIR'], 'dbRedoubt2009')
startt = obspy.core.UTCDateTime(2009,3,1)
endt = obspy.core.UTCDateTime(2009,4,1)
ext = 'pickle'
sampling_interval = 60 # seconds
do_metric = pipelines.check_what_to_do(paths, net, startt, endt, sampling_interval=sampling_interval, ext=ext, invfile=invfile)
if do_metric['SDS_RAW']:
    antelope2sds(startt, endt, inputdirroot, outputdir, dbout=dbout)

# derive datasets from SDS
Q=None
pipelines.small_sausage(paths, startt, endt, sampling_interval=sampling_interval, source=source, invfile=invfile, Q=Q, ext=ext, net=net, do_metric=do_metric)

