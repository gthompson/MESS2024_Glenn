#!/usr/bin/env python


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
        print(dayt, end="\n")
        ymd = dayt.strftime("%Y%m%d")
        YYYY = dayt.strftime("%Y")
        MMDD = dayt.strftime('%m%d')
        dboutymd = f"{dbout}{ymd}"
        dayepoch = int(dayt.timestamp)
        dayendepoch = dayepoch + secondsPerDay
        jday = dayt.strftime("%j")
        inputdir = os.path.join(inputdirroot, YYYY, jday)
        #print("inputdir = ",inputdir)
        allfilespattern = os.path.join(inputdir,f"*{YYYY}*")
        print(allfilespattern)
        allfiles = sorted(glob.glob(allfilespattern))
        if len(allfiles)>0:
            allfilesstr = " ".join(allfiles)
            #os.system(f"miniseed2days -U -w '%Y/%{{net}}/%{{sta}}/%{{chan}}.D/%{{net}}.%{{sta}}.%{{loc}}.%{{chan}}.D.%Y.%j' -S {outputdir} -C {chuckfile} -s {dayepoch} -e {dayendepoch} -d {dbout} {lastallfilesstr} {allfilesstr}")
            if dbout:
                os.system(f"miniseed2days -U -w '%Y/%{{net}}/%{{sta}}/%{{chan}}.D/%{{net}}.%{{sta}}.%{{loc}}.%{{chan}}.D.%Y.%j' -S {outputdir} -s {dayepoch} -e {dayendepoch} -d {dboutymd} {allfilesstr}")
            else:    
                os.system(f"miniseed2days -U -w '%Y/%{{net}}/%{{sta}}/%{{chan}}.D/%{{net}}.%{{sta}}.%{{loc}}.%{{chan}}.D.%Y.%j' -S {outputdir} -s {dayepoch} -e {dayendepoch} {allfilesstr}")
                
        else:
            print('- no matching files')
        #lastallfilesstr = allfilesstr
        dayt += secondsPerDay

# create inventory XML
'''
net = 'AV'
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
'''
net = 'AV' # though some might be 'AK' or even 'AT'
# Make raw SDS from Antelope archive
inputdirroot =  '/shares/newton/raid/data/ANTELOPE/Alaska_all_waveforms_together'
outputdir = paths['SDS_DIR']
outputdir = '/data/SDS'
startt = obspy.core.UTCDateTime(1999,7,14)
endt = obspy.core.UTCDateTime(2015,11,1)
ext = 'pickle'
sampling_interval = 60 # seconds
invfile=None
#do_metric = pipelines.check_what_to_do(paths, net, startt, endt, sampling_interval=sampling_interval, ext=ext, invfile=invfile)
#print(do_metric)
dbout=None
#if do_metric['SDS_RAW']:
#    antelope2sds(startt, endt, inputdirroot, outputdir, net, dbout=dbout)
antelope2sds(startt, endt, inputdirroot, outputdir, dbout=dbout)

# derive datasets from SDS
Q=None
#pipelines.small_sausage(paths, startt, endt, sampling_interval=sampling_interval, source=source, invfile=invfile, Q=Q, ext=ext, net=net, do_metric=do_metric)

