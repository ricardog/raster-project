#!/usr/bin/env python3

from copy import copy
import os

import click
import matplotlib.pyplot as plt
from mpl_toolkits.axes_grid1 import make_axes_locatable
import numpy as np
import numpy.ma as ma
import rasterio
from rasterio.plot import show, plotting_extent

import projections.utils as utils

import pdb

def read_historical(start, end, bounds, metric):
  path = '/out/luh2/historical-%s-%%d.tif' % metric
  nodata = -9999.0
  data = []
  last_year = None
  for year in range(start, end):
    fname = path % year
    if os.path.isfile(fname):
      with rasterio.open(fname) as src:
        win = src.window(*bounds)
        d = src.read(1, masked=True, window=win)
      if last_year is not None and (year - last_year != 1):
        ## Interpolate between the values
        delta = year - last_year
        f1 = 1. / delta
        for yy in range(last_year + 1, year):
          i = yy - last_year
          dd = data[-1] * i * f1 + d * (delta - i) * f1
          data.append(dd)
        pass
      data.append(d)
      last_year = year
  stack = np.stack(data, axis=0)
  stack2 = ma.masked_equal(stack, nodata)
  return stack2

@click.command()
@click.argument('metric', click.Choice(['Ab', 'SR', 'CompSimAb', 'CompSimSR',
                                        'BIIAb', 'BIISR']))
@click.argument('scenario', type=click.Choice(utils.luh2_scenarios()))
@click.option('--start', '-s', type=int, default=1900)
@click.option('--out', '-o', type=click.File(mode='wb'))
def main(metric, scenario, start, out):
  palette = copy(plt.cm.viridis_r)
  palette.set_under('k', 1.0)
  palette.set_over('r', 1.0)
  palette.set_bad('w', 1.0)

  fname = '/out/luh2/%s-%s-%d.tif' % (scenario, metric, 2100)
  with rasterio.open(fname) as src:
    meta = src.meta
    end = src.read(1, masked=True)
    stack = read_historical(start, 2015, src.bounds, metric)
  inc = ma.where(stack < end, 1, 0)
  years = inc.sum(axis=0)
  years2 = ma.where(end > stack[-1],
                    ma.where(end > stack[0], start - 1, 2015 - years), -1)
  if out:
    meta_out = meta.copy()
    meta_out['dtype'] = 'int32'
    with rasterio.open(out.name, 'w', **meta_out) as dst:
      dst.write(years2.filled(meta_out['nodata']).astype(np.int32),
                indexes=1)
  title = 'Abundance-based BII recovery year (%s)' % scenario
  vmin = start - 2
  vmax = 2015
  dpi = 100.0
  size = [years2.shape[1] / dpi, years2.shape[0] / dpi]
  size[1] += 70 / dpi
  fig = plt.figure(figsize=size, dpi=dpi)
  ax = plt.gca()
  show(years2, ax=ax, cmap=palette, title=title, vmin=vmin, vmax=vmax,
         extent=plotting_extent(src))
  fig.tight_layout()
  #ax.axis('off')
  divider = make_axes_locatable(ax)
  cax = divider.append_axes("bottom", size="5%", pad=0.25)
  plt.colorbar(ax.images[0], cax=cax, orientation='horizontal')
  fig.savefig(out.name.replace('.tif', '.png'), transparent=False)
  plt.show()
  
  #show(years2, cmap=palette, vmin=start, vmax=2100)
  #pdb.set_trace()
  pass

if __name__ == '__main__':
  main()
