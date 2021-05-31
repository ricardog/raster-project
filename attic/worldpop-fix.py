#!/usr/bin/env python3

from affine import Affine
from pathlib import Path
import rasterio

def do_one(path):
    gdal2 = (-179.99999928, 0.0083333333, 0.0,
             83.999999664, 0.0, -0.0083333333)
    xform2 = Affine.from_gdal(*gdal2)
    with rasterio.open(path, 'r+') as ds:
        ds.transform = xform2
    return

def doit():
    pattern = 'worldpop-*.tif'
    for path in [p for p in Path('/data/worldpop').iterdir()
                 if p.match(pattern)]:
        print(path)
        do_one(path)
    return

if __name__ == '__main__':
    doit()
