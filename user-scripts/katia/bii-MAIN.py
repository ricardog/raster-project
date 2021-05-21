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

from rasterset import RasterSet, Raster, SimpleExpr

import projections.predicts as predicts
import projections.r2py.modelr as modelr
import projections.utils as utils
import projections.raster_utils as ru

CLIP = 'no-clip'

# pull in all the rasters for computing bii
bii_rs = RasterSet({'abundance': Raster('abundance',
                                        utils.outfn('katia',
                                                    CLIP,
                                                    'bii-ab-mainlands.tif')),
                    'comp_sim': Raster('comp_sim',
                                       utils.outfn('katia',
                                                   'bii-ab-cs-mainlands.tif')),
                    'clip_ab': SimpleExpr('clip_ab',
                                          'clip(abundance, 0, 1.655183)'),
                    'bii_ab': SimpleExpr('bii_ab', 'abundance * comp_sim'),
                    'bii_ab2': SimpleExpr('bii_ab2', 'clip_ab * comp_sim'),
})

# write out bii raster
bii_rs.write('bii_ab' if CLIP == 'clip' else 'bii_ab2',
             utils.outfn('katia', CLIP, 'abundance-based-bii-mainlands.tif'))

# do the same for species richness
# pull in all the rasters for computing bii
bii_rs = RasterSet({'sp_rich': Raster('sp_rich',
                                      utils.outfn('katia',
                                                  CLIP,
                                                  'bii-sr-mainlands.tif')),
                    'comp_sim': Raster('comp_sim',
                                       utils.outfn('katia',
                                                   'bii-sr-cs-mainlands.tif')),
                    'clip_sr': SimpleExpr('clip_sr',
                                          'clip(sp_rich, 0, 1.636021)'),
                    'bii_sr': SimpleExpr('bii_sr', 'sp_rich * comp_sim'),
                    'bii_sr2': SimpleExpr('bii_sr2', 'clip_sr * comp_sim')})

# write out bii raster
bii_rs.write('bii_sr' if CLIP == 'clip' else 'bii_sr2',
             utils.outfn('katia', CLIP,
                         'speciesrichness-based-bii-mainlands.tif'))
