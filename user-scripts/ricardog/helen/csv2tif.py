#!/usr/bin/env python3

from io import BytesIO
from pprint import pprint

import click
import geopandas as gpd
import numpy as np
import numpy.ma as ma
import rasterio
from rasterio.crs import CRS
from rasterio.io import MemoryFile
from rasterio.profiles import DefaultGTiffProfile
from shapely import wkb, wkt


def parse(s):
    return wkb.loads(s, hex=True)


def read_csv(fname, col='st_astext'):
    #col = "geom"
    print("reading csv file")
    df = gpd.read_file(fname)
    if col == "geom":
        df.geometry = df[col].apply(parse)
    else:
        df.geometry = df[col].apply(wkt.loads)
    del df[col]
    df["lat"] = df.geometry.y
    df["lon"] = df.geometry.x
    df = df[df.lon <= 180.0]
    return df.sort_values(by=["lat", "lon"], axis=0, ascending=[False, True])


def write_xyz(df):
    print("writing xyz buffer")
    buf = BytesIO()
    data = df[["lon", "lat", "sum"]]
    data.to_csv(buf, index=False, header=False, sep=" ")
    buf.seek(0)
    return buf


def to_tif(buf, output, mask):
    print("parsing xyz buffer")
    with MemoryFile(buf) as memfile:
        with memfile.open() as src:
            pprint(src.meta)
            data = src.read(1, masked=True)
            if mask:
                with rasterio.open(mask) as mask_ds:
                    win = mask_ds.window(*src.bounds)
                    mdata = mask_ds.read(1, window=win)
            odata = np.where(mdata == 1, -9999,
                                np.where(data.filled() == src.nodata,
                                         0, data))
            out_data = ma.masked_where(odata == -9999, odata)
            kwargs = DefaultGTiffProfile(count=1,
                                         dtype="float32",
                                         nodata=-9999,
                                         predictor=3,
                                         crs=CRS.from_epsg(4326),
                                         transform=src.transform,
                                         width=src.width,
                                         height=src.height,
                                         interleave="pixel"
                                         )
            with rasterio.open(output, "w", **kwargs) as dst:
                dst.write(out_data, indexes=1)
    return


@click.command()
@click.argument("filename", type=click.Path(dir_okay=False))
@click.argument("output", type=click.Path(dir_okay=False))
@click.option("--mask", "-m", type=click.Path(dir_okay=False))
def doit(filename, output, mask):
    df = read_csv(filename)
    buf = write_xyz(df)
    to_tif(buf, output, mask)
    return


if __name__ == "__main__":
    doit()
    
x
