#!/usr/bin/env python
import os
import datetime, pytz
import glob
inputdirroot =  '/data/RedoubtCSS3.0/2009'
outputdir = 'data/continuous/SDS'
dbout = f"db/dbRedoubt"
if not os.path.isdir('db'):
    os.makedirs('db')

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
