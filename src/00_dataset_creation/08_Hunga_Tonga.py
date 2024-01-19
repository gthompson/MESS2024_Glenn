import os
import sys
import glob
import obspy
sys.path.append('../../src/lib')
import setup_paths
paths = setup_paths.paths
import SDS
import pipelines
import InventoryTools

from obspy.clients.fdsn.client import Client
client = Client('IRIS')
net = 'II'
invfile = os.path.join(paths['RESPONSE_DIR'],f"{net}.xml")
source = {'lat':-20.57, 'lon':-175.38}
print(source)
stime = obspy.core.UTCDateTime(2022,1,15)
etime = obspy.core.UTCDateTime(2022,1,16)

if not os.path.isfile(invfile):
    maxRadius = 10
    inv = client.get_stations( \
        starttime=stime, endtime=etime, \
        latitude="%.4f" % source['lat'], longitude="%.4f" % source['lon'], maxradius="%.1f" % maxRadius, \
        level="response")
    inv.write(invfile, format = 'stationxml')
else:
    from obspy import read_inventory
    inv = read_inventory(invfile)
    
sampling_interval = 60 # seconds
Q=None
ext='pickle'
secondsPerDay = 60 * 60 * 24
seed_ids = InventoryTools.inventory2traceid(inv)
print(seed_ids)
good_seed_ids = []
for seed_id in seed_ids:
    net, sta, loc, chan = seed_id.split('.')
    print(net, sta, loc, chan)
    if sta=='MSVF' and (chan[0:2]=='BH' or chan[0:2]=='BD'):
        good_seed_ids.append(seed_id)
        dayt = stime
        while dayt < etime:
            print(f"Fetching from FDSN and writing to SDS. seed_id: {seed_id}: Day: {dayt.strftime('%Y-%m-%d')}")
            st = client.get_waveforms(net, sta, loc, chan, dayt, dayt+secondsPerDay)
            sdsclient = SDS.SDSobj(paths['SDS_DIR'], sds_type='D', format='MSEED', streamobj=st)
            sdsclient.write()
            dayt += secondsPerDay
if len(good_seed_ids)>0:            
    pipelines.small_sausage(paths, stime, etime, sampling_interval=sampling_interval, source=source, invfile=invfile, Q=Q, ext=ext, net=net)
            


