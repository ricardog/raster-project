#!/usr/bin/env python

import fiona
import time
from rasterio.plot import show, show_hist

from rasterset import RasterSet, Raster
import projections.predicts as predicts
import projections.modelr as modelr
from projections.r2py import pythonify

# Open the mask shape file
shp_file = "../../data/from-adriana/tropicalforests.shp"
shapes = fiona.open(shp_file)

# Read Adriana's abundance model (mainland)
mod = modelr.load("../models/ab-corrected.rds")
pythonify(mod)

# Import standard PREDICTS rasters
rasters = predicts.rasterset("1km", "foo", 2005, "historical")
rs = RasterSet(rasters, shapes=shapes, all_touched=True)

rs[mod.output] = mod
what = mod.output
stime = time.time()
data = rs.write(what, "hires.tif")
etime = time.time()
print("executed in %6.2fs" % (etime - stime))
