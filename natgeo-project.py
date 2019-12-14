#!/usr/bin/env python

import os
import sys
import time

import click

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
        values = value.split(':')
        if len(values) == 3:
          low, high, inc = values
        elif len(values) == 2:
          low, high = values
          inc = '1'
        else:
          raise ValueError
        return range(int(low), int(high), int(inc))
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
  rasters = predicts.rasterset('glb_lu', None, year, 'wpp')
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
      expr = '(%s / %f)'
    rs[what] = SimpleExpr(what, expr % (mod.output, mod.intercept))

  if what not in rs:
    print('%s not in rasterset' % what)
    print(', '.join(sorted(rs.keys())))
    sys.exit(1)

  stime = time.time()
  rs.write(what, utils.outfn('glb-lu', '%s-%d.tif' % (what, year)))
  etime = time.time()
  print("executed in %6.2fs" % (etime - stime))
  return


@click.command()
@click.argument('what', type=click.Choice(['ab', 'sr', 'cs-ab', 'cs-sr',
                                           'hpd']))
@click.argument('years', type=YEAR_RANGE)
@click.option('--model-dir', '-m', type=click.Path(file_okay=False),
              default=os.path.abspath('.'),
              help='Directory where to find the models ' +
              '(default: ../models)')
def project(what, years, model_dir):
  """Project changes in terrestrial biodiversity using REDICTS models.

  Writes output to a GeoTIFF file named <scenario>-<what>-<year>.tif.

  """

  for year in years:
    project_year(what, model_dir, 'glb_lu', year)

if __name__ == '__main__':
#pylint: disable-msg=no-value-for-parameter
  project()
#pylint: enable-msg=no-value-for-parameter
