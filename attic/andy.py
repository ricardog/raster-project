#!/usr/bin/env python3

import numpy as np
import numpy.ma as ma
import rasterio

def doit():
    plant = '/Users/ricardog/src/raster-project/attic/sdpt_qd/all-full.tif'
    states = '/Users/ricardog/src/eec/data/luh2_v2/historical/states.nc'
    static = '/Users/ricardog/src/eec/data/luh2_v2/staticData_quarterdeg.nc'
    with rasterio.open(plant) as plant_ds:
        print('Read SDPT raster')
        sdpt = plant_ds.read(1, masked=True)
        fract = 1 - sdpt
        out = np.full_like(sdpt, 0)
        out += sdpt
        for lu in ('pastr', 'range', 'c3ann', 'c3per', 'c4ann', 'c4per',
                   'c3nfx'):
            with rasterio.open('netcdf:' + states + ':' + lu) as ds:
                print(lu)
                lu_data = ds.read(1166, masked=True) * fract
                out += lu_data
        with rasterio.open('netcdf:' + static + ':icwtr') as icwtr_ds:
            icwtr = icwtr_ds.read(1, masked=False)
        out2 = ma.masked_where(icwtr == 1, out)
        out2.fill_value = -9999
        meta = plant_ds.meta.copy()
        meta.update({'compress': 'lzw', 'predictor': 2,
                     'nodata': -9999})
        with rasterio.open('andy.tif', 'w', **meta) as out_ds:
            print('writing')
            out_ds.write(out2.filled(), indexes=1)
    print('done')
    return

if __name__ == '__main__':
    doit()

