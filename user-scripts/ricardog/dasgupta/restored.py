#!/usr/bin/env python3

import click
import os
from pathlib import Path
import rasterio
from projections.utils import data_file

from attic.cell_area import raster_cell_area
SCENARIOS = ('sample', 'early', 'late', 'early_075', 'early_10', 'early_125',
             'late_125', 'late_15', 'late_175', 'late_20', 'late_23',
             'late_26', 'late_29', 'base')

def downsample(in1, src, dst):
    # Convert the data from Mha to cell grid fraction (and cell area is
    # in m^2).
    dst_carea = raster_cell_area(dst) / 1e10
    area = in1
    summed = area.reshape(90, 4, 180, 4).sum(3).sum(1)
    out = (summed / dst_carea).astype('float32')
    return out


def do_one(scenario):
    if scenario == 'early':
        dirname = 'HMT_Early_Action_v3'
    elif scenario == 'early_075':
        dirname = 'HMT_Early_Action_c075'
    elif scenario == 'early_10':
        dirname = 'HMT_Early_Action_c10'
    elif scenario == 'early_125':
        dirname = 'HMT_Early_Action_c125'
    elif scenario == 'late':
        dirname = 'HMT_Late_Action_v3'
    elif scenario == 'late_125':
        dirname = 'HMT_Late_Action_c125_v5'
    elif scenario == 'late_15':
        dirname = 'HMT_Late_Action_c15_v5'
    elif scenario == 'late_175':
        dirname = 'HMT_Late_Action_c175_v5'
    elif scenario == 'late_20':
        dirname = 'HMT_Late_Action_c2_v5'
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

    with rasterio.open(Path(os.getenv('OUTDIR', '/out'),
                            'rcp', 'forested-frac.tif')) as fds:
        forest_frac = fds.read(1, masked=True)
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
                    data = src.read(1)
                    if subtype == 'mf':
                        data *= forest_frac
                    #import pdb; pdb.set_trace()
                    dst.write(downsample(data, src, dst), indexes=idx + 1)
    return

    
@click.command()
@click.argument('scenario', type=click.Choice(SCENARIOS + ('all',)))
def doit(scenario):
    if scenario == 'all':
        for scene in SCENARIOS:
            do_one(scene)
    else:
        do_one(scenario)
    return


if __name__ == '__main__':
    doit()
