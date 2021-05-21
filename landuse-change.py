#!/usr/bin/env python

# From
## https://stackoverflow.com/questions/22787209/how-to-have-clusters-of-stacked-bars-with-python-pandas

import click
import itertools
import json
import matplotlib.cm as cm
import matplotlib.pyplot as plt
import multiprocessing
import numpy as np
import numpy.ma as ma
import os
import pandas as pd
from pylru import lrudecorator
import rasterio
import rasterio.windows
import time

import pdb

import projections.lu as lu
import projections.lui as lui
import projections.utils as utils
import projections.predicts as predicts
from rasterset import RasterSet

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

@lrudecorator(10)
def carea(bounds=None, height=None):
  ice_ds = rasterio.open('netcdf:%s:icwtr' % utils.luh2_static())
  print('reading area')
  
  ds = rasterio.open('netcdf:%s:carea' % utils.luh2_static())
  if bounds is None:
    ice = ice_ds.read(1)
    mask = np.where(ice == 1, True, False)
    ca = ds.read(1, masked=True)
    ca.mask = np.logical_or(ca.mask, mask)
    return ca
  win = ds.window(*bounds)
  if height is not None and win[1][1] - win[0][1] > height:
    win = ((win[0][0], win[0][0] + height), win[1])
  ice = ice_ds.read(1, window=win)
  mask = np.where(ice == 1, True, False)
  ca = ds.read(1, masked=True, window=win)
  ca.mask = np.logical_or(ca.mask, mask)
  return ca

@lrudecorator(5)
def carea2(bounds=None, height=None):
  ds = rasterio.open('netcdf:%s:carea' %
                     os.path.join(utils.luh2_dir(),
                                  'staticData_quarterdeg.nc'))
  if bounds is None:
    return ds.read(1, masked=True)
  win = ds.window(*bounds)
  if win[1][1] - win[0][1] > height:
    win = ((win[0][0], win[0][0] + height), win[1])
  return ds.read(1, masked=True, window=win)

@lrudecorator(5)
def tarea(bounds=None, height=None):
  area = carea2(bounds, height)
  ice_ds = rasterio.open(utils.luh2_static('icwtr'))
  if bounds is None:
    ice = ice_ds.read(1, masked=True)
  else:
    win = ice_ds.window(*bounds)
    if win[1][1] - win[0][1] > height:
      win = ((win[0][0], win[0][0] + height), win[1])
    ice = ice_ds.read(1, masked=True, window=win)
  return area * (1 - ice)

def plot_clustered_stacked(dfall, labels=None,
                           title="multiple stacked bar plot",
                           H="/", **kwargs):
  """Given a list of dataframes, with identical columns and index, create
a clustered stacked bar plot.  labels is a list of the names of the
dataframe, used for the legend title is a string for the title of the
plot H is the hatch used for identification of the different dataframe

  """

  n_df = len(dfall)
  n_col = len(dfall[0].columns)
  n_ind = len(dfall[0].index)
  #axe = plt.subplot(111)
  fig = plt.figure(figsize=(7, 4))
  axe = fig.add_axes([0.1, 0.1, 0.7, 0.75])

  for df in dfall : # for each data frame
    axe = df.plot(kind="bar",
                  linewidth=0,
                  stacked=True,
                  ax=axe,
                  cmap=plt.cm.viridis,
                  legend=False,
                  grid=False,
                  **kwargs)  # make bar plots

  h,l = axe.get_legend_handles_labels() # get the handles we want to modify
  for i in range(0, n_df * n_col, n_col): # len(h) = n_col * n_df
    for j, pa in enumerate(h[i:i+n_col]):
      for rect in pa.patches: # for each index
        rect.set_x(rect.get_x() + 1 / float(n_df + 1) * i / float(n_col))
        rect.set_hatch(H * int(i / n_col)) #edited part
        rect.set_width(1 / float(n_df + 1))

  axe.set_xticks((np.arange(0, 2 * n_ind, 2) + 1 / float(n_df + 1)) / 2.)
  axe.set_xticklabels(df.index, rotation = 0)
  axe.set_title(title)

  # Add invisible data to add another legend
  n=[]
  for i in range(n_df):
    n.append(axe.bar(0, 0, color="gray", hatch=H * i))

  l1 = axe.legend(h[:n_col], l[:n_col], loc=[1.01, 0.5])
  if labels is not None:
    l2 = plt.legend(n, labels, loc=[1.01, 0.1])
  axe.add_artist(l1)
  return axe

def read_data(dirname, lu_name, scenario, year):
  if lu_name == 'rcp':
    types = lu.rcp.types()
  elif lu_name == 'luh2':
    types = lu.luh2.types()
  elif lu_name == 'luh5':
    types = lu.luh5.types()
  else:
    raise RuntimeError('Error: unknown land use class %s' % lu)

  print("reading %s %d" % (scenario, year))
  types = filter(lambda x: x != 'plantation_sec', types)
  rasters = []
  for name in types:
    if name == 'plantation_sec':
      continue
    for intensity in lui.intensities():
      path = os.path.join(dirname, lu_name,
                          '%s-%s_%s-%d.tif' % (scenario, name,
                                               intensity, year))
      ras = rasterio.open(path)
      rasters.append(ras)

  all_bounds = map(lambda x: x.bounds, rasters)
  minxs, minys, maxxs, maxys = zip(*all_bounds)
  bounds = (max(minxs), max(minys), min(maxxs), min(maxys))
  areas = carea(bounds)
  total = ma.sum(areas)
  areas /= total / 100

  df = pd.DataFrame(index=types, columns=lui.intensities().reverse())
  for name in types:
    for intensity in lui.intensities():
      raster = rasters.pop(0)
      data = raster.read(1, masked=True, window=raster.window(*bounds))
      df.loc[name, intensity] = ma.sum(data * areas)
  if 'plantation_pri' in types:
    df.rename(index={'plantation_pri': 'plantation'}, inplace=True)
  return df

