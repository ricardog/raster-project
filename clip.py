#!/usr/bin/env python3

import click
import numpy as np
import rasterio

import pdb

@click.command()
@click.argument('infile', type=click.Path(dir_okay=False))
@click.argument('outfile', type=click.Path(dir_okay=False))
@click.option('--min', 'a_min', type=float, default=None,
              help='Min value to clip to (default: unbounded)')
@click.option('--max', 'a_max', type=float, default=None,
              help='Max value to clip to (default: unbounded)')
def clip(infile, outfile, a_min=None, a_max=None):
  if a_min is None and a_max is None:
    print("Please specify min, max, or both")
    return
  
  with rasterio.open(infile) as src:
    with rasterio.open(outfile, 'w', **src.meta) as dst:
      for block_index, window in src.block_windows(1):
        data = src.read(masked=True, window=window)
        clipped = np.clip(data, a_min, a_max)
        dst.write(clipped, window=window)

if __name__ == '__main__':
  clip()
  
