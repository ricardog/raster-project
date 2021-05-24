#!/usr/bin/env python

import os
import rasterio

from projections import predicts, utils
from r2py import modelr, pythonify
from rasterset import RasterSet, Raster, SimpleExpr

RD_DIST_MIN = 0
RD_DIST_MAX = 195274.3
HPD_MIN = 0
HPD_MAX = 22490

CLIP = True  # False

# Open the mask raster file (Mainlands)
mask_file = os.path.join(utils.data_root(), "1km/mainland-from-igor-edited.tif")
mask_ds = rasterio.open(mask_file)

# Read Katia's richness model
mod = modelr.load("/home/vagrant/katia/models/best_model_rich.rds")
pythonify(mod)

# Import standard PREDICTS rasters
rasters = predicts.rasterset("1km", "medium", year=2005)

# create an ISL_MAINL raster
# set it to Mainlands this time round (set Mainlands to 1 and Islands to 0)
rasters["ISL_MAINLMAINLAND"] = SimpleExpr("ISL_MAINLMAINLAND", "2")
rasters["ISL_MAINLISLAND"] = SimpleExpr("ISL_MAINLISLAND", "0")

# specify the plantation forest maps as 0
# not sure why it's plantations_pri rather than plantation, but hey ho
rasters["plantation_pri"] = SimpleExpr("plantation_pri", "0")
rasters["plantation_pri_minimal"] = SimpleExpr("plantation_pri_minimal", "0")
rasters["plantation_pri_light"] = SimpleExpr("plantation_pri_light", "0")
rasters["plantation_pri_intense"] = SimpleExpr("plantation_pri_intense", "0")

# If CLIP is true, limit the predictor variable values to the max seen
# when fitting the model
if CLIP:
    rasters["clip_hpd"] = SimpleExpr(
        "clip_hpd", "clip(hpd_ref, %f, %f)" % (HPD_MIN, HPD_MAX)
    )
else:
    rasters["clip_hpd"] = SimpleExpr("clip_hpd", "hpd_ref")
# ## Log values and then rescale them 0 to 1
# we need to check whether the logHPD.rs automatically produced uses the
# same values we use if not, manually create logHPD.rs
rasters["logHPD_rs"] = SimpleExpr(
    "logHPD_rs", "scale(log(clip_hpd + 1), 0.0, 1.0, 0.0, 10.02087)"
)

# Same is true for logDistRd_rs
rasters["DistRd"] = Raster(
    "DistRd", os.path.join(utils.data_root(), "1km/rddistwgs.tif")
)  # ## Use new raster
# If CLIP is true, limit the predictor variable values to the max seen
# when fitting the model
if CLIP:
    rasters["clipDistRd"] = SimpleExpr(
        "clipDistRd", "clip(DistRd, %f, %f)" % (RD_DIST_MIN, RD_DIST_MAX)
    )
else:
    rasters["clipDistRd"] = SimpleExpr("clipDistRd", "DistRd")
rasters["logDistRd_rs"] = SimpleExpr(
    "logDistRd_rs", "scale(log(clipDistRd + 100)," "0.0, 1.0, -1.120966, 12.18216)"
)
# ## Added +100 to DistRd to deal with  zero values in raster


# set up the rasterset, cropping to mainlands
rs = RasterSet(rasters, mask=mask_ds, maskval=0, crop=True)
# if you're projecting the whole world, use this code instead
# rs = RasterSet(rasters)

# evaluate the model
# model is square root abundance so square it

# note that the intercept value has been calculated for the baseline
# land use when all other variables are held at 0.
# Therefore I calculated separatedly an intercept where DistRd is set to
# the max value=1

rs[mod.output] = mod
# rs['output'] = SimpleExpr('output', 'exp(%s) / exp(%f)' % (mod.output, mod.intercept))

rs["output"] = SimpleExpr("output", "exp(%s) / exp(%f)" % (mod.output, 2.626708))

# Note that for mainlands, the model intercept is NOT what you want to
# have as your baseline so change mod.itercept to whatever the value is
# of the true intercept
path = ("katia", "clip" if CLIP else "no-clip", "bii-sr-mainlands.tif")
rs.write("output", utils.outfn(*path))
