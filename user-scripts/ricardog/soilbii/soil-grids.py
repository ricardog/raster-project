#!/usr/bin/env python3

from pathlib import Path

import click
import numpy.ma as ma
import rasterio

from projutils.utils import data_file, outfn

BAND_MAP = {
    "bdod": 1,
     "clay": 2,
    "phh2o": 3,
    "soc": 4,
}


SCALE_MAP = {
    "bdod": 10,
     "clay": 10,
    "phh2o": 0.1,
    "soc": 1,
}


LIMIT_MAP = {
    "bdod": [1, 10, 56.125, 160.775],
     "clay": [2, 10, 22.5, 545],
    "phh2o": [3, 0.1, 41.5, 86],
    "soc": [4, 1, 0, 348],
}


@click.command()
@click.argument("name", type=click.Choice(["bdod", "clay", "phh2o", "soc"]))
def doit(name):
    dir_path = Path(data_file("SoilGrids", "luh2"))
    with rasterio.open(Path(dir_path,
                            "soil-grids_15-30cm_mean.tif")) as fifteen_ds:
        with rasterio.open(Path(dir_path,
                                "soil-grids_5-15cm_mean.tif")) as five_ds:
            with rasterio.open(Path(dir_path,
                                    "soil-grids_0-5cm_mean.tif")) as zero_ds:
                meta = zero_ds.meta.copy()
                meta.update({
                    "compression": "deflate",
                    "predictor": 2,
                    "count": 1,
                    "dtype": "float32",
                    "nodata": -9999,
                })
                with rasterio.open(outfn("luh2", "soil-grids",
                                         f"{name}.tif"), "w",
                                   **meta) as dst:
                    #band = BAND_MAP[name]
                    #limits = LIMIT_MAP[name]
                    band, scale, minv, maxv = LIMIT_MAP[name]
                    data = (zero_ds.read(band, masked=True) +
                            five_ds.read(band, masked=True) +
                            fifteen_ds.read(band, masked=True)
                            ) / 3
                    clip1 = ma.masked_where(data < minv, data)
                    clip2 = ma.masked_where(clip1 > maxv, clip1)
                    #import pdb; pdb.set_trace()
                    scaled = (clip2 * scale).filled(-9999).astype("float32")
                    dst.write(scaled, indexes=1)
    return


if __name__ == "__main__":
    doit()

