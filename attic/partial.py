#!/usr/bin/env python

import click
import matplotlib
import matplotlib.pyplot as plt
#matplotlib.style.use('ggplot')

import numpy as np
import pandas as pd

from projections.pd_utils import load_pandas
import projections.modelr as modelr

LU2 = {'annual': 'c3ann + c4ann',
      'nitrogen': 'c3nfx',
      'pasture': 'pastr',
      'perennial': 'c3per + c4per',
      'primary': 'primf + primn',
      'rangelands': 'range',
      'timber': '0',
      'urban': 'urban',
      'young_secondary': 'secdy',
      'intermediate_secondary': 'secdi',
      'mature_secondary': 'secdm',
}

LU = {'cropland': 'cropland',
      'pasture': 'pastr',
      'primary': 'primf + primn',
      'urban': 'urban',
      'secondary': 'secdy',
}

@click.command()
@click.argument('model-file', type=click.Path(dir_okay=False))
@click.option('-m', '--max-x', type=float, default=1.2)
@click.option('-s', '--steps', type=int, default=20)
def main(model_file, max_x=1.2, steps=20):
  mod = modelr.load(model_file)
  mod.intercept

  out = {}
  for lu in LU.keys():
    out[lu] = np.exp(mod.partial({'logHPD_rs': np.linspace(0, max_x, steps),
                           lu: np.full(steps, 1.0),
                           lu + '_intense': np.full(steps, 0.04),
                           lu + '_light': np.full(steps, 0.07),
                           lu + '_minimal': np.full(steps, 0.35)
    }))
  df = pd.DataFrame(out, index=np.linspace(0, max_x, steps))
  print(df)

  df.plot()
  ax.set_title('')
  ax.set_ylabel('Species Richness')
  ax.set_xlabel('log(HPD + 1) [rescaled by 10.02083]')
  #ax.xaxis.set_major_locator(plt.NullLocator())
  plt.savefig('log-abund.png')
  plt.show()

if __name__ == '__main__':
  main()

