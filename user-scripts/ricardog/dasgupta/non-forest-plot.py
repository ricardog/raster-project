#!/usr/bin/env python3

import click
import os
import matplotlib.pyplot as plt
from pathlib import Path
import pandas as pd
import rasterio

from attic.cell_area import raster_cell_area
from projections.utils import data_file

import pdb

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


def do_one(scenario, df=None):
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
        carea = raster_cell_area(fds) / 1e6
    data_dir = data_file('vivid', dirname, 'spatial_files',
                         'restored_land')
    years = tuple(range(2020, 2061, 5))
    if df is None:
        df = pd.DataFrame(columns=['Scenario', 'Year', 'Forested',
                                   'Non-forested'])
    for idx, year in enumerate(years):
        data = None
        for subtype in ('mf', 'sf'):
            fname = f'{data_dir}/restored_{subtype}_{year}.tif'
            with rasterio.open(fname) as src:
                if data is None:
                    data = src.read(1, masked=True) #* carea
                else:
                    data += src.read(1, masked=True) #* carea
        in_forest = data * forest_frac
        f_frac = in_forest.sum() / data.sum()
        nf_frac = 1 - f_frac
        if idx == 0:
            acc = data
            acc_forest = in_forest
        else:
            acc += data
            acc_forest += in_forest

        #print("%s, %d, %5.3f, %5.3f" % (scenario, year, f_frac, nf_frac))
        df = df.append({'Scenario': scenario, 'Year': year,
                        'Forested': f_frac, 'Non-forested': nf_frac},
                       ignore_index=True)
    final_forest_frac = acc_forest.sum() / acc.sum()
    print('%s, %5.3f, %5.3f' % (scenario, final_forest_frac,
                                1 - final_forest_frac))
    return df

    
@click.command()
@click.argument('scenario', type=click.Choice(SCENARIOS + ('all',)))
def doit(scenario):
    print('Scenario, Forested, Non-forested')
    if scenario == 'all':
        df = None
        for scene in sorted(SCENARIOS):
            df = do_one(scene, df)
    else:
        df = do_one(scenario)
    import seaborn as sns
    sns.lineplot('Year', 'Forested', data=df, hue='Scenario', linewidth=2)
    plt.show()
    df.to_csv('restored.csv', index=False)
    return


if __name__ == '__main__':
    doit()
