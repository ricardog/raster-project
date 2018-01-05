#!/usr/bin/env python3

import math

import click
import joblib
import matplotlib.pyplot as plt
from multiprocessing import Pool as ThreadPool
from netCDF4 import Dataset
import numpy as np
import rasterio

import projections.utils as utils

import pdb

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
@click.argument('scenario', type=click.Choice(utils.luh2_scenarios() + ('all',)))
@click.argument('years', type=YEAR_RANGE)
def calculate(scenario, years):
  """Calculate and plot land use over time.

  Also compute what fraction of NPP is taken by humans.

  """

  if scenario != 'all':
    utils.luh2_check_year(min(years), scenario)
    utils.luh2_check_year(max(years), scenario)
    
  with Dataset(utils.luh2_static()) as static:
    carea = static.variables['carea'][:]
    land = 1 - static.variables['icwtr'][:]

  with rasterio.open(utils.outfn('luh2', 'npp.tif')) as npp_ds:
    npp = npp_ds.read(1, masked=True)

  npp_total = (carea * npp).sum()
  total = (carea * land).sum()

  if scenario != 'all':
    scenarios = (scenario, )
    fig, axes = plt.subplots()
    all_axes = [axes]
  else:
    scenarios = ('historical', ) + tuple(filter(lambda s : s != 'historical',
                                                utils.luh2_scenarios()))
    print(scenarios)
    fig, axes = plt.subplots(math.ceil(len(scenarios) / 3.0),
                             min(len(scenarios), 3))
    all_axes = [ax for sublist in axes for ax in sublist]

  storage = {}
  for scene in scenarios:
    with Dataset(utils.luh2_states(scene)) as ds:
      base_year = (850 if scene == 'historical' else 2015)
      years = ds.variables['time'][:] + base_year
      crop = np.zeros(len(years))
      past = np.zeros(len(years))
      prim = np.zeros(len(years))
      secd = np.zeros(len(years))
      urbn = np.zeros(len(years))
      human = np.zeros(len(years))

      for year in years:
        idx = int(year) - base_year
        click.echo('year: %d' % int(year))
        cr = (ds.variables['c3ann'][idx, :, :] + ds.variables['c4ann'][idx, :, :] +
              ds.variables['c3per'][idx, :, :] + ds.variables['c4per'][idx, :, :] +
              ds.variables['c3nfx'][idx, :, :])
        pa = (ds.variables['range'][idx, :, :] + ds.variables['pastr'][idx, :, :])
        pr = (ds.variables['primf'][idx, :, :] + ds.variables['primn'][idx, :, :])
        se = (ds.variables['secdf'][idx, :, :] + ds.variables['secdn'][idx, :, :])
        ur = ds.variables['urban'][idx, :, :]

        crop[idx] = (carea * cr).sum() / total * 100
        past[idx] = (carea * pa).sum() / total * 100
        prim[idx] = (carea * pr).sum() / total * 100
        secd[idx] = (carea * se).sum() / total * 100
        urbn[idx] = (carea * ur).sum() / total * 100

        human[idx] = (carea * (cr + pa + ur) * npp).sum() / npp_total * 100

    ax = all_axes.pop(0)
    ax.stackplot(years, (crop, past, prim, secd, urbn),
                 labels=['Cropland', 'Pasture', 'Primary', 'Secondary', 'Urban'])
    ax.plot(years, human, 'k-', linewidth=3, label='Human NPP')
    ax.set_ylabel('Fraction of land surface (%)')
    ax.set_xlabel('Year')
    ax.set_title(scene)
    ax.grid('on')
    ax.legend(loc='center left')
    storage[scene] = np.vstack((years, crop, past, prim, secd, urbn, human))
  plt.show()
  joblib.dump(storage, 'overtime.dat', compress=True)

if __name__ == '__main__':
#pylint: disable-msg=no-value-for-parameter
  calculate()
#pylint: enable-msg=no-value-for-parameter
