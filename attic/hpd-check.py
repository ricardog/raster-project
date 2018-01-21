#!/usr/bin/env python

from itertools import groupby
import os
import re
import sys

from bokeh.io import output_file, show, save
from bokeh.layouts import gridplot, column
from bokeh.models import Range1d, ColumnDataSource, HoverTool, CrosshairTool
from bokeh.palettes import Category20, brewer, viridis
from bokeh.plotting import figure

import click

import matplotlib.pyplot as plt
import numpy as np
import numpy.ma as ma
import pandas as pd
import rasterio
from rasterio.plot import show

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

def _one(fname, scale=True, band=1):
  ds = rasterio.open(fname)
  area = rcs(ds.height, ds.res, *ds.bounds)
  data = ds.read(band, masked=True).filled(0)
  data[np.where(np.isnan(data))] = 0
  adj = data * area if scale else data
  return adj.sum()

def one(name, fname, scale=True, band=1):
  ds = rasterio.open(fname)
  area = rcs(ds.height, ds.res, *ds.bounds)
  data = ds.read(band, masked=True).filled(0)
  data[np.where(np.isnan(data))] = 0
  adj = data * area if scale else data
  print("%-30s: %e" % (name, adj.sum()))
  #print("%10s: %e" % ('max', data.max()))
  if not scale:
    print("%30s: %e" % ('max', (data / area).max()))

def get_files(dname, what):
  files = groupby(map(lambda f: f.rsplit('-', 2),
                      map(lambda p: os.path.splitext(p)[0],
                          filter(lambda f: re.search(r'-%s-\d+.tif$' % what, f),
                                 sorted(os.listdir(dname))))),
                  key=lambda s: s[0])
  out = {}
  for scenario, content in files:
    out[scenario] = ['%s-%s-%s.tif' % (s, w, y)
                     for s, w, y in tuple(content)]
  return out

def pline(p, df, column, legend=None, color='black', line_width=3):
    src = ColumnDataSource(data={
        'year': df.index,
        'data': df[column],
        'name': [legend for n in range(len(df))]
    })
    if legend is None:
      legend = column
    p.line('year', 'data', source=src, line_width=line_width,
           legend=legend, color=color)

def bokeh_plot(dfs, title=''):
  p = figure(title='Worldwide Human Population (%s)' % title)
  mypalette=Category20[min(max(3, len(dfs)), 20)]
  for idx, scenario in enumerate(dfs):
    df = dfs[scenario]
    name = scenario.split('_', 1)[0]
    pline(p, df, scenario, name, mypalette[idx], 3)
  p.add_tools(HoverTool(tooltips=[('Year', '@year'),
                                  ('Population', '@data'),
                                  ('Scenario', '@name')]))
  p.legend.location = "top_left"
  return p

def do_plot(dfs, title, bokeh, out):
  if bokeh:
    p = bokeh_plot(dfs, title)
    if out:
      output_file(out)
    save(p)
  else:
    ax = None
    for key in dfs:
      ax = dfs[key].plot(ax=ax)
    ax.set_title('Worldwide Human Population (%s)' % title)
    plt.show()
  
@click.group(invoke_without_command=True)
@click.pass_context
def cli(ctx):
  if ctx.invoked_subcommand is None:
    click.echo('I was invoked without subcommand')
    projections()

@cli.command()
@click.pass_context
@click.argument('series', type=click.Choice(('hyde', 'sps', 'projected', 'all')))
@click.option('--outdir', type=click.Path(dir_okay=True, file_okay=False),
              default='/out/luh2')
@click.option('-o', '--out', type=click.Path(dir_okay=False, file_okay=True))
@click.option('-b', '--bokeh', is_flag=True, default=False)
def plot(ctx, series, outdir, out, bokeh):
  if series == 'hyde':
    dfs = hyde(outdir)
  elif series == 'sps':
    dfs = sps(outdir)
  elif series == 'projected':
    dfs = projected(outdir, 'hpd')
  elif series == 'all':
    p1 = bokeh_plot(hyde(outdir), 'hyde')
    p2 = bokeh_plot(sps(outdir), 'sps')
    p3 = bokeh_plot(projected(outdir), 'projected')
    col = column(p1, p2, p3)
    if out:
      output_file(out)
    save(col)
    return
  do_plot(dfs, series, bokeh, out)

def hyde(outdir):
  print('hyde')
  df = pd.DataFrame()
  ds = rasterio.open('netcdf:' + os.path.join(outdir, 'hyde.nc:popd'))
  years = tuple(map(lambda idx: int(ds.tags(idx)['NETCDF_DIM_time']),
                    ds.indexes))
  df['historical'] = tuple(map(lambda y: _one(ds.name, True,
                                              years.index(y) + 1),
                               years))
  df.index = years
  return {'historical': df}


def sps(outdir, raw=False):
  dfs = {}
  for scenario in map(lambda n: 'ssp%d' % n, range(1, 6)):
    print(scenario)
    df = pd.DataFrame()
    if raw:
      raise NotImplementedError('SPS unscaled support not implemented')
    else:
      ds = rasterio.open('netcdf:' +
                         os.path.join(outdir, 'sps.nc:%s' % scenario))
      years = tuple(map(lambda idx: int(ds.tags(idx)['NETCDF_DIM_time']),
                        ds.indexes))
      df[scenario] = tuple(map(lambda y: ds.read(years.index(y) + 1,
                                                 masked=True).sum(), years))
      df.index = years
    dfs[scenario] = df
  return dfs


def projected(outdir, what='hpd'):
  files = get_files(outdir, what)
  dfs = {}
  for scenario in files:
    print(scenario)
    df = pd.DataFrame()
    df[scenario] = tuple(map(lambda f: _one(os.path.join(outdir, f), True, 1),
                             files[scenario]))
    df.index = tuple(map(lambda f: int(os.path.splitext(f)[0].rsplit('-', 1)[-1]),
                         files[scenario]))
    dfs[scenario] = df
  return dfs

@cli.command()
def old_school():
  for year in (2011, 2012, 2013, 2014):
    one(str(year), '/out/luh2/historical-hpd-%d.tif' %year, True)
  return

  for year in (2010, 2099):
    scenario = 'ssp3'
    one('%s/%d' % (scenario, year),
        'netcdf:%s/luh2/sps.nc:%s' % (utils.outdir(), scenario),
        False, year - 2009)

  for name, fname, scale in (('gluds qd', '/out/luh2/gluds00ag.tif', True),
                             ('v4 qd', '/out/luh2/grumps4.tif', True),
  #                           ('1950', '/Volumes/Vagrant 155/playground/ds/luh2/historical-hpd-1950.tif', True),
                             ('sps3/2015', 'netcdf:/out/luh2/sps.nc:ssp3', False),
                             ('v4', utils.grumps4(), True),
                             ('gluds', utils.grumps1(), True),):
    one(name, fname, scale)

  #                           ('sps1', '/data/sps/SSP1_NetCDF/total/NetCDF/ssp1_2010.nc', False),
  #                           ('sps2', '/data/sps/SSP2_NetCDF/total/NetCDF/ssp2_2010.nc', False),
  #                           ('sps3', '/data/sps/SSP3_NetCDF/total/NetCDF/ssp3_2010.nc', False),
  #                           ('sps4', '/data/sps/SSP4_NetCDF/total/NetCDF/ssp4_2010.nc', False),
  #                           ('sps5', '/data/sps/SSP5_NetCDF/total/NetCDF/ssp5_2010.nc', False),
  
if __name__ == '__main__':
  cli()
