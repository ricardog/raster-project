#!/usr/bin/env python

import time

import fiona
import multiprocessing
from rasterio.plot import show

from projections.rasterset import RasterSet, Raster
from projections.simpleexpr import SimpleExpr
from projections.r2py pythonify
import projections.r2py.modelr as modelr
import projections.utils as utils

def project(year):
  print("projecting %d" % year)
  # Open the mask shape file
  shp_file = 'c:/data/from-adriana/tropicalforests.shp'
  shapes = fiona.open(shp_file)

  # Read Adriana's abundance model (mainland)
  mod = modelr.load('../tropical-bii/simplifiedAbundanceModel.rds')
  pythonify(mod)

  # Import standard PREDICTS rasters
  rasters = predicts.rasterset('1km', '', year, 'medium')
  rasters['primary_lightintense'] = SimpleExpr('primary_lightintense',
                                               'primary_light + primary_intense')
  rasters['cropland_lightintense'] = SimpleExpr('cropland_lightintense',
                                                'cropland_light + cropland_intense')
  rasters['pasture_lightintense'] = SimpleExpr('pasture_lightintense',
                                                'pasture_light + pasture_intense')
  rasters['rd_dist'] = Raster('rd_dist', '/out/1km/roads-adrid.tif')
  rasters['hpd'] = Raster('hpd',
                          '/vsizip//data/from-adriana/HPD01to12.zip/yr%d/hdr.adf' % year)

  rs = RasterSet(rasters, shapes = shapes, crop = True, all_touched = True)

  what = 'LogAbund'
  rs[what] = mod
  stime = time.time()
  rs.write(what, utils.outfn('1km', 'adrid-%d.tif' % year))
  etime = time.time()
  print("executed in %6.2fs" % (etime - stime))

if __name__ == '__main__':
  project(2005)
  #sys.exit()
  #pool = multiprocessing.Pool(processes=4)
  #pool.map(project, range(2001, 2013))
  #map(project, range(2001, 2013))
