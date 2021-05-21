#!/usr/bin/env python3
from affine import Affine
from fnmatch import fnmatch
import os
from pathlib import Path
import rasterio

import pdb


def fix_one(infile):
    path = Path(infile)
    ofile = Path(path.parent, path.stem + "-fixed" + path.suffix)
    print(infile, ofile)
    with rasterio.open(infile) as src:
        meta = src.meta.copy()
        gdal_xform = list(src.transform.to_gdal())
        gdal_xform[0] = -180
        gdal_xform[3] = 90
        xform = Affine.from_gdal(*gdal_xform)
        meta.update(
            {"driver": "GTiff", "compress": "lzw", "predictor": 3, "transform": xform}
        )
        with rasterio.open(ofile, "w", **meta) as dst:
            dst.write(src.read())
    return


def fix_bounds():
    outdir = os.path.join(
        os.environ["DATA_ROOT"], "vivid", "sample", "spatial_files", "restored_land"
    )
    for path in filter(
        lambda p: fnmatch(p.name, "restored_[ul]b_*.tif"), Path(outdir).iterdir()
    ):
        fix_one(path)


if __name__ == "__main__":
    fix_bounds()
