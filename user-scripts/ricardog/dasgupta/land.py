#!/usr/bin/env python3

from netCDF4 import Dataset
import numpy as np
import numpy.ma as ma
import rasterio
from rasterio.plot import show


def doit(in_file, out_file):
    nodata = -9999.0
    with rasterio.open(f"netcdf:{in_file}:crop") as crop_ds:
        meta = crop_ds.meta.copy()
    meta.update(
        {
            "driver": "GTiff",
            "compress": "lzw",
            "predictor": 3,
            "count": 1,
            "nodata": nodata,
            "dtype": "float32",
        }
    )
    with Dataset(in_file) as src:
        with rasterio.open(out_file, "w", **meta) as dst:
            land = np.full((dst.height, dst.width), fill_value=0, dtype="float32")
            for layer in src.variables:
                print(layer)
                if len(src.variables[layer].shape) != 3:
                    continue
                land += src.variables[layer][0, ::-1, ::]
            land2 = ma.fix_invalid(ma.masked_equal(land, 0))
            land2.set_fill_value(nodata)
            dst.write(land2.filled(), indexes=1)
    show(land2)
    return


if __name__ == "__main__":
    doit(
        "/Users/ricardog/src/eec/data/vivid/sample/spatial_files/cell.land_0.5.nc",
        "land.tif",
    )
