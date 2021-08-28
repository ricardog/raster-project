#!/usr/bin/env python3

import click
import numpy.ma as ma
from pprint import pprint
import rasterio
from rasterio.crs import CRS
from rasterio.enums import Resampling
from rasterio.io import MemoryFile
from rasterio.profiles import DefaultGTiffProfile
import rioxarray as rxr

def write_upsample(memfile, outfile, upscale_factor):
    with memfile.open() as src:
        pprint(src.meta)
        width = int(src.width * upscale_factor)
        height = int(src.height * upscale_factor)
        out_shape = (src.count, height, width)
        data = src.read(masked=True, out_shape=out_shape,
                        resampling=Resampling.bilinear)
        xform = src.transform * src.transform.scale(
            (src.width / data.shape[-1]),
            (src.height / data.shape[-2])
        )
        kwargs = DefaultGTiffProfile(count=src.count,
                                     dtype=src.dtypes[0],
                                     nodata=src.nodata,
                                     predictor=3,
                                     crs=src.crs,
                                     transform=xform,
                                     width=width,
                                     height=height,
                                     interleave="pixel")
        with rasterio.open(outfile, "w", **kwargs) as dst:
            dst.write(data)
    return


@click.command()
@click.argument("datafile", type=click.Path(dir_okay=False))
@click.argument("outfile", type=click.Path(dir_okay=False))
@click.option("--factor", "-f", type=int, default=2)
def doit(datafile, outfile, factor):
    with rxr.open_rasterio(datafile) as src:
        crs = src.rio.crs or CRS.from_epsg(4326)
        tmp = src.tmp[0:360, :, :]
        #tmp = ma.masked_equal(tmp, tmp._FillValue)
        tmp_mean = ma.masked_invalid(ma.mean(tmp, axis=0))
        tmp_std = ma.masked_invalid(ma.std(tmp, axis=0))
        #import pdb; pdb.set_trace()
        kwargs = DefaultGTiffProfile(count=2,
                                     dtype=tmp.dtype,
                                     nodata=tmp_mean.fill_value,
                                     predictor=3,
                                     crs=crs,
                                     transform=src.rio.transform(),
                                     width=src.rio.width,
                                     height=src.rio.height,
                                     interleave="pixel")
        with MemoryFile() as memfile:
            with memfile.open(**kwargs) as dst:
                dst.write(tmp_mean.filled(), indexes=1)
                dst.write(tmp_std.filled(), indexes=2)
            write_upsample(memfile, outfile, factor)
    return


if __name__ == "__main__":
    doit()
