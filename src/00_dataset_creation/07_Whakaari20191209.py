import os
import sys
import glob
import obspy
sys.path.append('../../src/lib')
import setup_paths
paths = setup_paths.paths
import SDS
import pipelines

from obspy.clients.fdsn.client import Client
client = Client('GEONET')
net = 'NZ'
invfile = os.path.join(paths['RESPONSE_DIR'],f"{net}.xml")
lat = - (37 + 31/60 + 17/3600)
lon = (177 + 11/60 + 6/3600)
source = {'lat':lat, 'lon':lon}
print(source)

if not os.path.isfile(invfile):

    sdate = obspy.core.UTCDateTime(2010,1,1)
    edate = obspy.core.UTCDateTime(2020,1,1)
    maxRadius = 0.5
    inv = client.get_stations( \
        starttime=sdate, endtime=edate, \
        latitude="%.4f" % source['lat'], longitude="%.4f" % source['lon'], maxradius="%.1f" % maxRadius, \
        level="response")
    inv.write(invfile, format = 'stationxml')

startt = [
#    (2019,12, 8),
    (2019,11,1),
    (2019,10,1),
    (2019,6,1),
    ]
endt = [
#    (2019,12,10),
    (2019,12,8),
    (2019,11,1),
    (2019,10,1),
    ]
sampling_interval = 60 # seconds
Q=None
ext='pickle'
secondsPerDay = 60 * 60 * 24
for i, s in enumerate(startt):
    s = startt[i]
    e = endt[i]
    print(s,e)
    stime = obspy.core.UTCDateTime(s[0], s[1], s[2]) 
    etime = obspy.core.UTCDateTime(e[0], e[1], e[2])
    print(f'Processing {stime} to {etime}')
    dbout = os.path.join(paths['DB_DIR'],f"dbWhakaari{s[0]}")
    remote_SDS_DIR = '/shares/newton/raid/data/SDS'
    if os.path.isdir(remote_SDS_DIR):
        paths['SDS_DIR'] = remote_SDS_DIR
    else:
        # need to create SDS RAW
        dayt = stime
        while dayt < etime:
            # check if files for this julian day already exist
            jday = dayt.strftime('%j')
            yyyy = dayt.strftime('%Y')
            existingfiles = glob.glob(os.path.join(paths['SDS_DIR'], yyyy, net, '*', '*.D', f"{net}*.{yyyy}.{jday}"))
            if len(existingfiles) > 0:
                print(f'Already have SDS data for {net} {yyyy} {jday}') 
                dayt += secondsPerDay
                continue
            print(f"Processing {dayt}:")
            #st = client.get_waveforms(net, '*', '*', '[SBEH][HD]?', dayt, dayt+secondsPerDay)
            st = client.get_waveforms(net, 'WIZ,WSRZ', '*', 'H??', dayt, dayt+secondsPerDay)
            sdsclient = SDS.SDSobj(paths['SDS_DIR'], sds_type='D', format='MSEED', streamobj=st)
            sdsclient.write()
            dayt += secondsPerDay

    #dbout = os.path.join(paths['DB_DIR'],f"dbWhakaari{stime.year}")

    pipelines.small_sausage(paths, stime, etime, sampling_interval=sampling_interval, source=source, invfile=invfile, Q=Q, ext=ext, net=net)

