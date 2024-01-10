#!/usr/bin/env python
import obspy, os, glob
sacfiles = glob.glob('/data/Montserrat/Data_Dinko_Sandija/*_SAC')
outfile = 'continuous/dinkodata2.mseed'
dbout = 'db/dbdinko'
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
os.system(f'miniseed2db {outfile} {dbout}')    
