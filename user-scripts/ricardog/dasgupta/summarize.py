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

def name_to_short(indicator):
    if indicator == 'BIIAb':
        return 'BII', 'bii'
    if indicator == 'CompSimAb':
        return 'CompSim', 'cs-ab'
    if indicator == 'Abundance':
        return 'Abundance', 'ab'
    if indicator == 'Abundance-te':
        return 'Temperate Abundance', 'ab-te'
    if indicator == 'Abundance-tr':
        return 'Tropical Abundance', 'ab-tr'
    if indicator == 'Abundance-nf':
        return 'Non-forest Abundance', 'ab-nf'
    return None, None
    
def plot_by_scenario(data, indicator, npp):
    t_ind, f_ind = name_to_short(indicator)
    if npp is None:
        npp_text = ' '
    else:
        npp_text = 'NPP-weighted '

    colors = ["windows blue", "amber", "faded green", "dusty purple"]
    palette = sns.xkcd_palette(colors)
    for scenario in data.Scenario.unique():
        subset = data.loc[data.Scenario == scenario]
        sns.lineplot('Year', 'Mean', data=subset, hue='Mask', style='Mask',
                     linewidth=2, palette=palette)
        ax = plt.gca()
        ax.set_ylabel(f'Mean {npp_text}{t_ind}')
        ax.set_xlabel('Year')
        ax.set_title(f'Mean {npp_text}{t_ind} per biome ({scenario})')
        plt.savefig(f'mean-{f_ind}-{scenario}.png')
        plt.show()
        plt.close()
    return


def plot_all(data, indicator, npp):
    t_ind, f_ind = name_to_short(indicator)
    if npp is None:
        npp_text = ' '
    else:
        npp_text = 'NPP-weighted '

    colors = ["windows blue", "amber", "dusty purple"]
    colors = ["windows blue", "amber", "faded green", "dusty purple",
              "scarlet"]
    palette = sns.xkcd_palette(colors)
    data = data.loc[data.Mask == 'Global']
    sns.lineplot('Year', 'Mean', data=data, hue='Scenario',
                 linewidth=2, palette=palette)
    ax = plt.gca()
    ax.set_title(f'Mean {npp_text}{t_ind}')
    ax.set_ylabel(f'Mean {npp_text}{t_ind}')
    ax.set_xlabel('Year')
    plt.savefig('Figure-1.png')
    plt.show()
    plt.close()
    return


@click.command()
@click.option('--npp', type=click.Path(dir_okay=False))
@click.option('--indicator', '-i', type=click.Choice(('BIIAb', 'Abundance',
                                                      'CompSimAb',
                                                      'Abundance-nf')),
              default='BIIAb')
def worldwide(npp, indicator):
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
    #outdir = Path(os.environ.get('OUTDIR', '/out'), 'rcp', 'nohpd-model')
    for path in filter(lambda p: fnmatch(p.name,
                                         f'dasgupta-*-{indicator}-20*.tif'),
                       outdir.iterdir()):
        print(path)
        _, scenario, _ = path.stem.split('-', 2)
        _, year = path.stem.rsplit('-', 1)
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
    #print(data.loc[df.Scenario == 'base'])
    data.to_csv('vivid-summary.csv', index=False)
    plot_by_scenario(data, indicator, npp)
    plot_all(data, indicator, npp)
    return



if __name__ == '__main__':
    worldwide()
    
