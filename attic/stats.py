#!/usr/bin/env python

import rasterio

import click
import itertools
import matplotlib.colors as colors
import matplotlib.pyplot as plt
import numpy as np
import numpy.ma as ma
import os
import pandas as pd
from pylru import lrudecorator
from rasterio.plot import show
import re

import pdb

import projections.utils as utils

@lrudecorator(5)
def carea(bounds=None, height=None):
  ds = rasterio.open('netcdf:%s:carea' %
                     os.path.join(utils.luh2_dir(),
                                  'staticData_quarterdeg.nc'))
  if bounds is None:
    return ds.read(1, masked=True)
  win = ds.window(*bounds)
  if win[1][1] - win[0][1] > height:
    win = ((win[0][0], win[0][0] + height), win[1])
  return ds.read(1, masked=True, window=win)

def rcs(height, res, left, bottom, right, top):
  er = 6378137.0
  lats = np.linspace(top, bottom + res[1], height)
  vec = ((np.sin(np.radians(lats + res[1] / 2.0)) -
          np.sin(np.radians(lats - res[1] / 2.0))) *
         (res[0] * np.pi/180) * er ** 2 / 1e6)
  return vec.reshape((vec.shape[0], 1))

def mean(data):
  return data.mean()

def median(data):
  return ma.median(data)

def total(data):
  return data.sum()

def get_domain(files):
  whats = []
  years = []
  for arg in files:
    scenario, what, year = os.path.splitext(arg)[0].split('-')
    whats.append(what)
    years.append(int(year))
  return list(set(whats)), list(set(years))
  
@click.command()
@click.argument('op', type=click.Choice(['sum', 'mean', 'median']))
@click.argument('infiles', nargs=-1, type=click.Path(dir_okay=False))
@click.option('-b', '--band', type=click.INT, default=1,
              help='Index of band to process (default: 1)')
@click.option('-l', '--log', is_flag=True, default=False,
              help='When set the data is in log scale and must be ' +
              'converted to linear scale (default: False)')
@click.option('-w', '--area-weighted', is_flag=True, default=False,
              help='Compute the area-weighted value ' +
              '(default: False)')
def stats(op, infiles, band, log, area_weighted):
  whats, years = get_domain(infiles)
  df = pd.DataFrame(columns=whats, index=sorted(years))
  for arg in infiles:
    with rasterio.open(arg) as src:
      data = src.read(band, masked=True)
      if log:
        data = ma.exp(data)
      if area_weighted:
        data *= rcs(data.shape[0], src.res, *src.bounds)
      data.mask = np.logical_or(data.mask, ma.where(np.isnan(data),
                                                    True, False))
      if op == 'sum':
        op = 'total'
      res = eval("%s(data)" % op)
      if re.search(r'-hpd-(\d){4}.tif', arg):
        print('%s: %8.4f %8.4f' % (os.path.basename(arg), res, np.log(res+1) / 10.02083))
      else:
        print('%s: %8.4f' % (os.path.basename(arg), res))
      scenario, what, year = os.path.splitext(arg)[0].split('-')
      df.ix[int(year), what] = res

  print(df)
  df.plot.bar()
  plt.savefig('lu-comp.png')
  plt.show()

  
if __name__ == '__main__':
  stats()
