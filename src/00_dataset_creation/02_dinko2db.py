#!/usr/bin/env python
# not for running at MESS2024
# This script is intended to be run on hal9000 at USF seismic lab.
# It gathers waveform data that Dinko Sindaja used for a Montserrat moment tensor paper, and converts it from SAC to MiniSEED.
# It then converts to SDS and wraps that in an Antelope/CSS3.0 database. 
import obspy, os, glob, sys
sys.path.append('..')
import setup_paths
paths = setup_paths.paths

sacfiles = glob.glob('/data/Montserrat/Data_Dinko_Sandija/*_SAC')
outfile = os.path.join(paths['EVENTS_DIR'], 'dinkodata.mseed')
outputdir = paths['SDS_DIR']
dbout = os.paths.join(paths['DB_DIR'],'dbdinko')
os.system(f"rm {dbout}*")
st = obspy.Stream()
for sacfile in sacfiles:
    print(sacfile)
    # 2012-03-23-0640-00S.MVO___024_MBGH__BH_N_SAC
    this_st=obspy.read(sacfile, format='sac') 
    for tr in this_st:
        tr.stats.station = sacfile[-14:-10]
        tr.stats.channel = tr.stats.channel[0:2] + sacfile[-5] 
        #print(tr.stats)
        st.append(tr)
st.write(outfile, format='mseed')
#os.system(f'miniseed2db {outfile} {dbout}')    
os.system(f"miniseed2days -U -w '%Y/%{{net}}/%{{sta}}/%{{chan}}.D/%{{net}}.%{{sta}}.%{{loc}}.%{{chan}}.D.%Y.%j' -S {outputdir} -d {dbout} {outfile}")