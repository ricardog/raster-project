#!/usr/bin/env python3
import click
from fnmatch import fnmatch
import numpy as np
import os
from pathlib import Path
import rasterio

import pdb

def vivid_dir(scenario):
    if scenario == 'early':
        return 'HMT_Early_Action_v3'
    if scenario == 'early_075':
        return 'HMT_Early_Action_c075'
    if scenario == 'early_10':
        return 'HMT_Early_Action_c10'
    if scenario == 'early_125':
        return 'HMT_Early_Action_c125'
    if scenario == 'late':
        return 'HMT_Late_Action_v3'
    if scenario == 'late_125':
        return 'HMT_Late_Action_c125_v5'
    if scenario == 'late_15':
        return 'HMT_Late_Action_c15_v5'
    if scenario == 'late_175':
        return 'HMT_Late_Action_c175_v5'
    if scenario == 'late_20':
        return 'HMT_Late_Action_c2_v5'
    if scenario == 'late_23':
        return 'HMT_Late_Action_c23_v4'
    if scenario == 'late_26':
        return 'HMT_Late_Action_c26_v4'
    if scenario == 'late_29':
        return 'HMT_Late_Action_c29_v4'
    if scenario == 'base':
        return 'HMT_Baseline_v3'
    return 'sample'
    
def fix_one(infile):
    land_file = Path(os.environ.get('OUTDIR', '/out'), 'rcp', 'land.tif')
    path = Path(infile)
    ofile = Path(path.parent, 'masked_' + path.stem + path.suffix)
    print(infile, ofile)
    with rasterio.open(land_file) as ds:
        land = ds.read(1, masked=True)
    with rasterio.open(infile) as src:
        meta = src.meta.copy()
        meta.update({'driver': 'GTiff', 'compress': 'lzw', 'predictor': 3,
                     'nodata': -9999.0})
        with rasterio.open(ofile, 'w', **meta) as dst:
            data = src.read(masked=True)
            data.mask = np.logical_or(data.mask, land.mask)
            data.set_fill_value(-9999.0)
            dst.write(data.filled() / land)
    return


@click.command()
@click.argument('scenario', type=click.Choice(('sample', 'early', 'late',
                                               'late_125', 'late_15',
                                               'late_175', 'late_20',
                                               'late_23', 'late_26',
                                               'late_29', 'base')))
def fix_mask(scenario):
    outdir = Path(os.environ.get('DATA_ROOT', '/data'),
                  'vivid', vivid_dir(scenario), 'spatial_files',
                  'restored_land')
    for path in filter(lambda p: fnmatch(p.name, 'restored_[sm]f_*.tif'),
                       Path(outdir).iterdir()):
        fix_one(path)


if __name__ == '__main__':
    fix_mask()