@click.group(invoke_without_command=True)
@click.pass_context
def cli(ctx):
    if ctx.invoked_subcommand is None:
        click.echo('I was invoked without subcommand')
    else:
        click.echo('I am about to invoke %s' % ctx.invoked_subcommand)


@cli.command()
@click.option('--show', '-s', is_flag=True, default=False)
def barplot(show):
  plt.style.use('ggplot')
  # Read the data
  df1 = read_data('ds', 'luh5', 'historical', 1950)
  df2 = read_data('ds', 'luh5', 'historical', 2010)

  # Then, just call :
  ax = plot_clustered_stacked([df1, df2], ["1950", "2010"],
                              title="Land use change 1950 to 2010")
  ax.set_ylabel('Fraction of land surface (%)')
  plt.savefig('landuse-1920-2010.png')
  if show:
    plt.show()

def bounds(meta):
  ul = meta['affine'] * (0, 0)
  lr = meta['affine'] * (meta['width'], meta['height'])
  return (ul[0], lr[1], lr[0], ul[1])

def eval(what, rsf, rsn):
  datan, meta = rsn.eval(what, quiet=True)
  dataf, _ = rsf.eval(what, quiet=True)
  #data_vals = dataf.filled(0) + datan.filled(0)
  #data = data_vals.view(ma.MaskedArray)
  #data.mask = np.logical_and(dataf.mask, datan.mask)
  #return data, meta
  area = carea(bounds(meta))
  valf = ma.sum(dataf * area)
  valn = ma.sum(datan * area)
  return float(valf + valn), meta

def project_hpd(scenario, year):
  print("projecting hpd for %d using %s" % (year, scenario))
  rasters = predicts.rasterset('luh2', scenario, year, 'f')
  rs = RasterSet(rasters)
  values, meta = rs.eval('hpd', quiet=True)
  area = tarea(bounds(meta), meta['height'])
  out = float(ma.sum(ma.masked_invalid(values * area)) / 1e9)
  return out

def project_year(model_dir, scenario, year):
  print("projecting land use for %d using %s" % (year, scenario))

  # Open forested/non-forested mask layer
  fstnf = rasterio.open('netcdf:%s:fstnf' % utils.luh2_static())

  # Import standard PREDICTS rasters
  rastersf = predicts.rasterset('luh2', scenario, year, 'f')
  rsf = RasterSet(rastersf, mask=fstnf, maskval=0.0)
  rastersn = predicts.rasterset('luh2', scenario, year, 'n')
  rsn = RasterSet(rastersn, mask=fstnf, maskval=1.0)

  lus = ('annual', 'nitrogen', 'pasture', 'perennial', 'primary',
         'rangelands', 'secondary', 'urban')
  stime = time.time()
  
  values = [eval(lu, rsf, rsn) for lu in lus]
  cells = carea(bounds(values[0][1]))
  area = ma.sum(cells)
  out = dict((lu, float(ma.sum(values[idx][0])))# / area * 100))
             for idx, lu in enumerate(lus))
  etime = time.time()
  print("executed in %6.2fs" % (etime - stime))
  return out

def unpack(args):
  return project_year(*args)

@cli.command()
@click.argument('scenario', type=click.Choice(utils.luh2_scenarios()))
@click.argument('years', type=YEAR_RANGE)
@click.argument('output', type=click.File('wb'))
@click.option('--model-dir', '-m', type=click.Path(file_okay=False))
@click.option('--history', type=click.File('rb'))
@click.option('--parallel', '-p', default=1, type=click.INT,
              help='How many projections to run in parallel (default: 1)')
def timeline(scenario, years, output, model_dir, history, parallel):
  if parallel == 1:
    data = map(lambda y: project_year(model_dir, scenario, y), years)
  else:
    pool = multiprocessing.Pool(processes=parallel)
    data = pool.map(unpack, itertools.izip(itertools.repeat(model_dir),
                                           itertools.repeat(scenario), years))

  lus = set(map(lambda xx: tuple(xx.keys()), data))
  assert len(lus) == 1
  lus = lus.pop()
  by_series = [{'name': lu, 'data': []} for lu in lus]
  for lu in by_series:
    for year in data:
      lu['data'].append(year[lu['name']])
  if history:
    hist = json.load(history)
    years = hist['years'] + years
    hist_map = dict((xx['name'], xx['data']) for xx in hist['data'])
    for row in by_series:
      if row['name'] in hist_map:
        row['data'] = hist_map[row['name']] + row['data']
  output.write(json.dumps({'years': years, 'data': by_series}))
  output.write("\n")

@cli.command()
@click.argument('output', type=click.File('wb'))
@click.option('--parallel', '-p', default=1, type=click.INT,
              help='How many projections to run in parallel (default: 1)')
def hpd(output, parallel):
  out = []
  for scenario in utils.luh2_scenarios():
    if scenario == 'historical':
      years = range(1950, 2011)
    else:
      years = range(2015, 2100)
    if True or parallel == 1:
      data = map(lambda y: project_hpd(scenario, y), years)
    else:
      pool = multiprocessing.Pool(processes=parallel)
      data = pool.map(unpack, itertools.izip(itertools.repeat(scenario), years))
    if scenario != 'historical':
      data = [None] * (2010 - 1950) + data
    out.append({'name': scenario, 'data': data})
  all_years = range(1950, 2011) + range(2015, 2100)
  output.write(json.dumps({'years': all_years, 'data': out}))
  output.write("\n")
  
if __name__ == '__main__':
  cli()
