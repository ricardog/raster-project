#!/usr/bin/env python3

import click
import numpy as np
import rasterio

import pdb

def find_bbox(srcs):
  cc = tuple(zip(*[src.bounds for src in srcs]))
  return (max(cc[0]), max(cc[1]), min(cc[2]), min(cc[3]))

@click.command()
@click.argument('raster', type=click.Path(dir_okay=False))
@click.argument('islands', type=click.Path(dir_okay=False))
@click.argument('mainland', type=click.Path(dir_okay=False))
@click.option('-o', '--out', type=click.Path(dir_okay=False))
def rm_overlap(raster, islands, mainland, out):
  with rasterio.open(raster) as src:
    with rasterio.open(islands) as isl:
      with rasterio.open(mainland) as main:
        bb = find_bbox((src, isl, main))
        print("Reading rasters")
        data = src.read(1, masked=True, window=src.window(*bb))
        isl_data = isl.read(1, window=isl.window(*bb))
        main_data = main.read(1, window=main.window(*bb))
        before = data.count()
        assert len(set((data.shape, isl_data.shape, main_data.shape))) == 1
        overlapped = np.logical_and(isl_data, main_data)
        data.mask = np.logical_or(data.mask, overlapped)
        after = data.count()
        print("Before : %d" % before)
        print("After  : %d" % after)
        print("Removed: %d" % (before - after))
        print("Overlap: %d" % overlapped.sum())

    if out:
      meta = src.meta.copy()
      print("Writing output [%s]" % out)
      if 'compress' not in meta:
        meta.update({'compress': 'lzw', 'predictpr': 2})
      with rasterio.open(out, 'w', **meta) as dst:
        dst.write(data.filled(), window=src.window(*bb), indexes=1)


if __name__ == "__main__":
  rm_overlap()
