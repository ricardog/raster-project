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
import pandas

from projections.rasterset import RasterSet, Raster
from projections.simpleexpr import SimpleExpr
import projections.predicts as predicts
import projections.r2py.modelr as modelr
import projections.utils as utils
import projections.raster_utils as ru

# pull out the bounding values for these model
df = pandas.read_csv('C:/data/from-adriana/ValuesForProjections/maxPreds.csv')

fldr = ['v1', 'v2', 'v3']

# for each model version
for version in fldr:

  # get the maximum prediction
  abmax = float(df[df['Version'] == int(version[1])]['Abundance'])
  csmax = float(df[df['Version'] == int(version[1])]['CompSim'])
  
  for year in range(2001, 2013):

    print("Working on year:" + str(year))
    # clip the abundance rasters so they can't go below 0 but no upper limit
    inname = 'C:/ds/temporal-bii/' + version + '/bii-ab-' + str(year) + '.tif'
    outname = 'C:/ds/temporal-bii/'  + version + '/bii-ab-low-bound-' + str(year) + '.tif'
    ru.clip(inname, outname, 0, None)

    # clip the cs rasters so they can't go below 0 but no upper limit
    inname = 'C:/ds/temporal-bii/' + version + '/bii-cs-' + str(year) + '.tif'
    outname = 'C:/ds/temporal-bii/' + version + '/bii-cs-low-bound-' + str(year) + '.tif'
    ru.clip(inname, outname, 0, None)

    # calculate bii (with only a lower bound)
    # pull in all the rasters for computing bii
    bii_rs = RasterSet({'abundance': Raster('abundance', 'C:/ds/temporal-bii/' + version + '/bii-ab-low-bound-%d.tif' % year),
                        'comp_sim': Raster('comp_sim', 'C:/ds/temporal-bii/' + version + '/bii-cs-low-bound-%d.tif' % year),
                        'bii_ab': SimpleExpr('bii_ab', 'abundance * comp_sim')})

    # write out bii raster
    bii_rs.write('bii_ab', utils.outfn('temporal-bii/' + version, 'bii-%d.tif' % year))

    # calculate bounded bii
    # clip the abundance rasters
    inname = 'C:/ds/temporal-bii/' + version + '/bii-ab-' + str(year) + '.tif'
    outname = 'C:/ds/temporal-bii/'  + version + '/bii-ab-bound-' + str(year) + '.tif'
    ru.clip(inname, outname, 0, abmax)

    # clip the cs rasters
    inname = 'C:/ds/temporal-bii/' + version + '/bii-cs-' + str(year) + '.tif'
    outname = 'C:/ds/temporal-bii/' + version + '/bii-cs-bound-' + str(year) + '.tif'
    ru.clip(inname, outname, 0, csmax)
    
    # pull in all the rasters for computing (bounded) bii
    bii_rs = RasterSet({'abundance': Raster('abundance', 'C:/ds/temporal-bii/' + version + '/bii-ab-bound-%d.tif' % year),
                        'comp_sim': Raster('comp_sim', 'C:/ds/temporal-bii/' + version + '/bii-cs-bound-%d.tif' % year),
                        'bii_ab': SimpleExpr('bii_ab', 'abundance * comp_sim')})

    # write out bii raster
    bii_rs.write('bii_ab', utils.outfn('temporal-bii/' + version,'bii-bounded-%d.tif' % year))
