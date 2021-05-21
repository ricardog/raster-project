#!/usr/bin/env python

from projections.atlas import atlas
from rasterset import RasterSet, Raster
from projections.r2py import pythonify
import projections.rds as rds

# Read Katia's abundance model (mainland)
mod = rds.read('../models/ab-mainland.rds')
pythonify(mod)

# Import standard PREDICTS rasters
rasters = predicts.rasterset('rcp', 'aim', 2020, 'medium')
rs = RasterSet(rasters)

rs[mod.output()] = mod
data = rs.eval(mod.output())

# Display the raster
atlas(data, mod.output(), 'viridis')
