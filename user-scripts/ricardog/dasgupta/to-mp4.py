#!/usr/bin/env python3

import click
from fnmatch import fnmatch
import matplotlib.colors as colors

import os
from pathlib import Path
import rasterio
from projections.mp4_utils import to_mp4


def parse_fname2(fname):
    return os.path.splitext(os.path.basename(fname))[0].rsplit("_", 3)


@click.command()
@click.argument("pattern", type=str)
@click.argument("oname", type=click.Path(dir_okay=False))
@click.option("--title", "-t", type=str)
@click.option("--fps", type=int, default=10)
@click.option("--outdir", type=click.Path(file_okay=False))
def convert(pattern, oname, title, fps, outdir):
    if outdir is None:
        outdir = Path(os.environ.get("OUTDIR", "/out"), "rcp")
    else:
        outdir = Path(outdir)
    files = [path for path in outdir.iterdir() if fnmatch(path.name, pattern)]
    files = sorted(files)
    nframes = len(files)
    cnorm = colors.Normalize(vmin=0.0, vmax=1.2)
    with rasterio.open(files[0]) as src:
        data = src.read(1, masked=True)
    if not title:
        title = pattern
    for idx, img, text in to_mp4(title, oname, nframes, data, "year", fps, cnorm=cnorm):
        _, scenario, metric, year = parse_fname2(files[idx])
        with rasterio.open(files[idx]) as ds:
            data = ds.read(1, masked=True)
        img.set_array(data)
        text.set_text(year)
    return


if __name__ == "__main__":
    convert()
