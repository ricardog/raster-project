#!/usr/bin/env python3

from functools import reduce

from affine import Affine
import click
import numpy as np
import rasterio
from rasterio.coords import BoundingBox, disjoint_bounds
from rasterio.crs import CRS
from rasterio.profiles import DefaultGTiffProfile


def intersection(*bounds):
    stacked = np.dstack(bounds)
    return BoundingBox(stacked[0, 0].max(), stacked[0, 1].max(),
                       stacked[0, 2].min(), stacked[0, 3].min())


@click.command()
@click.argument('in_file', type=click.Path(dir_okay=False))
@click.argument('mask_file', type=click.Path(dir_okay=False))
@click.argument('out_file', type=click.Path(dir_okay=False))
def doit(in_file, mask_file, out_file):
    with rasterio.open(in_file) as src:
        crs = src.crs or CRS.from_epsg(4326)
        with rasterio.open(mask_file) as mask:
            if disjoint_bounds(src.bounds, mask.bounds):
                raise RuntimeError("raster and mask have disjoint bounds")
            bounds = intersection(src.bounds, mask.bounds)
            xform = (Affine.translation(bounds.left,
                                        bounds.top) *
                     Affine.scale(src.res[0], src.res[1] * -1) *
                     Affine.identity())
            win = src.window(*bounds).round_offsets().round_lengths()
            data = src.read(masked=True, window=win)
            mwin = mask.window(*bounds).round_offsets().round_lengths()
            mdata = mask.read(1, masked=True, window=mwin)
            data.mask = data.mask | mdata.mask
            data.fill_value = -9999
            print("max road density: %6.2f km/km^2" % data.max())
            meta = DefaultGTiffProfile(count=src.count,
                                       dtype=np.float32,
                                       predictor=3,
                                       crs=crs,
                                       nodata=-9999,
                                       transform=xform,
                                       width=src.width,
                                       height=src.height,
                                       sparse_ok="YES",
                                       bounds=bounds,
                                       )
            with rasterio.open(out_file, 'w', **meta) as dst:
                dst.write(data.filled(), window=win)
    return


if __name__ == '__main__':
    doit()
