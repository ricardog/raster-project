#!/usr/bin/env python3

import click
from fnmatch import fnmatch
import matplotlib.pyplot as plt
import numpy.ma as ma
import os
import pandas as pd
from pathlib import Path
import rasterio

import pdb

@click.command()
@click.option('--npp', type=click.Path(dir_okay=False))
def worldwide(npp):
    outdir = Path(os.environ.get('OUTDIR', '/out'), 'rcp')
    df = pd.DataFrame(columns=['Year', 'Scenario', 'Mask', 'Mean'])
    mask = {}
    area = {}
    with rasterio.open(Path(outdir, 'land.tif')) as ds:
        land = ds.read(1, masked=True)
    if npp:
        with rasterio.open(npp) as ds:
            npp = ds.read(1, masked=True)
    else:
        npp = ma.empty_like(land)
        npp.mask = land.mask
    land_area = (land * npp).sum()
    masks = ('temperate', 'tropical', 'nonforested')
    for layer in masks:
        with rasterio.open(Path(outdir, f'{layer}.tif')) as ds:
            mask[layer] = ds.read(1, masked=True) * land
            area[layer] = (mask[layer] * npp).sum()
    for path in filter(lambda p: fnmatch(p.name, 'dasgupta-*-BIIAb-*.tif'),
                       outdir.iterdir()):
        print(path)
        _, scenario, what, year = path.stem.split('-')
        with rasterio.open(path) as src:
            data = src.read(1, masked=True) * npp
            df = df.append({'Year': int(year), 'Scenario': scenario,
                            'Mask': 'None',
                            'Mean': (data * land).sum() / land_area},
                           ignore_index=True)
            for mm in masks:
                df = df.append({'Year': int(year), 'Scenario': scenario,
                                'Mask': mm,
                                'Mean': ((data * mask[mm]).sum() /
                                         area[mm])},
                               ignore_index=True)
                
    df = df.sort_values(['Year', 'Scenario']).reset_index(drop=True)
    #print(df.loc[df.Scenario == 'early'])
    #print(df.loc[df.Scenario == 'late'])
    print(df.loc[df.Scenario == 'base'])
    df.to_csv('vivid-sumary.csv', index=False)

    for scenario in ('early', 'late', 'base'):
        plt.plot(df.loc[(df.Scenario == scenario) & (df.Mask == 'tropical')].Year,
                 df.loc[(df.Scenario == scenario) & (df.Mask == 'tropical')].Mean,
                 label='Tropical')
        plt.plot(df.loc[(df.Scenario == scenario) & (df.Mask == 'temperate')].Year,
                 df.loc[(df.Scenario == scenario) & (df.Mask == 'temperate')].Mean,
                 label='Temperate')
        plt.plot(df.loc[(df.Scenario == scenario) & (df.Mask == 'nonforested')].Year,
                 df.loc[(df.Scenario == scenario) & (df.Mask == 'nonforested')].Mean,
                 label='Non-forested')
        plt.plot(df.loc[(df.Scenario == scenario) & (df.Mask == 'None')].Year,
                 df.loc[(df.Scenario == scenario) & (df.Mask == 'None')].Mean,
                 label='Global', color='black', linewidth=2)
        ax = plt.gca()
        
        ax.set_ylabel('NPP-weighted Mean BII')
        ax.set_xlabel('Year')
        ax.set_title(f'Mean BII per model type ({scenario})')
        ax.legend()
        plt.savefig(f'mean-bii-{scenario}.png')
        plt.show()
    return



if __name__ == '__main__':
    worldwide()
    
