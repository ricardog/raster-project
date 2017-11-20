#!/usr/bin/env python

import itertools
import multiprocessing
import os
import sys
import time

import click
import matplotlib.pyplot as plt
import numpy as np
import numpy.ma as ma
import rasterio
from rasterio.plot import show

from projections.rasterset import RasterSet
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
        low, high = value.split(':')
        return range(int(low), int(high))
    except ValueError:
      self.fail('%s is not a valid year range' % value, param, ctx)

YEAR_RANGE = YearRangeParamType()

def select_models(model, model_dir):
  """Select the appropriate models for abundance, spieces richness, or
compositional similarity depending on what the user wants to project.

  Assumes models have fixed name and live in the folder passed as a
  parameter.

  """

  if model == 'ab':
    mods = ('ab-forested.rds', 'ab-nonforested.rds')
    out = 'Abundance'
  elif model == 'sr':
    mods = ('sr-forested.rds', 'sr-nonforested.rds')
    out = 'Richness'
  elif model == 'cs-ab':
    mods = ('cs-for-ab.rds', 'cs-non-ab.rds')
    out = 'CompSimAb'
  elif model == 'cs-sr':
    mods = ('cs-for-sr.rds', 'cs-non-sr.rds')
    out = 'CompSimSR'
  else:
    raise RuntimeError('Unknown model type %s' % model)
  return out, tuple(map(lambda x: os.path.join(model_dir, x), mods))

def project_year(model, model_dir, scenario, year):
  """Run a projection for a single year.  Can be called in parallel when
projecting a range of years.

  """

  print("projecting %s for %d using %s" % (model, year, scenario))

  what, models = select_models(model, model_dir)
  # Read Sam's abundance model (forested and non-forested)
  modf = modelr.load(models[0])
  predicts.predictify(modf)

  modn = modelr.load(models[1])
  predicts.predictify(modn)

  # Open forested/non-forested mask layer
  fstnf = rasterio.open(utils.luh2_static('fstnf'))

  # Import standard PREDICTS rasters
  rastersf = predicts.rasterset('luh2', scenario, year, 'f')
  rsf = RasterSet(rastersf, mask=fstnf, maskval=0.0)
  rastersn = predicts.rasterset('luh2', scenario, year, 'n')
  rsn = RasterSet(rastersn, mask=fstnf, maskval=1.0)
  #rsn = RasterSet(rastersn)

  if what in ('CompSimAb', 'CompSimSR'):
    expr = '(inv_logit(%s) - 0.001) / (inv_logit(%f) - 0.001)'
  else:
    expr = '(exp(%s) / exp(%f))'
  rsf[what] = SimpleExpr(what, expr % (modf.output, modf.intercept))
  rsn[what] = SimpleExpr(what, expr % (modn.output, modn.intercept))

  rsf[modf.output] = modf
  rsn[modn.output] = modn

  if what not in rsf:
    print('%s not in rasterset' % what)
    print(', '.join(sorted(rsf.keys())))
    sys.exit(1)

  stime = time.time()
  datan, meta = rsn.eval(what, quiet=True)
  dataf, _ = rsf.eval(what, quiet=True)
  data_vals = dataf.filled(0) + datan.filled(0)
  data = data_vals.view(ma.MaskedArray)
  data.mask = np.logical_and(dataf.mask, datan.mask)
  etime = time.time()
  print("executed in %6.2fs" % (etime - stime))
  oname = '%s/luh2/%s-%s-%d.tif' % (utils.outdir(), scenario, what, year)
  with rasterio.open(oname, 'w', **meta) as dst:
    dst.write(data.filled(meta['nodata']), indexes=1)
  if None:
    fig = plt.figure(figsize=(8, 6))
    show(data, cmap='viridis', ax=plt.gca())
    fig.savefig('luh2-%s-%d.png' % (scenario, year))
  return

def unpack(args):
  """Unpack arguments passed to parallel map."""
  project_year(*args)

@click.command()
@click.argument('what', type=click.Choice(['ab', 'sr', 'cs-ab', 'cs-sr']))
@click.argument('scenario', type=click.Choice(utils.luh2_scenarios()))
@click.argument('years', type=YEAR_RANGE)
@click.option('--model-dir', '-m', type=click.Path(file_okay=False),
              default=os.path.abspath('.'),
              help='Directory where to find the models ' +
              '(default: ../models)')
@click.option('--parallel', '-p', default=1, type=click.INT,
              help='How many projections to run in parallel (default: 1)')
def project(what, scenario, years, model_dir, parallel=1):
  """Project changes in terrestrial biodiversity using REDICTS models.

  Writes output to a GeoTIFF file named <scenario>-<what>-<year>.tif.

  """

  utils.luh2_check_year(min(years), scenario)
  utils.luh2_check_year(max(years), scenario)
  if parallel == 1:
    tuple(map(lambda y: project_year(what, model_dir, scenario, y),
              years))
    return
  pool = multiprocessing.Pool(processes=parallel)
  pool.map(unpack, zip(itertools.repeat(what),
                       itertools.repeat(model_dir),
                       itertools.repeat(scenario), years))

if __name__ == '__main__':
#pylint: disable-msg=no-value-for-parameter
  project()
#pylint: enable-msg=no-value-for-parameter
