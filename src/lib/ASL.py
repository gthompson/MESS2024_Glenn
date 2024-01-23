import pygmt
import numpy as np
import pandas as pd
import math
import matplotlib.pyplot as plt
import obspy
from obspy.geodetics import locations2degrees, degrees2kilometers
from SAM import DSAM

def inventory2seedids(inv, chancode='', force_location_code='*'):
    seed_ids = list()

    for networkObject in inv:
        if chancode:
            networkObject = networkObject.select(channel=chancode)
        stationObjects = networkObject.stations

        for stationObject in stationObjects:
            channelObjects = stationObject.channels
            for channelObject in channelObjects:
                this_seed_id = networkObject.code + '.' + stationObject.code + f'.{force_location_code}.' \
                            + channelObject.code
                seed_ids.append(this_seed_id)
    
    return seed_ids

def montserrat_topo_map(show=False, zoom_level=1, inv=None, add_labels=False):
    #define etopo data file
    # topo_data = 'path_to_local_data_file'
    #topo_data = '@earth_relief_30s' #30 arc second global relief (SRTM15+V2.1 @ 1.0 km)
    # topo_data = '@earth_relief_15s' #15 arc second global relief (SRTM15+V2.1)
    topo_data = '@earth_relief_03s' #3 arc second global relief (SRTM3S)
    
    # define plot geographical range
    if zoom_level==1:
        minlon, maxlon = -62.25, -62.13
        minlat, maxlat = 16.66, 16.83
    elif zoom_level==2:
        minlon, maxlon = -62.21, -62.15
        minlat, maxlat = 16.66, 16.74    
    # Visualization
    fig = pygmt.Figure()
    
    # make color pallets
    pygmt.makecpt(
        cmap='topo',
        series='-1300/1300/100',
        continuous=True
    )
    
    # plot high res topography
    fig.grdimage(
        grid=topo_data,
        region=[minlon, maxlon, minlat, maxlat],
        projection='M4i',
        shading=True,
        frame=True
        )
    
    # plot continents, shorelines, rivers, and borders
    fig.coast(
        region=[minlon, maxlon, minlat, maxlat],
        projection='M4i',
        shorelines=True,
        frame=True
        )
    
    # plot the topographic contour lines
    fig.grdcontour(
        grid=topo_data,
        interval=100,
        annotation="100+f6p",
        limit="-1300/1300", #to only display it below 
        pen="a0.15p"
        )
    
    # Plot colorbar
    fig.colorbar(
        frame='+l"Topography"',
    #     position="x11.5c/6.6c+w6c+jTC+v" #for vertical colorbar
        )
    
    if inv:
        seed_ids = inventory2seedids(inv, force_location_code='')
        #print(seed_ids)
        stalat = [inv.get_coordinates(seed_id)['latitude'] for seed_id in seed_ids]
        stalon = [inv.get_coordinates(seed_id)['longitude'] for seed_id in seed_ids]
        fig.plot(x=stalon, y=stalat, style="s0.4c", fill="dodgerblue4", pen='2p,black')  
        
        if add_labels:
            #print('Adding station labels')
            for thislat, thislon, this_id in zip(stalat, stalon, seed_ids):
                net, sta, loc, chan = this_id.split('.')
                #print(thislat, thislon, net, sta, loc, chan)
                fig.text(x=thislon, y=thislat, text=sta, textfiles=None, \
                        #font="Courier-Bold",
                        justify="ML",
                        offset="0.2c/0c",)
    
    if show:
        fig.show();


    return fig

class Grid:
    def __init__(self, centerlat, centerlon, nlat, nlon, node_spacing_m):
        deg2m = degrees2kilometers(1.0) * 1000.0
        node_spacing_lat = node_spacing_m / deg2m
        minlat = centerlat - (nlat-1)/2 * node_spacing_lat
        maxlat = centerlat + (nlat-1)/2 * node_spacing_lat
        latrange = np.array([lat for lat in np.arange(minlat, maxlat, node_spacing_lat)])
        node_spacing_lon = node_spacing_lat / np.cos(centerlat / (2 * math.pi))
        minlon = centerlon - (nlon-1)/2 * node_spacing_lon
        maxlon = centerlon + (nlon+1)/2 * node_spacing_lon
        lonrange = np.array([lon for lon in np.arange(minlon, maxlon, node_spacing_lon)])
        gridlon, gridlat = np.meshgrid(lonrange, latrange)
        self.gridlon = gridlon
        self.gridlat = gridlat
        self.node_spacing_lat = node_spacing_lat
        self.node_spacing_lon = node_spacing_lon
        self.lonrange = lonrange
        self.latrange = latrange

    def plot(self, node_spacing_m):
        fig = montserrat_topo_map()
        #plt.plot(self.gridlon, self.gridlat, marker='+', color='k', linestyle='none')
        #plt.show()
        symsize = node_spacing_m/9000
        stylestr = f'+{symsize}c'
        
        fig.plot(x=self.gridlon.reshape(-1), y=self.gridlat.reshape(-1), style=stylestr, pen='black')
        fig.show()


