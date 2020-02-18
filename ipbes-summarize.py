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
  if height and round(win.height) > height:
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
    width = min(width, round(win.width))
    height = min(height, round(win.height))
  return bounds, width, height

def get_ipbes_regions(subregions=True):
  with fiona.open(utils.outfn('vector', 'ipbes_land_shape',
                              'ipbes_land.shp')) as shapes:
    props = tuple(filter(lambda x: x.get('type') == 'Land',
                         (s['properties'] for s in shapes)))
    df = pd.DataFrame({'ID': tuple(int(s.get('OBJECTID')) for s in props),
                       'Name': tuple(s.get('IPBES_sub') for s in props),
                       'Region': tuple(s.get('IPBES_regi') for s in props)})
    if not subregions:
      df['ID'] = df.Region.astype('category').cat.codes
      df = df[['ID', 'Region']].drop_duplicates()
      df.columns = ['ID', 'Name']
      df.index = df.ID.values
      df = df.drop('ID', axis=1).drop(4, axis=0)
    return df

@click.group(invoke_without_command=True)
@click.pass_context
def cli(ctx):
  if ctx.invoked_subcommand is None:
    click.echo('I was invoked without subcommand')
    summarize()

@cli.command()
@click.argument('what', type=click.Choice(['ab', 'sr',
                                           'cs-ab', 'cs-sr',
                                           'bii-ab', 'bii-sr']))
@click.argument('scenario', type=click.Choice(utils.luh2_scenarios()))
@click.argument('years', type=YEAR_RANGE)
@click.option('--npp', type=click.Path(dir_okay=False))
@click.option('--vsr', type=click.Path(dir_okay=False))
@click.option('--regions', is_flag=True, default=False)
def summary(what, scenario, years, npp, vsr, regions):
  """Generate a per-year and per-IPBES region summary of a diversity metric.

  Diversity metric supported are

  - ab: abundance (Abundance)

  - sr: species richness (Richness)

  - cs-ab: abundance-based compositional similarity (CompSimAb)

  - cs-sr: species richness-based compositional similarity (CompSimSR)

  - bii-ab: abundance-based BII (BIIAb)

  - bii-sr: species richness-based BII (BIISR)

"""
  if npp and vsr:
    raise RuntimeError('Please specify --npp or --vsr, not both')

  df = get_ipbes_regions(not regions)
  df_global = pd.DataFrame({'ID': [-1], 'Name': ['Global']},
                           columns=('ID', 'Name'))
  vname =  'Abundance' if what == 'ab' \
           else 'Richness' if what =='sr' \
                else 'CompSimAb' if what == 'cs-ab' \
                     else 'CompSimSR' if what == 'cs-sr' \
                          else 'BIIAb' if what == 'bii-ab' \
                               else 'BIISR'
  template = '%s-%s-%%04d.tif' % (scenario, vname)

  if scenario == 'historical':
    # This is horrible kludge!
    years = (900, 1000, 1100, 1200, 1300, 1400, 1500, 1600,
             1700, 1710, 1720, 1730, 1740, 1750, 1760, 1770, 1780, 1790,
             1800, 1810, 1820, 1830, 1840, 1850, 1860, 1870, 1880, 1890,
             1900, 1910, 1920, 1930, 1940, 1950, 1960, 1970, 1980, 1990,
             2000, 2001, 2002, 2003, 2004, 2005, 2006, 2007, 2008, 2009,
             2010, 2011, 2012, 2013, 2014)
    
  for year in years:
    fnames = [utils.outfn('luh2', template % year)]
    fnames.append(utils.luh2_static('carea'))
    if npp:
      fnames.append(npp)
    if vsr:
      fnames.append(vsr)
    if regions:
      fnames.append(utils.outfn('luh2', 'ipbes-region.tif'))
    else:
      fnames.append(utils.outfn('luh2', 'ipbes-subs.tif'))

    sources = [rasterio.open(src) for src in fnames]
    bounds, width, height = find_bounds(sources)
    data = [read_bounded(src, bounds, height) for src in sources]
    bii = ma.prod(data[0:-1], 0)
    bii.mask = np.any(tuple(d.mask for d in data[0:-1]), 0)

    intact = ma.prod([np.full(data[0].shape, 1), data[1]], 0)
    if (npp or vsr):
      intact *= data[-2]
    intact.mask = bii.mask

    by_subs = weighted_mean_by(data[-1], bii)
    intact_by_subs = weighted_mean_by(data[-1], intact)
    if 'Cells' not in df.columns:
      df['Cells'] = by_subs.Cells
    df[year] = by_subs.Mean / intact_by_subs.Mean

    if 'Cells' not in df_global.columns:
      df_global['Cells'] = (bii.shape[0] * bii.shape[1] -
                            ma.count_masked(bii))
    df_global[year] = ma.average(bii) / ma.average(intact)

  if len(years) < 10:
    print(df)
  weight = "-npp" if npp else "-vsr" if vsr else ""
  area = 'reg' if regions else 'subreg'
  df.to_csv('%s-%s%s-%s-%04d-%04d.csv' % (scenario, vname, weight,
                                          area,
                                          years[0], years[-1]),
            index=False)
  df_global.to_csv('%s-%s%s-global-%04d-%04d.csv' % (scenario, vname, weight,
                                                     years[0], years[-1]),
                   index=False)
@cli.command()
@click.argument('what', type=click.Choice(['ab', 'sr']))
@click.argument('scenario', type=click.Choice(utils.luh2_scenarios()))
@click.argument('years', type=YEAR_RANGE)
@click.option('--npp', type=click.Path(dir_okay=False))
def summarize(what, scenario, years, npp):
  df = get_ipbes_regions()

  for year in years:
    template = '%s-%%s-%04d.tif' % (scenario, year)
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
