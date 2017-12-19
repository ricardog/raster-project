#!/usr/bin/env python3

import matplotlib.pyplot as plt
from netCDF4 import Dataset
import numpy as np
import rasterio

import projections.utils as utils

class YearRangeParamType(click.ParamType):
  name = 'year range'

  def convert(self, value, param, ctx):
    try:
      try:
        return [int(value)]
      except ValueError:
        low, high = value.split(':')
        return range(int(low), int(high))
    except ValueError:
      self.fail('%s is not a valid year range' % value, param, ctx)

YEAR_RANGE = YearRangeParamType()

@click.command()
@click.argument('scenario', type=click.Choice(utils.luh2_scenarios()))
@click.argument('years', type=YEAR_RANGE)
def calculate(scenario, years):
  """Calculate and plot land use over time.

  Also compute what fraction of NPP is taken by humans.

  """

  utils.luh2_check_year(min(years), scenario)
  utils.luh2_check_year(max(years), scenario)
  with Dataset(utils.static) as static:
    carea = static.variables['carea'][:]
    land = 1 - static.variables['icwtr'][:]

  with rasterio.open(utils.outfn('luh2', 'npp.tif')) as npp_ds:
    npp = npp_ds.read(1, masked=True)

  scale = carea * npp
  total = (carea * land).sum()
  crop = np.zeros(len(years))
  past = np.zeros(len(years))
  prim = np.zeros(len(years))
  secd = np.zeros(len(years))
  urbn = np.zeros(len(years))

  with Dataset(utils.state(scenario)) as ds:
    for year in years:
      idx = year - (850 if scenario == 'historical' else 2015)
      crop[idx] = (carea * (ds.variables['c3ann'][idx, :, :] +
                            ds.variables['c4ann'][idx, :, :] +
                            ds.variables['c3nfx'][idx, :, :] +
                            ds.variables['c3per'][idx, :, :]) / total)
      past[idx] = (carea * (ds.variables['range'][idx, :, :] +
                            ds.variables['pastr'][idx, :, :]) / total)
      prim[idx] = (carea * (ds.variables['primf'][idx, :, :] +
                            ds.variables['primn'][idx, :, :]) / total)
      secd[idx] = (carea * (ds.variables['secdf'][idx, :, :] +
                            ds.variables['secdn'][idx, :, :]) / total)
      urbn[idx] = (carea * ds.variables['urban'][idx, :, :] / total)

  fig, ax = plt.subplots()
  ax.stackplot(years, crop, past, prim, secd, urbn)
  plt.show()

if __name__ == '__main__':
#pylint: disable-msg=no-value-for-parameter
  calculate()
#pylint: enable-msg=no-value-for-parameter
