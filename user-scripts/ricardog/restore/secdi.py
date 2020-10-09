#!/usr/bin/env python3

import numpy as np
import numpy.ma as ma
import rasterio

from projections.utils import outfn

def rotate(array, places):
    new_arr = np.roll(array, places, axis=0)
    new_arr[:places] = ma.zeros((new_arr[:places].shape))
    return new_arr


def gen_secdi():
    '''Generate intermediate secondary raster

    "Age" the Restore layer to calculate intermediate secondary
    fraction.  When a Restore cell fraction is 15 years old, it converts
    to intermediate secondary.  The script is straightforward because
    the Restore layer is monotonically increasing so we don't have to
    handle conversion to a third land-use class.

    '''
    print('Generating intermediate secondary raster')
    with rasterio.open(outfn('luh2', 'brazil', 'Regrowth.tif')) as src:
        meta = src.meta
        meta.update({'driver': 'GTiff', 'compress': 'lzw', 'predictor': 3})
        data = src.read(masked=True)
        out = ma.empty_like(data)
        for idx in range(out.shape[0]):
            out[idx, :, :] = data[0:idx + 1, :, :].sum(axis=0)
        out = rotate(out, 3)
        out.mask = data.mask
        with rasterio.open(outfn('luh2', 'brazil', 'secdi.tif'), 'w',
                           **meta) as dst:
            dst.write(out.filled())
    print('done')
    return


if __name__ == '__main__':
    gen_secdi()
