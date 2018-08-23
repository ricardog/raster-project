#!/usr/bin/env python

import time

import fiona
import multiprocessing
from rasterio.plot import show
import math
import os

import click
#import matlibplot.pyplot as plt
import numpy as np
import numpy.ma as ma
import rasterio
from rasterio.plot import show, show_hist

from projections.rasterset import RasterSet, Raster
from projections.simpleexpr import SimpleExpr
import projections.predicts as predicts
import projections.r2py.modelr as modelr
import projections.utils as utils


# Open the mask raster file
mask_file = os.path.join(utils.data_root(),
                         '1km/mainland-from-igor-edited.tif')
mask_ds = rasterio.open(mask_file)

# Richness compositional similarity model with updated PriMin-Urb coefficient
mod = modelr.load('/home/vagrant/katia/models/updated_compsim_rich.rds')
predicts.predictify(mod)

# Import standard PREDICTS rasters
rasters = predicts.rasterset('1km', 'medium', year = 2005)

# create an ISL_MAINL raster
# set it to Mainlands this time round (set Mainlands to 1 and Islands to 0)
rasters['ISL_MAINMAINLAND'] = SimpleExpr('ISL_MAINMAINLAND', '2')
rasters['ISL_MAINISLAND'] = SimpleExpr('ISL_MAINISLAND', '0')

rasters['adjGeogDist'] = SimpleExpr('adjGeogDist', '0')
rasters['cubeRtEnvDist'] = SimpleExpr('cubeRtEnvDist', '0')

# set up the rasterset, cropping to mainlands
rs = RasterSet(rasters, mask = mask_ds, maskval=0, crop = True)
# if you're projecting the whole world, use this code instead
#rs = RasterSet(rasters)

# evaluate the model
# model is logit transformed with an adjustment, so back-transformation
rs[mod.output] = mod
rs['output'] = SimpleExpr('output', '(inv_logit(%s) - 0.01) / (inv_logit(%f) - 0.01)' % (mod.output, mod.intercept))
rs.write('output', utils.outfn('katia', 'bii-sr-cs-mainlands.tif'))

