#!/usr/bin/env python

import rasterio
from rasterio.plot import show
import numpy as np
import numpy.ma as ma
import sys

import pdb

import projections.utils as utils

import osr
def earth_radius():
  srs = osr.SpatialReference()
  srs.ImportFromEPSG(4326)
  return srs.GetSemiMajor()

def rcs(height, res, left, bottom, right, top):
  lats = np.linspace(top, bottom + res[1], height)
  vec = ((np.sin(np.radians(lats + res[1] / 2.0)) -
          np.sin(np.radians(lats - res[1] / 2.0))) *
         (res[0] * np.pi/180) * earth_radius() ** 2 / 1e6)
  return vec.reshape((vec.shape[0], 1))

def one(name, fname, scale=True, band=1):
  ds = rasterio.open(fname)
  area = rcs(ds.height, ds.res, *ds.bounds)
  data = ds.read(band, masked=True).filled(0)
  data[np.where(np.isnan(data))] = 0
  adj = data * area if scale else data
  print "%-10s: %e" % (name, adj.sum())
  print "%10s: %e" % ('max', data.max())
  if not scale:
    print "%10s: %e" % ('max', (data / area).max())

for year in (2010, 2099):
  scenario = 'ssp3'
  one('%s/%d' % (scenario, year),
      'netcdf:ds/luh2/sps.nc:%s' %scenario,
      False, year - 2009)

for name, fname, scale in (('gluds qd', 'ds/luh2/gluds00ag.tif', True),
                           ('v4 qd', 'ds/luh2/grumps4.tif', True),
#                           ('1950', '/Volumes/Vagrant 155/playground/ds/luh2/historical-hpd-1950.tif', True),
                           ('sps3/2015', 'netcdf:ds/luh2/sps.nc:ssp3', False),
                           ('v4', utils.grumps4(), True),
                           ('gluds', utils.grumps1(), True),):
  one(name, fname, scale)

#                           ('sps1', '/data/sps/SSP1_NetCDF/total/NetCDF/ssp1_2010.nc', False),
#                           ('sps2', '/data/sps/SSP2_NetCDF/total/NetCDF/ssp2_2010.nc', False),
#                           ('sps3', '/data/sps/SSP3_NetCDF/total/NetCDF/ssp3_2010.nc', False),
#                           ('sps4', '/data/sps/SSP4_NetCDF/total/NetCDF/ssp4_2010.nc', False),
#                           ('sps5', '/data/sps/SSP5_NetCDF/total/NetCDF/ssp5_2010.nc', False),
  
