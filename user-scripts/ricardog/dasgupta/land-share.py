#!/usr/bin/env python3

import matplotlib.pyplot as plt
from netCDF4 import Dataset
import numpy.ma as ma
import pandas as pd
import rasterio

from attic.cell_area import raster_cell_area
from projections.utils import data_file

icew_ds = rasterio.open(data_file('rcp1.1', 'gicew.1700.txt'))
icew = icew_ds.read(1)
land = 1 - icew

fname = data_file('vivid', 'HMT_Early_Action', 'spatial_files',
                  'cell.land_0.5.nc')
fname = data_file('vivid', 'HMT_Late_Action', 'spatial_files',
                  'cell.land_0.5.nc')
fname = data_file('vivid', 'sample', 'spatial_files',
                  'cell.land_0.5.nc')
src = rasterio.open(f'netcdf:{fname}:crop')

ds = Dataset(fname)

df = pd.DataFrame(columns=['crop', 'past', 'forestry', 'primforest',
                           'secdforest', 'urban', 'other'],
                  index=ds.variables['time'][:])
carea = raster_cell_area(src, full=True) / 1e6
carea = ma.masked_array(carea)
carea.mask = ds.variables['crop'][0, ::-1, :].mask

for lu in df.columns: 
    for idx, year in enumerate(df.index): 
        data = ds.variables[lu][idx, ::-1, :] 
        df.loc[year, lu] = data.sum() 
df2 = (df / (land * carea / 1e4).sum()) * 100
df2.sum(axis=1)
import pdb; pdb.set_trace()

fig = plt.figure(figsize=(11, 8))
ax = plt.gca()
df2.plot.area(ax=ax)
fig.savefig('land-share.png')
plt.show()
