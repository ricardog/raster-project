#!/usr/bin/env python
# -*- coding: utf-8 -*-
import rasterio

import click
from copy import copy
import itertools
import json
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

@lrudecorator(5)
def tarea(bounds=None, height=None):
  area = carea(bounds, height)
  ice_ds = rasterio.open(utils.luh2_static('icwtr'))
  if bounds is None:
    ice = ice_ds.read(1, masked=True)
  else:
    win = ice_ds.window(*bounds)
    if win[1][1] - win[0][1] > height:
      win = ((win[0][0], win[0][0] + height), win[1])
    ice = ice_ds.read(1, masked=True, window=win)
  return area * (1 - ice)

@lrudecorator(10)
def cnames_df():
  cnames = pd.read_csv(os.path.join(utils.data_root(), 'ssp-data',
                                    'country-names.csv'))
  return cnames

@lrudecorator(10)
def gdp_df():
  return pd.read_csv(utils.gdp_csv(), index_col=0).T

def gdp(year, fips=None):
  if fips:
    return gdp_df().loc[fips, year]
  else:
    return gdp_df().loc[:, year]

def cid_to_x(cid, x):
  if cid == 736:
    cid = 729
  df = cnames_df()
  row = df[df.un == cid]
  if not row.empty:
    return row[x].values[0]
  return str(int(cid))

def cid_to_fips(cid):
  return cid_to_x(cid, 'fips')

def cid_to_name(cid):
  return cid_to_x(cid, 'country.name.en')

def cid_to_ar5(cid):
  return cid_to_x(cid, 'ar5')

def mean_by(idx, data):
  assert idx.shape == data.shape
  return np.bincount(idx, weights=data)

def sum_by(idx, data):
  df = pd.DataFrame({'idx': ccode.reshape(-1),
                     'data': data.reshape(-1)}).dropna()
  agg = df.groupby(['idx'], sort=False).sum()
  return np.column_stack((agg.index.values.astype(int), agg.values))
  
def sum_by(ccode, data, weight):
  dd = data * weights
  dd.mask = np.logical_or(data.mask, ccode.mask)
  return sum_by(ccode, dd)

def weighted_mean_by_country(ccode, data, weights):
  dd = data * weights
  dd.mask = np.logical_or(data.mask, ccode.mask)
  save_mask = ccode.mask
  ccode.mask = dd.mask
  ccode_idx = ccode.compressed()
  ccode.mask = save_mask
  sums = mean_by(ccode_idx, dd.compressed())
  ncells = np.bincount(ccode_idx)
  idx = np.where(ncells > 0)
  carea = ncells[idx]
  return np.column_stack((idx[0].astype(int), carea, sums[idx] / carea))

def remap(what, table, nomatch=None):
  f = np.vectorize(lambda x: table.get(x, nomatch), otypes=[np.float32])
  shape = what.shape
  tmp = f(what.reshape(-1))
  return tmp.reshape(*shape)

def gen_mp4(oname, stack, ccode, title='', captions=None):
  from projections.mp4_utils import to_mp4

  all_max = stack[:, 2, :].max()
  all_min = stack[:, 2, :].min()
  cnorm = colors.Normalize(vmin=all_min, vmax=all_max)
  cmap = dict((k,v) for k,v in itertools.izip(stack[:, 0, 0],
                                              stack[:, 2, 0]))
  data = remap(ccode, cmap, ccode.fill_value)
  if captions is None:
    captions = tuple(itertools.repeat('', stack.shape[2]))
  elif len(captions) != stack.shape[2]:
    print "Error: not enough captions for all frames"
    return
  for idx, img, text in to_mp4(title, oname, stack.shape[2],
                               data, text='LogAbund', fps=10, cnorm=cnorm):
    cmap = dict((k,v) for k,v in itertools.izip(stack[:, 0, idx],
                                                stack[:, 2, idx]))
    img.set_array(remap(ccode, cmap, ccode.fill_value))
    text.set_text(captions[idx])

def parse_fname(fname):
  m = re.search(r'([a-zA-Z0-9.]+)-([a-zA-Z_]+)-([0-9]{4})\.tif$',
                os.path.basename(fname))
  if m:
    return int(m.group(3))
  return os.path.splitext(os.path.basename(fname))[0]


def parse_fname2(fname):
  return os.path.splitext(os.path.basename(fname))[0].rsplit('-', 2)

def printit(stacked):
  print "%4s %8s %8s %6s" % ('fips', 'start', 'end', '%')
  for idx in xrange(stacked.shape[0]):
    print "%4s %8.2f %8.2f %6.2f%%" % (cid_to_fips(stacked[idx, 0, 0]),
                                       stacked[idx, 2, 0],
                                       stacked[idx, 2, -1],
                                       (100.0 *
                                        stacked[idx, 2, -1] /
                                        stacked[idx, 2, 0]))

