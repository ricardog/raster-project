#!/usr/bin/env python3

import click
import rasterio

import pdb


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
        data = src.read(1, masked=True)
        out = data.reshape(meta["height"], factor, meta["width"], factor).sum(3).sum(1)
        out /= factor ** 2
        out.fill_value = -9999.0
        with rasterio.open(out_file, "w", **meta) as dst:
            dst.write(out.filled(), indexes=1)

    return


if __name__ == "__main__":
    main()
