#!/usr/bin/env python

import argparse
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

parser = argparse.ArgumentParser(description="bii.py -- BII projections")
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
  suffix = 'mainland'
  ab_max = 1.655183
  sr_max = 1.636021
else:
  assert False
  suffix = 'islands'
  ab_max = None
  sr_max = None

folder = 'clip' if args.clip else 'no-clip'

# pull in all the rasters for computing bii
bii_rs = RasterSet({'abundance': Raster('abundance',
                                        utils.outfn('katia',
                                                    folder,
                                                    'ab-%s.tif' % suffix)),
                    'comp_sim': Raster('comp_sim',
                                       utils.outfn('katia',
                                                   'ab-cs-%s.tif' % suffix)),
                    'clip_ab': SimpleExpr('clip_ab',
                                          'clip(abundance, 0, %f)' % ab_max),
                    'bii_ab': SimpleExpr('bii_ab', 'abundance * comp_sim'),
                    'bii_ab2': SimpleExpr('bii_ab2', 'clip_ab * comp_sim'),
})

# write out bii raster
bii_rs.write('bii_ab' if args.clip else 'bii_ab2',
             utils.outfn('katia', folder,
                         'abundance-based-bii-%s.tif' % suffix))

# do the same for species richness
# pull in all the rasters for computing bii
bii_rs = RasterSet({'sp_rich': Raster('sp_rich',
                                      utils.outfn('katia',
                                                  folder,
                                                  'sr-%s.tif' % suffix)),
                    'comp_sim': Raster('comp_sim',
                                       utils.outfn('katia',
                                                   'sr-cs-%s.tif' % suffix)),
                    'clip_sr': SimpleExpr('clip_sr',
                                          'clip(sp_rich, 0, %f)' % sr_max),
                    'bii_sr': SimpleExpr('bii_sr', 'sp_rich * comp_sim'),
                    'bii_sr2': SimpleExpr('bii_sr2', 'clip_sr * comp_sim')})

# write out bii raster
bii_rs.write('bii_sr' if args.clip else 'bii_sr2',
             utils.outfn('katia', folder,
                         'speciesrichness-based-bii-%s.tif' % suffix))
