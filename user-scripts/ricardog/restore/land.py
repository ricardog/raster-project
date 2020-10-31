#!/usr/bin/env python3

import rasterio
import numpy.ma as ma

from projections.utils import luh2_static, outfn


def water():
    nodata = -9999.0
    with rasterio.open(luh2_static('carea')) as carea_ds:
            meta = carea_ds.meta.copy()
            meta.update({'driver': 'GTiff', 'compress': 'lzw',
                         'predictor': 3, 'nodata': nodata})
            carea = carea_ds.read(1, masked=True)
    with rasterio.open(luh2_static('icwtr')) as icwtr_ds:
        icwtr = icwtr_ds.read(1, masked=True)
    with rasterio.open(outfn('luh2', 'land.tif'), 'w', **meta) as land_ds:
        land = ma.masked_equal(carea * (1 - icwtr), 0)
        import pdb; pdb.set_trace()
        land.fill_value = nodata
        land_ds.write(land.filled(), indexes=1)
    return

if __name__ == '__main__':
    water()