def to_df(stacked, names):
  hs = {'fips': map(cid_to_fips, stacked[:, 0, 0]),
        'name': map(cid_to_name, stacked[:, 0, 0]),
        'ar5': map(cid_to_ar5, stacked[:, 0, 0]),
        'ratio': stacked[:, 2, -1] / stacked[:, 2, 0],
        'percent': (stacked[:, 2, -1] - stacked[:, 2, 0]) / stacked[:, 2, 0]}
  assert len(names) == stacked.shape[2]
  for idx in xrange(stacked.shape[2]):
    hs[names[idx]] = stacked[:, 2, idx]
  df = pd.DataFrame(hs, index=stacked[:, 0, 0].astype(int))
  return df

@click.group(invoke_without_command=True)
@click.pass_context
def cli(ctx):
    if ctx.invoked_subcommand is None:
        click.echo('I was invoked without subcommand')
    else:
        click.echo('I am about to invoke %s' % ctx.invoked_subcommand)

@cli.command()
@click.argument('country-file', type=click.Path(dir_okay=False))
@click.argument('infiles', nargs=-1, type=click.Path(dir_okay=False))
@click.option('--npp', type=click.Path(dir_okay=False),
              help='Weight the abundance data with NPP per cell')
@click.option('-b', '--band', type=click.INT, default=1,
              help='Index of band to process (default: 1)')
@click.option('--mp4', type=click.Path(dir_okay=False),
              help='Generate a video (in mp4 format) of the by country' +
              'weighted mean (default: False)')
@click.option('-l', '--log', is_flag=True, default=False,
              help='When set the data is in log scale and must be ' +
              'converted to linear scale (default: False)')
def countrify(infiles, band, country_file, npp, mp4, log):
  stack = []
  maps = []
  extent = None
  extent_inset = None
  area = None
  if npp:
    npp_ds = rasterio.open(npp)
  with rasterio.open(country_file) as cc_ds:
    for arg in infiles:
      with rasterio.open(arg) as src:
        win = cc_ds.window(*src.bounds)
        if win[1][1] - win[0][1] > src.height:
          win = ((win[0][0], win[0][0] + src.height), win[1])
        ccode = cc_ds.read(1, masked=True, window=win)
        if extent is None:
          extent = (src.bounds.left, src.bounds.right,
                    src.bounds.bottom, src.bounds.top)
          ul = src.affine * (480, 400)
          lr = src.affine * (530, 450)
          extent_inset = (ul[0], lr[0], lr[1], ul[1])
        data = src.read(band, masked=True)
        if log:
          data = ma.exp(data)
        if npp:
          npp_data = npp_ds.read(1, masked=True,
                                 window=npp_ds.window(*src.bounds))
          data *= npp_data
        res = weighted_mean_by_country(ccode, data, carea(src.bounds,
                                                          src.height))
        if area == None:
          ice_ds = rasterio.open('NETCDF:"../../data/luh2_v2/staticData_quarterdeg.nc":icwtr')
          ice = ice_ds.read(1, window=ice_ds.window(*src.bounds))
          area = ma.MaskedArray(carea(src.bounds, src.height))
          area.mask = np.where(ice == 1, True, False)
          intercept = np.exp(4.63955498) * area
          if npp:
            npp_data = npp_ds.read(1, masked=True,
                                   window=npp_ds.window(*src.bounds))
            intercept *= npp_data

        #res = weighted_mean_by_country(ccode, data, 1)
        stack.append(res)
        maps.append(data)
        print '%40s: %8.2f / %8.2f' % (os.path.basename(arg),
                                       res[2, :].max(), res[2, :].min())
    stacked = np.dstack(stack)
    names = map(parse_fname, infiles)
    df = to_df(stacked, names)
    print df

    ratio = maps[-1] / maps[0]
    a = ma.where(ratio > 1.05)
    b = ma.where(ratio < 0.85)
    w = ma.where((ratio >= 0.75) & (ratio <= 1.05))
    area.mask = ratio.mask

    above = ma.sum(area[a])
    below = ma.sum(area[b])
    within = ma.sum(area[w])
    total = ma.sum(area)
    unaccounted = ma.sum(area[ratio.mask != area.mask])
    print "Area: %6.4f / %6.4f / %6.4f" % (above / total, below / total, within / total)

    q = ma.masked_invalid(maps[0] * area)
    above = ma.sum(q[a])
    below = ma.sum(q[b])
    within = ma.sum(q[w])
    total = ma.sum(q)
    print "0: %6.4f / %6.4f / %6.4f" % (above / total, below / total, within / total)

    q = ma.masked_invalid(maps[-1] * area)
    above = ma.sum(q[a])
    below = ma.sum(q[b])
    within = ma.sum(q[w])
    total = ma.sum(q)
    print "1: %6.4f / %6.4f / %6.4f" % (above / total, below / total, within / total)
    total1950 = ma.sum(ma.masked_invalid(maps[0] * area))
    
    # newbold-a intercept is 4.63955498
    pristine = ma.sum(intercept)
    
    print "loss w.r.t. primary: %6.4f" % (total / pristine)
    print "loss w.r.t. 1950   : %6.4f" % (total / total1950)
    #pdb.set_trace()    
    gdp_1950 = gdp([1950, 1951])
    gdp_1950.columns = ('gdp', 'gdp_1951')
    merged = pd.merge(df, gdp_1950, left_on='fips', right_index=True,
                      sort=False).sort_values(by=['gdp'])
    #plt.plot(merged.gdp / merged.gdp.min(), merged.ratio, 'o')
    #plt.plot(range(len(merged)), merged.ratio, 'o')
    #ax = plt.gca()
    #ax.set_xscale('log')
    #plt.show()
    merged['pindex'] = range(len(merged))
    idx = 0
    syms = ['x', 'o', '+', 'v', '^', '*']
    cols = ['r', 'g', 'blue', 'b', 'purple', 'y']

    plt.style.use('ggplot')
    fig1 = plt.figure(figsize=(6, 4))
    ax1 = plt.gca()
    for name, group in merged.groupby('ar5'):
      ax1.plot(group.pindex, group.ratio, label=name, marker=syms[idx],
              linestyle='', #ms=11,
              c=cols[idx])
      idx += 1
    #ax1.set_title('SSP3 (RCP 7.0) AIM')
    ax1.plot([0, len(df)], [1.0, 1.0], color='k', linestyle='-', linewidth=2)

    title = u'Abundance gain (loss) 1950 — 2010'
    ax1.set_title(title)
    ax1.set_ylabel('Mean area weighted abundance gain (%)')
    ax1.set_xlabel('Country sorted by GDP (1950)')
    ax1.xaxis.set_major_locator(plt.NullLocator())
    ax1.legend()
    fig1.savefig('ab-by-gdp.png')
    fig1.savefig('ab-by-gdp.pdf')
    plt.show()

    palette = copy(plt.cm.viridis)
    palette.set_over('w', 1.0)
    palette.set_under('r', 1.0)
    palette.set_bad('k', 1.0)

    fig2 = plt.figure(figsize=(6, 4))
    ax2 = plt.gca()
    title = u'Abundance ratio 2010 / 1950'
    ax2.set_title(title)
    ax2.axis('off')
    img = plt.imshow(maps[-1] / maps[0], cmap=palette, vmin=0.75, vmax=1.05,
                     extent=extent)
    plt.colorbar(orientation='horizontal')
    fig2.savefig('ab-1950-2010.png')
    fig2.savefig('ab-1950-2010.pdf')
    plt.show()

    fig3, (ax1, ax2) = plt.subplots(1, 2, figsize=(6, 4))
    ax1.set_title(u'Abundance 1950')
    ax2.set_title(u'Abundance 2010')
    mmin = min(maps[0][400:450, 480:530].min(),
               maps[-1][400:450, 480:530].min())
    mmax = max(maps[0][400:450, 480:530].max(),
               maps[-1][400:450, 480:530].max())
    img1 = ax1.imshow(maps[0][400:450, 480:530], cmap=palette,
                      extent=extent_inset, vmin=mmin, vmax=mmax)
    img2 = ax2.imshow(maps[-1][400:450, 480:530], cmap=palette,
                      extent=extent_inset, vmin=mmin, vmax=mmax)
    ax3 = fig3.add_axes((0.1, 0.05, 0.8, 0.1))
    fig3.colorbar(img1, cax=ax3, orientation='horizontal')
    fig3.savefig('ab-inset.png')
    plt.show()
    
    #printit(stacked)
    #diff = np.column_stack((stacked[:, 0, 0], mmax, mmin))
    #print diff
    if mp4:
      gen_mp4(mp4, stacked, ccode)

