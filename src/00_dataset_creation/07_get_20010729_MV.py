#!/usr/bin/env python
# coding: utf-8

# not for running at MESS2024
# This Jupyter notebook is intended to be run on hal9000 at USF seismic lab.
# It gathers continuous waveform data for Montserrat 2001 that is stored in a Seisan database.
# It uses Antelope tools to create SDS, SDS_VEL, and SDS_DISP archives
# It also computes RSAM, VSAM, VSEM, DSAM, DR, and DRS. 
import os
import sys
sys.path.append('../../src/lib')
import setup_paths
paths = setup_paths.paths

seisandbdir =  '/data/SEISAN_DB/WAV/DSNC_'
sdsdir = paths['SDS_DIR']
invfile = os.paths.join(paths['RESPONSE_DIR'],'MV.xml')
startt = obspy.core.UTCDateTime(2001, 7, 28, 0, 0, 0)
endt = obspy.core.UTCDateTime(2001, 7, 31, 0, 0, 0)
delta = 10 # seconds    
source = {'lat':16.71111, 'lon':-62.17722}
dbout = os.path.join(paths['DB_DIR'],f"dbMontserrat{startt.year}")
pipelines.seisandb2SDS(seisandbdir, paths['SDS_DIR'], startt, endt, dbout)
pipelines.compute_raw_metrics(paths['SDS_DIR'], startt, endt, sampling_interval=delta, do_RSAM=True)
pipelines.compute_SDS_VEL(paths, startt, endt, invfile=invfile)
pipelines.compute_velocity_metrics(paths, startt, endt, sampling_interval=delta, do_VSAM=True, do_VSEM=True)
pipelines.compute_SDS_DISP(paths, startt, endt, invfile=invfile)
pipelines.compute_displacement_metrics(paths, startt, endt, sampling_interval=delta, do_DSAM=True)
pipelines.reduce_to_1km(paths, do_VR=False, do_VRS=False, do_ER=True, do_ERS=True, do_DR=True, do_DRS=True, invfile=invfile, source=source)

# SDS -> RSAM
# SDS_VEL -> VSAM, VSEM
# SDS_DISP -> DSAM
# VSAM -> VR, VRS (VSAM reduced to "source" or "standard distance". But rarely done)
# VSEM -> ER, ERS (VSEM reduced to "source" or "standard distance" using Boatwright or Johnson & Aster equations)
# DSAM -> DR, DRS (DSAM reduced to "source" or "standard distance")
