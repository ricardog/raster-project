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
import projections.raster_utils as ru


# pull in all the rasters for computing bii
bii_rs = RasterSet({'abundance': Raster('abundance',
                                        utils.outfn('katia',
                                                    'bii-ab-mainlands.tif')),
                    'comp_sim': Raster('comp_sim',
                                       utils.outfn('katia',
                                                   'bii-ab-cs-mainlands.tif')),
                    'bii_ab': SimpleExpr('bii_ab', 'abundance * comp_sim')})

# write out bii raster
bii_rs.write('bii_ab',
             utils.outfn('katia', 'abundance-based-bii-mainlands.tif'))

# do the same for species richness
# pull in all the rasters for computing bii
bii_rs = RasterSet({'sp_rich': Raster('sp_rich',
                                      utils.outfn('katia',
                                                  'bii-sr-mainlands.tif')),
                    'comp_sim': Raster('comp_sim',
                                       utils.outfn('katia',
                                                   'bii-sr-cs-mainlands.tif')),
                    'bii_sr': SimpleExpr('bii_sr', 'sp_rich * comp_sim')})

# write out bii raster
bii_rs.write('bii_sr',
             utils.outfn('katia', 'speciesrichness-based-bii-mainlands.tif'))
