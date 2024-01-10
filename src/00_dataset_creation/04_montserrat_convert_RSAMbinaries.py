#!/usr/bin/env python
# coding: utf-8

# In[ ]:


# convert original RSAM binary files to CSV (and Pickle) files

# not for running at MESS2024
# This Jupyter notebook is intended to be run on hal9000 at USF seismic lab.
# It converts RSAM binary files created by the original RSAM system in Montserrat in 1996
import os
import sys
import obspy
sys.path.append('..')
import setup_paths
paths = setup_paths.paths
sys.path.append('../../lib')
from SAM import RSAM

os.system(f"cp /data/Montserrat/ASN/RSAM/RSAM_1/M???????.DAT {paths['SAMBINARY_DIR']}")

st = obspy.core.Stream()
stime = obspy.core.UTCDateTime(1996,1,1,0,0,0)
etime = obspy.core.UTCDateTime(1996,12,31,23,59,59)
stations = ['MCPZ', 'MGAT', 'MGHZ', 'MLGT', 'MRYT', 'MSPT', 'MSSZ', 'MWHT']
rsamObj = SAM.readRSAMbinary(paths['SAMBINARY_DIR'], stations, stime, etime)
#rsamObj.plot()
rsamObj.write(paths['SAM_DIR'], ext='csv')
rsamObj.write(paths['SAM_DIR'], ext='pickle')

