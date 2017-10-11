#!/usr/bin/env python

import click
import fiona
import itertools
import matplotlib.pyplot as plt
import multiprocessing
import numpy as np
import numpy.ma as ma
import os
import sys
import time
import rasterio
from rasterio.plot import show, show_hist

import pdb

from projections.rasterset import RasterSet, Raster
from projections.simpleexpr import SimpleExpr
import projections.r2py.modelr as modelr
import projections.predicts as predicts
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

def select_models(model, model_dir):
  if model == 'ab':
    mods = ('ab-fst-1.rds', 'ab-nfst-1.rds')
  elif model == 'sr':
    mods = ('sr-fst.rds', 'sr-nfst.rds')
  else:
    mods = ('bii-fst-scaled.rds', 'bii-nfst-scaled.rds')
  return map(lambda x: os.path.join(model_dir, x), mods)

def project_year(model, model_dir, what, scenario, year):
  print "projecting %s for %d using %s" % (what, year, scenario)

  models = select_models(model, model_dir)
  # Read Sam's abundance model (forested and non-forested)
  modf = modelr.load(models[0])
  intercept_f = modf.intercept
  predicts.predictify(modf)

  modn = modelr.load(models[1])
  intercept_n = modn.intercept
  predicts.predictify(modn)
  
  # Open forested/non-forested mask layer
  fstnf = rasterio.open(utils.luh2_static('fstnf'))

  # Import standard PREDICTS rasters
  rastersf = predicts.rasterset('luh2', scenario, year, 'f')
  rsf = RasterSet(rastersf, mask=fstnf, maskval=0.0)
  rastersn = predicts.rasterset('luh2', scenario, year, 'n')
  rsn = RasterSet(rastersn, mask=fstnf, maskval=1.0)
  #rsn = RasterSet(rastersn)

  if what == 'bii':
    vname = 'bii'
    rsf[vname] = SimpleExpr(vname, 'exp(%s) / exp(%f)' % (modf.output,
                                                          intercept_f))
    rsn[vname] = SimpleExpr(vname, 'exp(%s) / exp(%f)' % (modn.output,
                                                          intercept_n))
    rsf[modf.output] = modf
    rsn[modn.output] = modn
  else:
    vname = modf.output
    assert modf.output == modn.output
    rsf[vname] = modf
    rsn[vname] = modn

  if what not in rsf:
    print '%s not in rasterset' % what
    print ', '.join(sorted(rsf.keys()))
    sys.exit(1)
    
  stime = time.time()
  datan, meta = rsn.eval(what, quiet=False)
  dataf, _ = rsf.eval(what, quiet=True)
  data_vals = dataf.filled(0) + datan.filled(0)
  data = data_vals.view(ma.MaskedArray)
  data.mask = np.logical_and(dataf.mask, datan.mask)
  #data = datan
  etime = time.time()
  print "executed in %6.2fs" % (etime - stime)
  oname = 'ds/luh2/%s-%s-%d.tif' % (scenario, what, year)
  with rasterio.open(oname, 'w', **meta) as dst:
    dst.write(data.filled(meta['nodata']), indexes = 1)
  if None:
    fig = plt.figure(figsize=(8, 6))
    ax = plt.gca()
    show(data, cmap='viridis', ax=ax)
    plt.savefig('luh2-%s-%d.png' % (scenario, year))
  return

def unpack(args):
  project_year(*args)

@click.command()
#@click.argument('what', type=click.Choice(['ab', 'sr']))
@click.argument('model', type=click.Choice(['ab', 'sr', 'bii']))
@click.argument('what', type=str)
@click.argument('scenario', type=click.Choice(utils.luh2_scenarios()))
@click.argument('years', type=YEAR_RANGE)
@click.option('--model-dir', '-m', type=click.Path(file_okay=False),
                default=os.path.join('..', 'models'),
              help='Directory where to find the models ' +
              '(default: ../models)')
@click.option('--parallel', '-p', default=1, type=click.INT,
              help='How many projections to run in parallel (default: 1)')
def project(model, what, scenario, years, model_dir, parallel=1):
  if parallel == 1:
    map(lambda y: project_year(model, model_dir, what, scenario, y), years)
    return
  pool = multiprocessing.Pool(processes=parallel)
  pool.map(unpack, itertools.izip(itertools.repeat(model),
                                  itertools.repeat(model_dir),
                                  itertools.repeat(what),
                                  itertools.repeat(scenario), years))
    
if __name__ == '__main__':
  project()
