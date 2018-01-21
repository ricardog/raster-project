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

def select_model(model, model_dir):
  """Select the appropriate models for abundance, spieces richness, or
compositional similarity depending on what the user wants to project.

  Assumes models have fixed name and live in the folder passed as a
  parameter.

  """

  if model == 'ab':
    mod = 'ab.rds'
    out = 'Abundance'
  elif model == 'sr':
    mod = 'sr.rds'
    out = 'Richness'
  elif model == 'cs-ab':
    mod = 'cs-ab.rds'
    out = 'CompSimAb'
  elif model == 'cs-sr':
    mod = 'cs-sr.rds'
    out = 'CompSimSR'
  else:
    mod = None
    out = model
    #raise RuntimeError('Unknown model type %s' % model)
  return out, None if mod is None else os.path.join(model_dir, mod)

def project_year(model, model_dir, scenario, year):
  """Run a projection for a single year.  Can be called in parallel when
projecting a range of years.

  """

  print("projecting %s for %d using %s" % (model, year, scenario))

  # Import standard PREDICTS rasters
  rasters = predicts.rasterset('luh2', scenario, year)
  rs = RasterSet(rasters)

  what, model = select_model(model, model_dir)
  # Read Sam's models
  if model:
    mod = modelr.load(model)
    predicts.predictify(mod)
    rs[mod.output] = mod

  if what in ('CompSimAb', 'CompSimSR', 'Abundance', 'Richness'):
    if what in ('CompSimAb', 'CompSimSR'):
      expr = '(inv_logit(%s) - 0.01) / (inv_logit(%f) - 0.01)'
    else:
      expr = '(exp(%s) / exp(%f))'
    rs[what] = SimpleExpr(what, expr % (mod.output, mod.intercept))

  if what not in rs:
    print('%s not in rasterset' % what)
    print(', '.join(sorted(rs.keys())))
    sys.exit(1)

  stime = time.time()
  data, meta = rs.eval(what, quiet=True)
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
@click.argument('what', type=click.Choice(['ab', 'sr', 'cs-ab', 'cs-sr',
                                           'hpd']))
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
