#!/usr/bin/env python3

import click
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


@click.command()
@click.argument('scenario', type=click.Choice(('sample', 'early', 'late',
                                               'late_23', 'late_26',
                                               'late_29', 'base')))
def doit(scenario):
    if scenario == 'early':
        dirname = 'HMT_Early_Action_v3'
    elif scenario == 'late':
        dirname = 'HMT_Late_Action_v3'
    elif scenario == 'late_23':
        dirname = 'HMT_Late_Action_c23_v4'
    elif scenario == 'late_26':
        dirname = 'HMT_Late_Action_c26_v4'
    elif scenario == 'late_29':
        dirname = 'HMT_Late_Action_c29_v4'
    elif scenario == 'base':
        dirname = 'HMT_Baseline_v3'
    else:
        dirname = 'sample'

    with rasterio.open('andy-data/historical-primary.tif') as ref:
        meta = ref.meta.copy()
    data_dir = data_file('vivid', dirname, 'spatial_files',
                         'restored_land')
    years = tuple(range(2020, 2061, 5))
    meta.update({'compression': 'lzw', 'predictor': 3, 'count': len(years)})
    for subtype in ('mf', 'sf'):
        with rasterio.open(f'andy-data/restored-{scenario}-{subtype}.tif', 'w',
                           **meta) as dst:
            for idx, year in enumerate(years):
                print(year, idx)
                fname = f'{data_dir}/restored_{subtype}_{year}.tif'
                with rasterio.open(fname) as src:
                    dst.write(downsample(src.read(1), src, dst),
                              indexes=idx + 1)
    return


if __name__ == '__main__':
    doit()
