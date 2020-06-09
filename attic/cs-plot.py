#!/usr/bin/env python3

import click
import matplotlib
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import re
import seaborn as sns

import projections.r2py.modelr as modelr
import projections.lu.luh2 as luh2

import pdb

def inv_logit(p):
  """Returns the inverse logit function of the input."""
  return np.exp(p) / (1 + np.exp(p))

@click.command()
@click.argument('model', type=click.Path(dir_okay=False))
@click.option('--title', '-t', type=str,
              default='Model response vs HPD',
              help='Plot title')
@click.option('--adjust', type=float,
              default=0.1,
              help='Adjustment value for inverse logit transformation')
@click.option('--save', type=click.Path(dir_okay=False),
              help='A file to save the plot to.')
@click.option('--tropical', '-t', is_flag=True, default=False)
def plot(model, title, save, adjust, tropical):
  """Plot response curve of CS model versus HPD."""
  mod = modelr.load(model)

  columns = tuple(filter(lambda x: re.search(r'_age\d+$', x), mod.syms))
  df = pd.DataFrame(columns=tuple(luh2.LU.keys()))
  df = pd.DataFrame(columns=columns)
  pname1 = 'forested_tropic_temperate_tropical_forest'
  pname2 = 'tropic_temperate_tropical_forest_tropical_forest'

  tropical = 1 if tropical else 0
    
  for col in df.columns:
    s = pd.Series(mod.partial({'loghpd': np.linspace(0, 11, 13),
                               's2_loghpd': np.linspace(0, 11, 13),
                               'hpd_diff': np.linspace(0, -11, 13),
                               pname1: tropical,
                               pname2: tropical,
                               col: np.full((13), 1)}))
    intercept = mod.intercept

    if mod.output == 'sqrtRescaledAbundance':
        df[col] = np.power(s, 2) / np.power(intercept, 2)
    else:
        df[col] = (inv_logit(s) - adjust) / (inv_logit(intercept) - adjust)

  prefix = df.columns[0].rsplit('_', 1)[0]
  df = df.rename(columns=lambda c: c.replace(prefix + '_', ''))
  df.plot()
  ax = plt.gca()
  ax.set_title(title)
  ax.set_xlabel('log(HPD + 1)')
  if mod.output == 'sqrtRescaledAbundance':
    ax.set_ylabel('Abundance')
  else:
    ax.set_ylabel('CompSim')

  if save:
    plt.savefig(save, transparent=True, bbox_inches="tight", pad_inches=0)
  plt.show()

if __name__ == '__main__':
  matplotlib.style.use('ggplot')
  sns.set_style("darkgrid")
#pylint: disable-msg=no-value-for-parameter
  plot()
#pylint: enable-msg=no-value-for-parameter
