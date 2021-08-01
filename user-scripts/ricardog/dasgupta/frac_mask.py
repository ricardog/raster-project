#!/usr/bin/env python3

import math

import click
import rasterio
from rasterio.coords import BoundingBox


def round(left, bottom, top, right, res):
    def round_down(x, a):
        return math.floor(x / a) * a

    def round_up(x, a):
        return math.ceil(x / a) * a

    def round_to_inf(x, a):
        if a * x < 0:
            return round_down(x, a)
        return round_up(x, a)
    return BoundingBox(round_to_inf(left, res[0]),
                       round_to_inf(bottom, res[1]),
                       round_to_inf(top, res[0]),
                       round_to_inf(right, res[1])
                       )


@click.command()
@click.argument("factor", type=int)
@click.argument("in-file", type=click.Path(dir_okay=False))
@click.argument("out-file", type=click.Path(dir_okay=False))
def main(factor, in_file, out_file):
    with rasterio.open(in_file) as src:
        meta = src.meta.copy()
        meta["width"] //= factor
        meta["height"] //= factor
        meta["transform"] *= src.transform.scale(factor)
        meta["nodata"] = -9999.0
        bounds = round(*src.bounds, (meta['transform'].a * factor,
                                     meta['transform'].e * factor))
        win = src.window(*bounds)
        width = int(win.width // factor)
        height = int(win.height // factor)
        data = src.read(1, masked=True, window=win, boundless=True)
        out = data.reshape(height, factor, width, factor).sum(3).sum(1)
        out /= factor ** 2
        out.fill_value = -9999.0
        with rasterio.open(out_file, "w", **meta) as dst:
            dst.write(out.filled(), indexes=1)

    return


if __name__ == "__main__":
    main()
