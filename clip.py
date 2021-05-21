#!/usr/bin/env python3

import click
import numpy as np
import numpy.ma as ma
import rasterio

import projections.raster_utils as ru


@click.command()
@click.argument("infile", type=click.Path(dir_okay=False))
@click.argument("outfile", type=click.Path(dir_okay=False))
@click.option(
    "--min",
    "a_min",
    type=float,
    default=None,
    help="Min value to clip to (default: unbounded)",
)
@click.option(
    "--max",
    "a_max",
    type=float,
    default=None,
    help="Max value to clip to (default: unbounded)",
)
@click.option(
    "--mask",
    is_flag=True,
    default=False,
    help="Mask (insted of clip) pixels outside the bounds",
)
def clip(infile, outfile, a_min=None, a_max=None, mask=False):
    ru.clip(infile, outfile, a_min, a_max, mask)


if __name__ == "__main__":
    clip()
