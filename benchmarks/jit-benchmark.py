#!/usr/bin/env python

import numpy as np
import os
import rasterio
import sys
import timeit

outdir = 'out/_d5ed9724c6cb2c78b59707f69b3044e6/'
sys.path.append(outdir)
import cropland_py
import cropland

import urban_py
import urban

import projections.modelr as modelr
import projections.predicts as predicts

cland_ds = rasterio.open('/out/luh5/cropland-recal.tif')
hpd_ds = rasterio.open('/out/luh5/gluds00ag-full.tif')
unsub_ds = rasterio.open('/out/luh5/un_subregions-full.tif')

unsub = unsub_ds.read(1, masked=True)
hpd = hpd_ds.read(1, masked=True)
cland = cland_ds.read(1, masked=True)

mask = np.logical_or(np.logical_or(cland.mask, hpd.mask), unsub.mask)
cland.mask = mask
hpd.mask = mask
unsub.mask = mask

c = cland.compressed()
h = hpd.compressed()
u = unsub.compressed()

str1 = "out2 = cropland_py.intense(c, h, u)"
str2 = "out = cropland.intense(c, h, u)"
str3 = "out2 = urban_py.intense(c, h, u)"
str4 = "out = urban.intense(c, h, u)"
n = 10

prelude = "from __main__ import c, h, u, cropland_py, cropland, urban_py, urban"
print("c1: ", timeit.timeit(str1, setup=prelude, number=n))
print("c2: ", timeit.timeit(str2, setup=prelude, number=n))

print("u1: ", timeit.timeit(str3, setup=prelude, number=n))
print("u2: ", timeit.timeit(str4, setup=prelude, number=n))

mod = modelr.load(os.path.join(outdir, 'ab-model.rds'))
predicts.predictify(mod)
logHPD_rs = np.log(h + 1) / 10.02803
df = {'cropland': c,
      'cropland_intense': c,
      'cropland_light': c,
      'cropland_minimal': c,
      'logHPD_rs': logHPD_rs,
      'pasture': c,
      'pasture_intense': c,
      'pasture_light': c,
      'pasture_minimal': c,
      'plantation_pri': c,
      'plantation_pri_intense': c,
      'plantation_pri_light': c,
      'plantation_pri_minimal': c,
      'primary_intense': c,
      'primary_light': c,
      'secondary': c,
      'secondary_light': c,
      'secondary_minimal': c,
      'urban': c,
      'urban_intense': c,
      'urban_minimal': c}
mod.eval(df)

str3 = "out = mod.eval(df)"
prelude = "from __main__ import df, mod"
print("a: ", timeit.timeit(str3, setup=prelude, number=n))

#print(cland.flags)

#ds = gdal.Open('cropland-recal.tif')
#data = ds.GetRasterBand(1).ReadAsArray()
#print(data.flags)
