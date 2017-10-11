#!/usr/bin/env python

import fiona
import multiprocessing
import os
import time
from rasterio.plot import show, show_hist

from projections.rasterset import RasterSet, Raster
from projections.simpleexpr import SimpleExpr
import projections.predicts as predicts
import projections.modelr as modelr

def project(year):
  print "projecting %d" % year
  # Open the mask shape file
  shp_file = '../../data/from-adriana/tropicalforests.shp'
  shapes = fiona.open(shp_file)

  # Read Adriana's abundance model (mainland)
  mod = modelr.load('../models/ab-corrected3.rds')
  predicts.predictify(mod)

  # Import standard PREDICTS rasters
  rasters = predicts.rasterset('1km', 'version3.3', year, 'medium')
  rasters['primary_lightintense'] = SimpleExpr('primary_lightintense',
                                               'primary_light + primary_intense')
  rasters['cropland_lightintense'] = SimpleExpr('cropland_lightintense',
                                                'cropland_light + cropland_intense')
  rasters['rd_dist'] = Raster('rd_dist', 'ds/1km/roads-adrid.tif')
  rasters['hpd'] = Raster('hpd',
                          '/vsizip//data/from-adriana/HPD01to12.zip/yr%d/hdr.adf' % year)
                          
  rs = RasterSet(rasters, shapes = shapes, crop = True, all_touched = True)
  
  what = 'LogAbund'
  rs[what] = mod
  stime = time.time()
  data = rs.write(what, 'adrid-%d.tif' % year)
  etime = time.time()
  print "executed in %6.2fs" % (etime - stime)

if __name__ == '__main__':
  pool = multiprocessing.Pool(processes=4)
  pool.map(project, range(2001, 2013))
  #map(project, range(2001, 2013))         
  
