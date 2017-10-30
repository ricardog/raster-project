#!/usr/bin/env python

import click
from copy import copy
#import gdal
import matplotlib.pyplot as plt
from mpl_toolkits.axes_grid1 import make_axes_locatable
import numpy.ma as ma
import rasterio
#import projections.tiff_utils as tu

@click.command()
@click.argument('infile', type=click.Path(dir_okay=False))
@click.argument('outfile', type=click.Path(dir_okay=False))
@click.option('-b', '--band', type=int, default=1)
def plot(infile, outfile, band):
  palette = copy(plt.cm.viridis)
  #palette.set_over('w', 1.0)
  #palette.set_under('r', 1.0)
  palette.set_bad('k', 1.0)
  
  #ds = gdal.Open(infile)
  #band = ds.GetRasterBand(band)
  #raw = band.ReadAsArray()
  #print(raw.shape)
  #ndv = band.GetNoDataValue()
  #data = ma.masked_equal(raw, ndv)
  #print(data.shape)
  #vmin, vmax = tu.get_min_max(ds)
  #print(vmin, vmax)
  #vmin, vmax = (4.2, 4.69)
  ds = rasterio.open(infile)
  data = ds.read(band, masked=True)
  vmin, vmax = (0.31, 1.51)
  #import pdb; pdb.set_trace()
  fig = plt.figure(figsize=(14.40, 5.59), dpi=100)
  ax1 = plt.gca()
  img = ax1.matshow(data, vmax=vmax, vmin=vmin, cmap=palette)
  ax1.axes.get_yaxis().set_visible(False)
  ax1.axes.get_xaxis().set_visible(False)
  ax1.set_frame_on(False)
  divider = make_axes_locatable(ax1)
  cax = divider.append_axes("bottom", size="10%", pad=0.05)
  plt.colorbar(img, cax=cax, orientation='horizontal')
  plt.savefig(outfile, transparent=True, bbox_inches="tight", pad_inches=0)
  #plt.show()


if __name__ == '__main__':
  plot()
