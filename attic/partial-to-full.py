#!/usr/bin/env python3

import click
import numpy as np
import numpy.ma as ma
import rasterio

@click.command()
@click.argument('output', type=click.Path(dir_okay=False))
@click.argument('input', type=click.Path(dir_okay=True))
@click.argument('reference', type=click.Path(dir_okay=True))
def main(output, input, reference):
    epsilon = 1e-4
    print('Output: %s' % output)
    print('Input : %s' % input)
    print('Reference: %s' % reference)

    with rasterio.open(reference) as ref:
        meta = ref.profile
        ref_data = ref.read(1, masked=True)
        out = ma.masked_array(np.zeros_like(ref_data))
    with rasterio.open(input) as src:
        meta.update({'driver': 'GTiff', 'compress': 'lzw',
                     'predictor': 2, 'nodata': src.nodata})
        src_data = src.read(1, masked=True)
        src_bounds = src.bounds
        out.set_fill_value(src.nodata)
    with rasterio.open(output, 'w', **meta) as dst:
        if dst.crs is None or dst.crs == {}:
            dst.crs = rasterio.crs.CRS(init='epsg:4326')
        win = dst.window(*src_bounds)
        yl = round(win.row_off)
        yh = round(win.row_off + win.height)
        xl = round(win.col_off)
        xh = round(win.col_off + win.width)
        out[yl:yh, xl:xh] = np.where(src_data.mask == False, src_data,
                                     ref_data[yl:yh, xl:xh])
        out.mask = np.logical_or(ref_data.mask,
                                 np.where(ref_data >= (1.0 - epsilon),
                                          True, False))
        dst.write(out.filled(), indexes=1)
    return


if __name__ == '__main__':
    main()
