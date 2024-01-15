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
startt = obspy.core.UTCDateTime(2003, 7, 12, 0, 0, 0)
endt = obspy.core.UTCDateTime(2003, 7, 16, 0, 0, 0)
sampling_interval = 60 # seconds
source = {'lat':16.71111, 'lon':-62.17722}
dbout = os.path.join(paths['DB_DIR'],f"dbMontserrat{startt.year}")
ext='pickle'
Q=None
pipelines.big_sausage(seisandbdir, paths, startt, endt, sampling_interval=sampling_interval, source=source, invfile=invfile, Q=Q, ext=ext, dbout=dbout, net=net)

