#!/usr/bin/env python

from projections.atlas import atlas
from projections.rasterset import RasterSet, Raster
import projections.predicts as predicts
import projections.rds as rds

# Read Katia's abundance model (mainland)
mod = rds.read('../models/ab-mainland.rds')
predicts.predictify(mod)

# Import standard PREDICTS rasters
rasters = predicts.rasterset('rcp', 'aim', 2020, 'medium')
rs = RasterSet(rasters)

rs[mod.output()] = mod
data = rs.eval(mod.output())

# Display the raster
atlas(data, mod.output(), 'viridis')
