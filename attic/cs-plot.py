#!/usr/bin/env python3

import matplotlib
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

import click
import seaborn as sns

import projections.r2py.modelr as modelr
import projections.lu.luh2 as luh2

def inv_logit(p):
  """Returns the inverse logit function of the input."""
  return np.exp(p) / (1 + np.exp(p))

@click.command()
@click.argument('model', click.Path(dir_okay=False))
@click.option('--title', '-t', type=str,
              default='Model response vs HPD',
              help='Plot title')
@click.option('--adjust', type=float,
              default=0.001,
              help='Adjustment value for inverse logit transformation')
@click.option('--save', type=click.Path(dir_okay=False),
              help='A file to save the plot to.')
def plot(model, title, save, adjust):
  """Plot response curve of CS model versus HPD."""
  mod = modelr.load(model)
  df = pd.DataFrame(columns=tuple(luh2.LU.keys()))
  for col in df.columns:
    s = pd.Series(mod.partial({'LogHPD_s2': np.linspace(0, 11, 13),
                               'LogHPD_diff': np.linspace(0, -11, 13),
                               col: np.full((13), 1)}))
    df[col] = (inv_logit(s) - adjust) / (1 - 2 * adjust)

  df.plot()
  ax = plt.gca()
  ax.set_title(title)
  ax.set_xlabel('log(HPD + 1)')
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
