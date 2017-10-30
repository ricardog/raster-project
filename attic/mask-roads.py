#!/usr/bin/env python

import click
import numpy as np
import os
import pdb
import rasterio
import sys

import projections.utils as utils

def window_inset(win1, win2):
  if win2:
    return ((win1[0][0] + win2[0][0], min(win1[0][1] + win2[0][0], win2[0][1])),
            (win1[1][0] + win2[1][0], min(win1[1][1] + win2[1][0], win2[1][1])))
  return win1

@click.command()
@click.option('--band', default=1, help='Band of raster to mask')
@click.argument('raster', type=click.Path())
@click.argument('mask', type=click.Path())
def maskit(raster, mask, band=1):
  rds = rasterio.open(raster, 'r+')
  ice = rasterio.open(mask)
  minxs, minys, maxxs, maxys = zip(rds.bounds, ice.bounds)
  bounds = (max(minxs), max(minys), min(maxxs), min(maxys))
  ice_view = ice.window(*bounds)
  nodata = rds.nodatavals[band - 1]
  
  for ij, win in rds.block_windows():
    if rds.height > 10000 and win[0][1] % 100 == 0:
      print(win)
    rr = rds.read(band, masked=True, window=win)
    ii = ice.read(1, masked=True, window=window_inset(win, ice_view))
    rr.mask = np.logical_or(rr.mask,
                            np.where(ii == 1.0, True, False))
    rds.write(rr.filled(nodata), window=win, indexes=band)


if __name__ == '__main__':
  raster = 'ds/1km/roads.tif'  
  mask = 'zip:%s/1km/ICE.zip!ICE_1km_2005.bil' % utils.data_root()
  maskit()
