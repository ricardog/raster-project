#!/usr/bin/env python3

import rasterio
from projections.utils import data_file

from attic.cell_area import raster_cell_area

def downsample(in1, src, dst):
    # Convert the data from Mha to cell grid fraction (and cell area is
    # in m^2).
    dst_carea = raster_cell_area(dst) / 1e10
    area = in1
    summed = area.reshape(90, 4, 180, 4).sum(3).sum(1)
    out = (summed / dst_carea).astype('float32')
    return out


def doit(scenario):
    with rasterio.open('andy-data/historical-primary.tif') as ref:
        meta = ref.meta.copy()
    data_dir = data_file('vivid', scenario, 'spatial_files',
                         'restored_land')
    years = tuple(range(2020, 2061, 5))
    meta.update({'compression': 'lzw', 'predictor': 3, 'count': len(years)})
    for bound in ('lb', 'ub'):
        with rasterio.open(f'andy-data/restored-{bound}.tif', 'w',
                           **meta) as dst:
            for idx, year in enumerate(years):
                print(year, idx)
                fname = f'{data_dir}/restored_{bound}_{year}.tif'
                with rasterio.open(fname) as src:
                    dst.write(downsample(src.read(1), src, dst),
                              indexes=idx + 1)
    return

if __name__ == '__main__':
    doit('sample')
