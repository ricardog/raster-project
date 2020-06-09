#!/usr/bin/env python3

import matplotlib.pyplot as plt
from netCDF4 import Dataset
import numpy.ma as ma
import pandas as pd
import rasterio

import cell_area

icew_ds = rasterio.open('/data/rcp1.1/gicew.1700.txt')
icew = icew_ds.read(1)
land = 1 - icew

src = rasterio.open('netcdf:cell.land_0.5_share.nc:crop')

ds = Dataset('cell.land_0.5.nc')

df = pd.DataFrame(columns=['crop', 'past', 'forestry', 'primforest',
                           'secdforest', 'urban', 'other'],
                  index=ds.variables['time'][:])
carea = cell_area.raster_cell_area(src, full=True) / 1e6
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