def simulate_DSAM(inv, source, units='m', surfaceWaves=False, wavespeed_kms=1.5, peakf=8.0, Q=None, noise_level_percent=0.0):
    npts = len(source['DR'])
    seed_ids = inventory2seedids(inv, force_location_code='')
    st = obspy.Stream()
    
    for id in seed_ids:
        coordinates = inv.get_coordinates(id)
        stalat = coordinates['latitude']
        stalon = coordinates['longitude']
        distance_km = degrees2kilometers(locations2degrees(stalat, stalon, source['lat'], source['lon']))
        tr = obspy.Trace()
        tr.id = id
        tr.stats.starttime = source['t'][0]
        tr.stats.delta = source['t'][1] - source['t'][0]
        gsc = DSAM.compute_geometrical_spreading_correction(distance_km, tr.stats.channel, surfaceWaves=surfaceWaves, wavespeed_kms=wavespeed_kms, peakf=peakf)
        isc = DSAM.compute_inelastic_attenuation_correction(distance_km, peakf, wavespeed_kms, Q)
        tr.data = source['DR'] / (gsc * isc)
        if noise_level_percent > 0.0:
            tr.data += np.multiply(np.nanmax(tr.data), np.random.uniform(0, 1, size=npts) )
            pass # do something here
        tr.stats['units'] = units
        st.append(tr)
    return DSAM(stream=st, sampling_interval=tr.stats.delta)

'''
def simulate_DSAM(inv, source, units='m', surfaceWaves=False, wavespeed_kms=1.5, peakf=8.0, Q=None, noise_level_percent=0.0):
    a = np.random.uniform(0, 1, size=source['npts']) * source['max_DR']
    seed_ids = inventory2seedids(inv, force_location_code='')
    st = obspy.Stream()
    
    for id in seed_ids:
        coordinates = inv.get_coordinates(id)
        stalat = coordinates['latitude']
        stalon = coordinates['longitude']
        distance_km = degrees2kilometers(locations2degrees(stalat, stalon, source['lat'], source['lon']))
        tr = obspy.Trace()
        tr.id = id
        tr.stats.starttime = source['starttime']
        tr.stats.delta = source['sampling_interval']
        gsc = DSAM.compute_geometrical_spreading_correction(distance_km, tr.stats.channel, surfaceWaves=surfaceWaves, wavespeed_kms=wavespeed_kms, peakf=peakf)
        isc = DSAM.compute_inelastic_attenuation_correction(distance_km, peakf, wavespeed_kms, Q)
        tr.data = a / (gsc * isc)
        if noise_level_percent > 0.0:
            tr.data += np.multiply(np.nanmax(tr.data), np.random.uniform(0, 1, size=source['npts']) )
            pass # do something here
        tr.stats['units'] = units
        st.append(tr)
    return DSAM(stream=st, sampling_interval=source['sampling_interval'])
'''

