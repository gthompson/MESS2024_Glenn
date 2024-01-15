import os
import sys
import obspy
sys.path.append('../../src/lib')
import setup_paths
paths = setup_paths.paths
import SDS
import pipelines

net = 'NZ'
invfile = os.path.join(paths['RESPONSE_DIR'],f"{net}.xml")
lat = - (37 + 31/60 + 17/3600)
lon = (177 + 11/60 + 6/3600)
source = {'lat':lat, 'lon':lon}
print(source)

if not os.path.isfile(invfile):
    from obspy.clients.fdsn.client import Client
    client = Client('GEONET')
    sdate = obspy.core.UTCDateTime(2010,1,1)
    edate = obspy.core.UTCDateTime(2020,1,1)
    maxRadius = 0.5
    inv = client.get_stations( \
        starttime=sdate, endtime=edate, \
        latitude="%.4f" % source['lat'], longitude="%.4f" % source['lon'], maxradius="%.1f" % maxRadius, \
        level="response")
    inv.write(invfile, format = 'stationxml')

startt = obspy.core.UTCDateTime(2019, 12, 8, 0, 0, 0)
endt = obspy.core.UTCDateTime(2019, 12, 10, 0, 0, 0)
remote_SDS_DIR = '/shares/newton/raid/data/SDS'
if os.path.isdir(remote_SDS_DIR):
    paths['SDS_DIR'] = remote_SDS_DIR
else:
    # need to create SDS RAW
    dayt = startt
    while dayt < endt:
        st = client.get_waveforms(net, '*', '*', '[SBEH][HD]?', dayt, dayt+86400)
        sdsclient = SDS.SDS_obj(SDS_TOP, sds_type='D', format='MSEED', streamobj=st)
        sdsclient.write()
        dayt += 86400


#dbout = os.path.join(paths['DB_DIR'],f"dbWhakaari{startt.year}")
sampling_interval = 60 # seconds
Q=None
ext='pickle'
pipelines.small_sausage(paths, startt, endt, sampling_interval=sampling_interval, source=source, invfile=invfile, Q=Q, ext=ext, net=net)

