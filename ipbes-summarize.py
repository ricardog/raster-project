#!/usr/bin/env python

import click
import fiona
import numpy as np
import numpy.ma as ma
import pandas as pd
import rasterio
from rasterio.plot import show

import pdb

import projections.utils as utils

class YearRangeParamType(click.ParamType):
  name = 'year range'

  def convert(self, value, param, ctx):
    try:
      try:
        return [int(value)]
      except ValueError:
        l, h = value.split(':')
        return range(int(l), int(h))
    except ValueError:
      self.fail('%s is not a valid year range' % value, param, ctx)

YEAR_RANGE = YearRangeParamType()

def read_bounded(ds, bounds=None, height=None):
  if bounds is None:
    return ds.read(1, masked=True)
  win = ds.window(*bounds)
  if height and win[0][1] - win[0][0] > height:
    win = ((win[0][0], win[0][0] + height), win[1])
  return ds.read(1, masked=True, window=win)

def carea(bounds=None, height=None):
  with rasterio.open(utils.luh2_static('carea')) as ds:
    read_bounded(ds, bounds, height)

def tarea(bounds=None, height=None):
  with rasterio.open(utils.luh2_static('icwtr')) as ds:
    ice = read_bounded(ds, bounds, height)
  return (1 - ice) * carea(bounds, height)

def weighted_mean_by(regions, data):
  data.mask = np.logical_or(data.mask, regions.mask)
  regions.mask = ma.getmask(data)
  regions_idx = regions.compressed().astype(int)
  sums = np.bincount(regions_idx, data.compressed())
  ncells = np.bincount(regions_idx)
  idx = np.where(ncells > 0)
  carea = ncells[idx]
  as_array = np.column_stack((idx[0].astype(int), carea, sums[idx] / carea))
  return pd.DataFrame(as_array, columns=['ID', 'Cells', 'Mean'])

def find_bounds(sources):
  bounds = [-180, -90, 180, 90]
  width = 0
  height = 0
  for src in sources:
    if rasterio.coords.disjoint_bounds(bounds, src.bounds):
      raise ValueError("rasters do not intersect")
    bounds[0] = max(bounds[0], src.bounds[0])
    bounds[1] = max(bounds[1], src.bounds[1])
    bounds[2] = min(bounds[2], src.bounds[2])
    bounds[3] = min(bounds[3], src.bounds[3])
    width = max(width, src.width)
    height = max(height, src.height)
  for src in sources:
    win = src.window(*bounds)
    width = min(width, win[1][1] - win[1][0])
    height = min(height, win[0][1] - win[0][0])
  return bounds, width, height

def get_ipbes_regions():
  with fiona.open(utils.outfn('vector', 'ipbes_land_shape',
                              'ipbes_land.shp')) as shapes:
    props = tuple(filter(lambda x: x.get('type') == 'Land',
                         (s['properties'] for s in shapes)))
    return pd.DataFrame({'ID': tuple(int(s.get('OBJECTID')) for s in props),
                         'Name': tuple(s.get('IPBES_sub') for s in props)})

@click.group(invoke_without_command=True)
@click.pass_context
def cli(ctx):
  if ctx.invoked_subcommand is None:
    click.echo('I was invoked without subcommand')
    summarize()
  else:
    click.echo('I am about to invoke %s' % ctx.invoked_subcommand)

@cli.command()
@click.argument('what', type=click.Choice(['ab', 'sr']))
@click.argument('scenario', type=click.Choice(utils.luh2_scenarios()))
@click.argument('years', type=YEAR_RANGE)
@click.option('--npp', type=click.Path(dir_okay=False))
def summary(what, scenario, years, npp):
  df = get_ipbes_regions()
  template = '%s-%s-%%4d.tif' % (scenario, 'BIIAb'
                                 if what == 'ab' else 'BIISR')

  for year in years:

    fnames = [utils.outfn('luh2', template % year)]
    fnames.append(utils.luh2_static('carea'))
    if npp:
      fnames.append(npp)
    fnames.append(utils.outfn('luh2', 'ipbes-subs.tif'))

    sources = [rasterio.open(src) for src in fnames]
    bounds, width, height = find_bounds(sources)
    data = [read_bounded(src, bounds, height) for src in sources]
    bii = ma.prod(data[0:-1], 0)
    bii.mask = np.any(tuple(d.mask for d in data[0:-1]), 0)

    intact = ma.prod([np.full(data[0].shape, 1), data[1]], 0)
    intact.mask = bii.mask

    by_subs = weighted_mean_by(data[-1], bii)
    intact_by_subs = weighted_mean_by(data[-1], intact)
    if 'Cells' not in df.columns:
      df['Cells'] = by_subs.Cells
    df[year] = by_subs.Mean / intact_by_subs.Mean
  if len(years) < 10:
    print(df)
  df.to_csv('%s-%s-%4d-%4d.csv' % (scenario,
                                   'BIIAb' if what == 'ab' else 'BIISR',
                                   years[0], years[-1]))

@cli.command()
@click.argument('what', type=click.Choice(['ab', 'sr']))
@click.argument('scenario', type=click.Choice(utils.luh2_scenarios()))
@click.argument('years', type=YEAR_RANGE)
@click.option('--npp', type=click.Path(dir_okay=False))
def summarize(what, scenario, years, npp):
  df = get_ipbes_regions()

  for year in years:
    template = '%s-%%s-%4d.tif' % (scenario, year)
    vnames = ('Abundance', 'CompSimAb') if what == 'ab' else ('Richness',
                                                              'CompSimSR')
    fnames = [utils.outfn('luh2', template % vname)
              for vname in vnames]
    fnames.append(utils.luh2_static('carea'))
    if npp:
      fnames.append(npp)
    fnames.append(utils.outfn('luh2', 'ipbes-subs.tif'))

    sources = [rasterio.open(src) for src in fnames]
    bounds = find_bounds(sources)
    data = [read_bounded(src, bounds) for src in sources]
    bii = ma.prod(data[0:-1], 0)
    bii.mask = np.any(tuple(d.mask for d in data[0:-1]), 0)

    intact = ma.prod([np.full(data[0].shape, 1), data[2:-1]], 0)
    intact.mask = bii.mask

    by_subs = weighted_mean_by(data[-1], bii)
    intact_by_subs = weighted_mean_by(data[-1], intact)
    df[year] = by_subs.Mean / intact_by_subs.Mean
  print(df)

if __name__ == '__main__':
#pylint: disable-msg=no-value-for-parameter
  cli()
#pylint: enable-msg=no-value-for-parameter
