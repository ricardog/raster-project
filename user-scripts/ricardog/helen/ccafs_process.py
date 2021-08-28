#!/usr/bin/env python3

from pprint import pprint

import click
import numpy.ma as ma
import rasterio
from rasterio.crs import CRS
from rasterio.enums import Resampling
from rasterio.io import MemoryFile
from rasterio.profiles import DefaultGTiffProfile


def write_downsample(memfile, outfile, factor):
    with memfile.open() as src:
        #pprint(src.meta)
        width = int(src.width * factor)
        height = int(src.height * factor)
        out_shape = (src.count, height, width)
        data = src.read(masked=True, out_shape=out_shape,
                        resampling=Resampling.average)
        xform = src.transform * src.transform.scale(
            (src.width / data.shape[-1]),
            (src.height / data.shape[-2])
        )
        kwargs = DefaultGTiffProfile(count=src.count,
                                     dtype="float32",
                                     nodata=src.nodata,
                                     predictor=3,
                                     crs=src.crs,
                                     transform=xform,
                                     width=width,
                                     height=height,
                                     interleave="pixel")
        with rasterio.open(outfile, "w", **kwargs) as dst:
            dst.write(data.astype("float32"))
    return
    
@click.command()
@click.argument("infile", type=click.Path(dir_okay=False))
@click.argument("outfile", type=click.Path(dir_okay=False))
def process(infile, outfile):
    factor = 1.5
    with rasterio.open(infile) as src:
        crs = src.crs or CRS.from_epsg(4326)
        data = src.read(masked=True)
        mean = ma.mean(data / 10.0, axis=0)
        #pprint(src.meta)
        kwargs = DefaultGTiffProfile(count=1,
                                     dtype="float",
                                     nodata=mean.fill_value,
                                     predictor=3,
                                     crs=crs,
                                     transform=src.transform,
                                     width=src.width,
                                     height=src.height,
                                     interleave="pixel")
        with MemoryFile() as memfile:
            with memfile.open(**kwargs) as dst:
                dst.write(mean.filled(), indexes=1)
            write_downsample(memfile, outfile, factor)
    return


if __name__ == "__main__":
    process()



        
