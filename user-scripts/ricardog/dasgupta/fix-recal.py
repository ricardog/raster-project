#!/usr/bin/env python3

import click
from fnmatch import fnmatch
import numpy as np
from pathlib import Path
import os
import rasterio

def fix_one(infile, land_file):
    path = Path(infile)
    ofile = Path(path.parent, path.stem + '-fix' + path.suffix)
    print(infile, ofile)
    with rasterio.open(land_file) as ds:
        land = ds.read(1, masked=True)
    with rasterio.open(infile) as src:
        meta = src.meta.copy()
        meta.update({'driver': 'GTiff', 'compress': 'lzw', 'predictor': 3})
        with rasterio.open(ofile, 'w', **meta) as dst:
            data = src.read(1, masked=True)
            data[np.where(~land.mask & data.mask)] = 0
            dst.write(data, indexes=1)
    return


@click.command()
@click.argument('land-file', type=click.Path(dir_okay=False))
def fix(land_file):
    outdir = os.environ['OUTDIR'] + '/rcp'
    for path in filter(lambda p: fnmatch(p.name, '*-recal.tif'),
                       Path(outdir).iterdir()):
        fix_one(path, land_file)
    return


if __name__ == '__main__':
    fix()
