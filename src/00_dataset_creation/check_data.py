#!/usr/bin/env python
# Usage: python check_data.py {net} {startt} {endt}
#        python check_data.py MV "1997/12/14" "1997/12/28"

import os
import sys
import obspy
sys.path.append('../lib')
import setup_paths
paths=setup_paths.paths
import pipelines


net = sys.argv[1]
invfile = os.path.join(paths['RESPONSE_DIR'],f"{net}.xml")
startt = obspy.core.UTCDateTime(sys.argv[2])
endt = obspy.core.UTCDateTime(sys.argv[3])
sampling_interval = 60 # seconds
ext='pickle'

do_metric = pipelines.check_what_to_do(paths, net, startt, endt, sampling_interval=sampling_interval, ext=ext, invfile=invfile)
for metric in do_metric:
    print(f"{metric} exists = {not do_metric[metric]}")
