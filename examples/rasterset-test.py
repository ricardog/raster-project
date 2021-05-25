#!/usr/bin/env python

from projections import atlas, predicts
from rasterset import RasterSet
from r2py import modelr

# Read Katia's abundance model (mainland)
mod = modelr.load("../models/ab-mainland.rds")

# Import standard PREDICTS rasters
rasters = predicts.rasterset("rcp", "aim", 2020, "medium")
rs = RasterSet(rasters)

rs[mod.output()] = mod
data = rs.eval(mod.output())

# Display the raster
atlas(data, mod.output(), "viridis")
