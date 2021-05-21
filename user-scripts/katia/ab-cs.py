#!/usr/bin/env python

import argparse

import math
import os

import rasterio

from rasterset import RasterSet, SimpleExpr
from projections.r2py import pythonify
import projections.r2py.modelr as modelr
import projections.utils as utils

parser = argparse.ArgumentParser(
    description="ab-cs.py -- abundance-based " "compositional similarity projections"
)
parser.add_argument(
    "--mainland",
    "-m",
    dest="mainland",
    default=False,
    action="store_true",
    help="Project using mainland coefficients " "(default: islands)",
)
args = parser.parse_args()

if args.mainland:
    ISLMAIN = 1
    mask_file = os.path.join(utils.data_root(), "1km/mainland-from-igor-edited.tif")
else:
    mask_file = os.path.join(utils.data_root(), "1km/islands-from-igor-edited.tif")
    ISLMAIN = 0

# Open the mask raster file (Mainlands)
mask_ds = rasterio.open(mask_file)

# Abunadnce compositional similarity model with updated PriMin-Urb coefficient
mod = modelr.load("/home/vagrant/katia/models/updated_compsim_abund.rds")
pythonify(mod)

# Import standard PREDICTS rasters
rasters = predicts.rasterset("1km", "medium", year=2005)

# create an ISL_MAINL raster
# set it to Mainlands this time round (set Mainlands to 1 and Islands to 0)
rasters["ISL_MAINMAINLAND"] = ISLMAIN
rasters["ISL_MAINISLAND"] = 0

rasters["adjGeogDist"] = 0
rasters["cubeRtEnvDist"] = 0

# set up the rasterset, cropping to mainlands
rs = RasterSet(rasters, mask=mask_ds, maskval=0, crop=True)
# if you're projecting the whole world, use this code instead
# rs = RasterSet(rasters)

# evaluate the model
# model is logit transformed with an adjustment, so back-transformation
rs[mod.output] = mod
intercept = mod.partial({"ISL_MAINMAINLAND": ISLMAIN})
print("intercept: %.5f" % intercept)
if args.mainland:
    assert math.isclose(intercept, 1.939964, rel_tol=0.001)
else:
    assert math.isclose(intercept, 1.439107176, rel_tol=0.001)

rs["output"] = "(inv_logit(%s) - 0.01) / (inv_logit(%f) - 0.01)" % (
    mod.output,
    intercept,
)

fname = "ab-cs-%s.tif" % ("mainland" if args.mainland else "islands")
rs.write("output", utils.outfn("katia", fname))
