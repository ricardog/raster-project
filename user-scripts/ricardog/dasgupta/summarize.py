#!/usr/bin/env python3

import click
from fnmatch import fnmatch
import matplotlib.pyplot as plt
import numpy.ma as ma
import os
import pandas as pd
from pathlib import Path
import rasterio
import seaborn as sns

import pdb

def plot_by_scenario(data):
    colors = ["windows blue", "amber", "faded green", "dusty purple"]
    palette = sns.xkcd_palette(colors)
    for scenario in data.Scenario.unique():
        subset = data.loc[data.Scenario == scenario]
        sns.lineplot('Year', 'Mean', data=subset, hue='Mask',
                     linewidth=2, palette=palette)
        ax = plt.gca()
        ax.set_ylabel('NPP-weighted Mean BII')
        ax.set_xlabel('Year')
        ax.set_title(f'Mean BII per model type ({scenario})')
        plt.savefig(f'mean-bii-{scenario}.png')
        plt.show()
    return


def plot_all(data):
    colors = ["windows blue", "amber", "dusty purple"]
    palette = sns.xkcd_palette(colors)
    data = data.loc[data.Mask == 'Global']
    sns.lineplot('Year', 'Mean', data=data, hue='Scenario',
                 linewidth=2, palette=palette)
    ax = plt.gca()
    ax.set_title('NPP-weighted Mean BII')
    ax.set_ylabel('NPP-weighted Mean BII')
    ax.set_xlabel('Year')
    plt.savefig('Figure-1.png')
    plt.show()
    return


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
                            'Mask': 'Global',
                            'Mean': (data * land).sum() / land_area},
                           ignore_index=True)
            for mm in masks:
                df = df.append({'Year': int(year), 'Scenario': scenario,
                                'Mask': mm,
                                'Mean': ((data * mask[mm]).sum() /
                                         area[mm])},
                               ignore_index=True)
                
    data = df.sort_values(['Year', 'Scenario']).reset_index(drop=True)
    #print(df.loc[df.Scenario == 'early'])
    #print(df.loc[df.Scenario == 'late'])
    print(data.loc[df.Scenario == 'base'])
    data.to_csv('vivid-summary.csv', index=False)
    #plot_by_scenario(data)
    plot_all(data)
    return



if __name__ == '__main__':
    worldwide()
    