@cli.command()
@click.argument('infiles', nargs=-1, type=click.Path(dir_okay=False))
@click.option('--npp', type=click.Path(dir_okay=False),
              help='Weight the abundance data with NPP per cell')
@click.option('-b', '--band', type=click.INT, default=1,
              help='Index of band to process (default: 1)')
def timeline(infiles, npp, band):
  area = None
  if npp:
    npp_ds = rasterio.open(npp)
  parsed = map(lambda fname: parse_fname2(fname), infiles)
  scenarios, whats, years = zip(*parsed)
  yy = sorted(set(map(int, years)))
  assert len(set(whats)) == 1
  keys = tuple(set(scenarios))
  out = dict((key, [0.0] * len(yy)) for key in keys)
  out = [{'name': xx, 'data': [0.0] * len(yy)} for xx in keys]
  for scenario, year, arg in zip(scenarios, years, infiles):
    print scenario, year
    with rasterio.open(arg) as src:
      data = src.read(band, masked=True)
      if npp:
        npp_data = npp_ds.read(1, masked=True,
                               window=npp_ds.window(*src.bounds))
        data *= npp_data
      area = tarea(src.bounds, src.height)
      data *= area
      out[keys.index(scenario)]['data'][years.index(year)] = float(ma.sum(data))

  if 'historical' in keys:
    #ref = out[keys.index('historical')]['data'][0]
    ref = ma.sum(area)
    for jj, k in enumerate(out):
      for ii, v in enumerate(k['data']):
        out[jj]['data'][ii] /= ref
  print json.dumps({'years': yy, 'data': out})
  print
  
if __name__ == '__main__':
  cli()
