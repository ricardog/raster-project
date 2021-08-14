#!/usr/bin/env python3

from pathlib import Path
from zipfile import ZipFile

import click
import numpy as np
import rasterio
from rasterio.crs import CRS
from rasterio.io import MemoryFile
from rasterio.profiles import DefaultGTiffProfile


def isfloat(dtype):
    return dtype in (np.float16, np.float32, np.float32, np.floating)


def to_tif(handle, oname, count, band):
    with MemoryFile(handle) as mfile:
        with rasterio.open(mfile) as src:
            print(f"   : {band}")
            if not oname.exists():
                crs = src.crs
                if not crs:
                    crs = CRS.from_epsg(4326)
                predictor = 3 if isfloat(src.dtypes[0]) else 2
                kwargs = DefaultGTiffProfile(count=count,
                                             dtype=src.dtypes[0],
                                             nodata=src.nodata,
                                             predictor=predictor,
                                             crs=crs,
                                             transform=src.transform,
                                             width=src.width,
                                             height=src.height,
                                             interleave="pixel")
                #import pdb; pdb.set_trace()
                with rasterio.open(oname, "w", **kwargs) as dst:
                    dst.write(src.read().squeeze(), indexes=band)
            else:
                with rasterio.open(oname, "r+") as dst:
                    dst.write(src.read().squeeze(), indexes=band)
    return


def do_decade(handle, fname):
    oname = fname.parent / fname.with_suffix(".tif")
    print(oname)
    with ZipFile(handle, "r") as zip:
        count = len(zip.filelist)
        for info in zip.filelist:
            band = int(Path(info.filename).stem.split('_')[-1])
            with zip.open(info) as zip_src:
                to_tif(zip_src, oname, count, band)
    return


def do_archive(handle, outdir):
    with ZipFile(handle, "r") as zip:
        for info in zip.filelist:
            if "giss_e2_r_" in info.filename and "tmean" in info.filename:
                print(info.filename)
                fname = outdir / Path(info.filename)
                if not fname.parent.is_dir():
                    fname.parent.mkdir()
                with zip.open(info) as ff:
                    do_decade(ff, fname)
    return


@click.command()
@click.argument("zipfile", type=click.Path(dir_okay=False))
def do_toplevel(zipfile):
    zipfile = Path(zipfile)
    outdir = zipfile.parent
    with ZipFile(zipfile, "r") as zip:
        for info in zip.filelist:
            print(info.filename)
            with zip.open(info) as handle:
                do_archive(handle, outdir)
    return


if __name__ == '__main__':
    do_toplevel()
