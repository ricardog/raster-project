#!/usr/bin/env python

import argparse
import math
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
        
from rasterset import RasterSet, Raster, SimpleExpr
from projections.r2py import pythonify
import projections.r2py.modelr as modelr
import projections.utils as utils

RD_DIST_MIN = 0
RD_DIST_MAX = 195274.3
HPD_MIN = 0
HPD_MAX = 22490

parser = argparse.ArgumentParser(description="sr.py -- richness projections")
parser.add_argument('--mainland', '-m', dest='mainland', default=False,
                    action='store_true',
                    help='Project using mainland coefficients '
                    '(default: islands)')
parser.add_argument('--clip', '-c', dest='clip', default=False,
                    action='store_true',
                    help='Clip predictor variables to max value seen '
                    'during model fitting')
args = parser.parse_args()

if args.mainland:
  ISLMAIN = 1
  mask_file = os.path.join(utils.data_root(),
                           '1km/mainland-from-igor-edited-at.tif')
else:
  ISLMAIN = 0
  mask_file = os.path.join(utils.data_root(),
                         '1km/islands-from-igor-edited-at.tif')

# Open the mask raster file (Mainlands)
mask_ds = rasterio.open(mask_file)

# Read Katia's richness model
mod = modelr.load('/home/vagrant/katia/models/best_model_rich.rds')
pythonify(mod)

# Import standard PREDICTS rasters
rasters = predicts.rasterset('1km', 'medium', year = 2005)

# create an ISL_MAINL raster
# set it to Mainlands this time round (set Mainlands to 1 and Islands to 0)
rasters['ISL_MAINLMAINLAND'] = ISLMAIN

# specify the plantation forest maps as 0
# not sure why it's plantations_pri rather than plantation, but hey ho
rasters['plantation_pri'] = 0
rasters['plantation_pri_minimal'] = 0
rasters['plantation_pri_light'] = 0
rasters['plantation_pri_intense'] = 0

## If clip is true, limit the predictor variable values to the max seen
## when fitting the model
if args.clip:
  rasters['clip_hpd'] = 'clip(hpd_ref, %f, %f)' %(HPD_MIN, HPD_MAX)
else:
  rasters['clip_hpd'] = 'hpd_ref'
###log values and then rescale them 0 to 1
# we need to check whether the logHPD.rs automatically produced uses the
# same values we use if not, manually create logHPD.rs
rasters['logHPD_rs'] = 'scale(log(clip_hpd + 1), 0.0, 1.0, 0.0, 10.02087)'

# Same is true for logDistRd_rs
rasters['DistRd'] = Raster('DistRd', os.path.join(utils.data_root(), '1km/rddistwgs.tif')) ###Use new raster
## If clip is true, limit the predictor variable values to the max seen
## when fitting the model
if args.clip:
  rasters['clipDistRd'] = 'clip(DistRd, %f, %f)' %(RD_DIST_MIN, RD_DIST_MAX)
else:
    rasters['clipDistRd'] = 'DistRd'
rasters['logDistRd_rs'] = 'scale(log(clipDistRd + 100), 0.0, 1.0, -1.120966, 12.18216)'
###Added +100 to DistRd to deal with  zero values in raster


# set up the rasterset, cropping to mainlands
rs = RasterSet(rasters, mask = mask_ds, maskval=0, crop = True)
# if you're projecting the whole world, use this code instead
#rs = RasterSet(rasters)

# note that the intercept value has been calculated for the baseline
# land use when all other variables are held at 0

# Calculate an intercept where DistRd is set to the max value
# (logDistRd_ds = 1).
intercept = mod.partial({'ISL_MAINLMAINLAND': ISLMAIN,
                         'logDistRd_rs': 1.0})
print("intercept: %.5f" % intercept)
# Verify the computed intercept matches R-computed intercept.
if args.mainland:
  assert math.isclose(intercept, 2.626708, rel_tol=0.001)
else:
  assert math.isclose(intercept, 2.796343, rel_tol=0.001)

# evaluate the model
# model is square root abundance so square it
rs[mod.output] = mod
rs['output'] = 'exp(%s) / exp(%f)' % (mod.output, intercept)

fname = 'sr-%s.tif' % ('mainland' if args.mainland else 'islands')
path = ('katia', 'clip' if args.clip else 'no-clip', fname)
rs.write('output', utils.outfn(*path))