class ASL:
    def __init__(self, samobject, metric, inventory, gridobj):
        ''' 
        ASL: Simple amplitude-based source location for volcano-seismic data 
        This program takes a DSAM object as input
        Then armed with an inventory that provides station coordinates, it attempts
        to find a location for each sample by reducing amplitudes based on the grid
        node to station distance. Grid nodes are contained in a Grid object.

        ASL can use any one of the mean, max, median, VLP, LP, or VT metrics from a DSAM object

        '''

        if isinstance(samobject, DSAM):
            pass
        else:
            print('invalid type passed as samobject. Aborting')
            return

        self.samobject = samobject
        self.metric = metric
        self.inventory = inventory
        self.gridobj = gridobj
        self.node_distances_km = {}
        self.station_coordinates = {}
        self.amplitude_corrections = {}
        
    def setup(self, surfaceWaves=False):  
        self.compute_grid_distances()
        self.compute_amplitude_corrections(surfaceWaves = surfaceWaves)

    def compute_grid_distances(self):
        st = self.samobject.to_stream()
        coordinates = {}
        node_distances_km = {}
        for tr in st:
            d_list = []
            try:
                coordinates[tr.id] = self.inventory.get_coordinates(tr.id)
                stalat = coordinates[tr.id]['latitude']
                stalon = coordinates[tr.id]['longitude']
                #print(tr.id, stalat, stalon)
            except Exception as e:
                #print(e)
                continue
            gridlat = self.gridobj.gridlat.reshape(-1)
            gridlon = self.gridobj.gridlon.reshape(-1)
            nodelatlon = zip(gridlat, gridlon)
            distances = np.array([locations2degrees(nodelat, nodelon, stalat, stalon) for nodelat, nodelon in nodelatlon])       
            node_distances_km[tr.id] = np.array([degrees2kilometers(thisdistance) for thisdistance in distances])
        self.node_distances_km = node_distances_km
        self.station_coordinates = coordinates 
        
    @staticmethod
    def set_peakf(metric, df):
        if metric in ['mean', 'median', 'max', 'rms']:
            ratio = df['VT'].sum()/df['LP'].sum()
            peakf = np.sqrt(ratio) * 4
        elif metric == 'VLP':
            peakf = 0.1
        elif metric == 'LP':
            peakf = 2.0
        elif metric == 'VT':
            peakf = 8.0
        return peakf
             
    def compute_amplitude_corrections(self, surfaceWaves=False, wavespeed_kms=None, Q=None, fix_peakf=None):
        #st = self.samobject.to_stream()
        corrections = {}
        if not wavespeed_kms:
            if surfaceWaves:
                wavespeed_kms = 1.5
            else:
                wavespeed_kms = 3.0
        for seed_id, df in self.samobject.dataframes.items():
            if fix_peakf:
                peakf = fix_peakf
            else:
                peakf = self.set_peakf(self.metric, df)
            wavelength_km = peakf * wavespeed_kms
            distance_km = self.node_distances_km[seed_id]
            #print(seed_id, len(distance_km), distance_km)
            gsc = DSAM.compute_geometrical_spreading_correction(distance_km, seed_id[-3:], \
                                                       surfaceWaves=surfaceWaves, \
                                                       wavespeed_kms=wavespeed_kms, peakf=peakf)
            #print(seed_id, 'gsc: ', gsc)
            isc = DSAM.compute_inelastic_attenuation_correction(distance_km, peakf, wavespeed_kms, Q) 
            #print(seed_id, 'isc: ', isc)
            '''
            if surfaceWaves and seed_id[-2]=='H':
                gsc = np.sqrt(np.multiply(self.node_distances_km[seed_id], wavelength_km))
            else:
                gsc = self.node_distances_km[seed_id]
            #print(seed_id, gsc)
            
            if Q:
                t = np.divide(self.node_distances_km[seed_id], wavespeed_kms)
                iac = np.power(math.e, math.pi * peakf * t / Q)
                corrections[seed_id] = np.multiply(gsc, iac)
            else:
                corrections[seed_id] = gsc
            '''
            corrections[seed_id] = gsc * isc
            #print(corrections[seed_id])
        self.amplitude_corrections = corrections
            
    def locate(self):
        gridlat = self.gridobj.gridlat.reshape(-1)
        gridlon = self.gridobj.gridlon.reshape(-1)
        st = self.samobject.to_stream(metric=self.metric)
        seed_ids = [tr.id for tr in st]
        lendata = len(st[0].data)
        #print(seed_ids[0])
        #print(self.amplitude_corrections)
        corrections = self.amplitude_corrections[seed_ids[0]]
        #print(len(corrections))
        #print(self.amplitude_corrections[seed_ids[0]])
        locations = []
        best_corrections = {}
        source_amplitudes = []
        #t = [t.datetime for t in st[0].times('utcdatetime')]
        t = st[0].times('utcdatetime')
        for i in range(lendata): # loop ovder time samples
            y = [tr.data[i] for tr in st] # (len(st), 1)
            reduced_y = []
            misfit = []
            best_j = -1
            best_misfit = 1e15

            #####################################################################
            ##### how to vectorize this loop to compute misfit for each node? ###
            
            for j in range(len(corrections)): # loop over nodes
                # assume source is at grid node j
                c = [self.amplitude_corrections[id][j] for id in seed_ids] # corrections for this node (len(st), 1)
                #if self.metric=='energy': # for VSEM
                #    c = np.multiply(c,c)
                #print(c)
                reduced_y = np.multiply(y, c) # correcting everything to 1 km distance for all seed ids
                this_misfit = np.nanstd(reduced_y)/np.nanmedian(reduced_y)
             #####################################################################
                
                #print(this_misfit)
                if this_misfit < best_misfit:
                    best_misfit = this_misfit
                    best_j = j
                
            for tracenum, id in enumerate(seed_ids):
                A = y[tracenum] * self.amplitude_corrections[id][best_j]
            best_A = np.nanmedian(A)
            misfit.append(best_misfit)
            locations.append( ( t[i], gridlat[best_j], gridlon[best_j], best_A )  )
            
        return locations
        # Here is where i would add loop over shrinking grid

    def fast_locate(self):
        gridlat = self.gridobj.gridlat.reshape(-1)
        gridlon = self.gridobj.gridlon.reshape(-1)
        st = self.samobject.to_stream(metric=self.metric)
        seed_ids = [tr.id for tr in st]

        t = st[0].times('utcdatetime')

        source_DR = np.empty(len(t), dtype=float)
        source_lat = np.empty(len(t), dtype=float)
        source_lon = np.empty(len(t), dtype=float)
        for i in range(len(t)): # loop ovder time samples
            DR_stations_nodes = np.empty(  ( len(st), len(gridlat) ) )
            for j, seed_id in enumerate(seed_ids):
                tr = st.select(id=seed_id)[0]
                DR_stations_nodes[j] = np.multiply(self.amplitude_corrections[seed_id], tr.data[i])
            #print('shape of all array = ',DR_stations_nodes.shape)
            DR_mean_nodes = np.nanmean(DR_stations_nodes, axis=0)
            DR_std_nodes = np.nanstd(DR_stations_nodes, axis=0)
            #print('shape of mean array = ',DR_mean_nodes.shape)
            misfit = np.divide(DR_std_nodes, DR_mean_nodes)
            #print('shape of misfit array = ',misfit.shape)
            lowest_misfit = np.nanmin(misfit)
            lowest_misfit_index = np.argmin(misfit)
            source_DR[i] = DR_mean_nodes[lowest_misfit_index]
            source_lat[i] = gridlat[lowest_misfit_index]
            source_lon[i] = gridlon[lowest_misfit_index]
            
        source = {'t':t, 'lat':source_lat, 'lon':source_lon, 'DR':source_DR*1e7}
        return source

    def plot(self, source=None, cross_scale=1e3, zoom_level=1, threshold_DR=None, scale=1e-2):

        #stalat = [self.station_coordinates[seed_id]['latitude'] for seed_id in self.station_coordinates]
        #stalon = [self.station_coordinates[seed_id]['longitude'] for seed_id in self.station_coordinates]
        
        
        if source:
            print(max(source['DR']))
                
            # timeseries of DR vs threshold_amp
            t_dt = [this_t.datetime for this_t in source['t']]
            plt.figure()
            plt.plot(t_dt, source['DR'])
            plt.plot(t_dt, np.ones(source['DR'].size) * threshold_DR)
            plt.xlabel('Date/Time (UTC)')
            plt.ylabel('Reduced Displacement (${cm}^2$)')

              
            if threshold_DR:
                
                indices = source['DR']<threshold_DR
                source['DR'][indices]=0.0
                source['lat'][indices]=None
                source['lon'][indices]=None
            
               
            # Heatmap
            symsize = source['DR']*cross_scale
            df = pd.DataFrame()
            df['time'] = source['t']
            df['lon'] = source['lon']
            df['lat'] = source['lat']
            df['DR'] = source['DR']
            df['energy'] = np.multiply(source['DR'], source['DR'])
            #unique_locationsDF = df[['lat', 'lon']].value_counts().reset_index(name='count')
            unique_locationsDF = df.groupby(['lat', 'lon'])['energy'].sum().reset_index()
            #print(unique_locationsDF)
            fig = montserrat_topo_map(zoom_level=zoom_level, inv=self.inventory)
            x=unique_locationsDF['lon'].to_numpy()
            y=unique_locationsDF['lat'].to_numpy()
            symsize = np.sqrt(unique_locationsDF['energy'].to_numpy())*scale/len(t_dt)
            symsize = np.divide(symsize, np.nanmax(symsize))
            print(max(symsize))
            #fig.plot(x=x, y=y, style='c0.3c', fill='black', pen='black')
            fig.plot(x=x, y=y, size=symsize, style='cc', fill='black', pen='2p,black')
            #fig.plot(x=stalon, y=stalat, style="s0.3c", fill="black")
            fig.show();

            '''
            # time-longitude plot
            plt.figure()
            plt.scatter(t_dt, lon, s=source['DR']*cross_scale, marker='x')  

            # time-latitude plot
            plt.figure()
            plt.scatter(t_dt, lat, s=source['DR']*cross_scale, marker='x')
            '''
            
        else: # no location data      
            fig = montserrat_topo_map(zoom_level=zoom_level, inv=self.inventory, show=True)
          
