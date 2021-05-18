#!/usr/bin/env python

import rasterio
import fiona
import numpy as np
import os
import time

from rasterio.plot import show
import matplotlib.pyplot as plt

from projections.rasterset import RasterSet, Raster
from projections.r2py import pythonify
import projections.r2py.modelr as modelr

# Open the mask shape file
shp_file = os.path.join(os.environ['DATA_ROOT'],
                        'from-adriana/tropicalforests.shp')
shapes = fiona.open(shp_file)

# Read Adriana's abundance model (mainland)
mod = modelr.load(os.path.join(os.environ['MODEL_DIR'],
                               'ab-model.rds'))
pythonify(mod)

# Import standard PREDICTS rasters
rasters = predicts.rasterset('luh5', 'historical', 1990, True)
rs = RasterSet(rasters, shapes = shapes, all_touched = True)

what = mod.output
rs[mod.output] = mod
stime = time.time()
data1, meta_data1 = rs.eval(what)
etime = time.time()
print("executed in %6.2fs" % (etime - stime))
show(data1)

##
## Compare with good raster
##
out = rasterio.open('adrid-good.tif')
good = out.read(1, masked=True)
diff = np.fabs(data1 - good)
print("max diff: %f" % diff.max())
assert np.allclose(data1, good, atol=1e-05, equal_nan=True)
del out

##
## Redo the projection using iterative API
##
mod = modelr.load('../models/ab-corrected.rds')
pythonify(mod)

# Import standard PREDICTS rasters
rasters2 = predicts.rasterset('rcp', 'aim', 2020, 'medium')
rs2 = RasterSet(rasters2, shapes = shapes, all_touched = True)

rs2[mod.output] = mod
stime = time.time()
rs2.write(what, 'adrid.tif')
etime = time.time()
print("executed in %6.2fs" % (etime - stime))

out = rasterio.open('adrid.tif')
data2 = out.read(1, masked=True)
diff = np.fabs(data1 - data2)
print("max diff: %f" % diff.max())

plot = None
if plot:
  fig, (ax1, ax2, ax3) = plt.subplots(1, 3, figsize=(10, 5))
  show(data1, ax=ax1, cmap='Greens', title='Non-incremental')
  show(data2, ax=ax2, cmap='Greens', title='Incremental')
  show(diff, ax=ax3, cmap='viridis', title='Difference')
  plt.show()

# Verify the data matches  
assert np.allclose(data1, data2, atol=1e-05, equal_nan=True)
