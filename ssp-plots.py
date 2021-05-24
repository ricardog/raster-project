#!/usr/bin/env python
# -*- coding: utf-8 -*-
import rasterio

import click
from copy import copy
import matplotlib.pyplot as plt
import numpy as np
import numpy.ma as ma
import os
import pandas as pd
from pylru import lrudecorator

import projections.utils as utils


@lrudecorator(5)
def carea(bounds=None, height=None):
    ds = rasterio.open(
        "netcdf:%s:carea" % os.path.join(utils.luh2_dir(), "staticData_quarterdeg.nc")
    )
    if bounds is None:
        return ds.read(1, masked=True)
    win = ds.window(*bounds)
    if win[1][1] - win[0][1] > height:
        win = ((win[0][0], win[0][0] + height), win[1])
    return ds.read(1, masked=True, window=win)


@lrudecorator(10)
def cnames_df():
    cnames = pd.read_csv(
        os.path.join(utils.data_root(), "ssp-data", "country-names.csv")
    )
    return cnames


@lrudecorator(10)
def gdp_df():
    return pd.read_csv(utils.gdp_csv(), index_col=0).T


def remap(what, table, nomatch=None):
    f = np.vectorize(lambda x: table.get(x, nomatch), otypes=[np.float32])
    shape = what.shape
    tmp = f(what.reshape(-1))
    return tmp.reshape(*shape)


def parse_fname(fname):
    return os.path.splitext(os.path.basename(fname))[0].rsplit("-", 2)


def to_df(stacked, names):
    hs = {
        "fips": map(cid_to_fips, stacked[:, 0, 0]),
        "name": map(cid_to_name, stacked[:, 0, 0]),
        "ar5": map(cid_to_ar5, stacked[:, 0, 0]),
        "ratio": stacked[:, 2, -1] / stacked[:, 2, 0],
        "percent": (stacked[:, 2, -1] - stacked[:, 2, 0]) / stacked[:, 2, 0],
    }
    assert len(names) == stacked.shape[2]
    for idx in range(stacked.shape[2]):
        hs[names[idx]] = stacked[:, 2, idx]
    df = pd.DataFrame(hs, index=stacked[:, 0, 0].astype(int))
    return df


@click.command()
@click.argument("reference", type=click.Path(dir_okay=False))
@click.argument("infiles", nargs=-1, type=click.Path(dir_okay=False))
@click.option(
    "--npp",
    type=click.Path(dir_okay=False),
    help="Weight the abundance data with NPP per cell",
)
@click.option(
    "-b",
    "--band",
    type=click.INT,
    default=1,
    help="Index of band to process (default: 1)",
)
@click.option(
    "-l",
    "--log",
    is_flag=True,
    default=False,
    help="When set the data is in log scale and must be "
    + "converted to linear scale (default: False)",
)
def do_plots(infiles, band, reference, npp, log):
    refs = []
    maps = []
    titles = []
    extent = None
    if npp:
        npp_ds = rasterio.open(npp)
    with rasterio.open(reference) as ref_ds:
        for arg in infiles:
            with rasterio.open(arg) as src:
                print(arg)
                scenario, what, year = parse_fname(arg)
                win = ref_ds.window(*src.bounds)
                if win[1][1] - win[0][1] > src.height:
                    win = ((win[0][0], win[0][0] + src.height), win[1])
                ref = ref_ds.read(1, masked=True, window=win)
                if extent is None:
                    extent = (
                        src.bounds.left,
                        src.bounds.right,
                        src.bounds.bottom,
                        src.bounds.top,
                    )
                data = src.read(band, masked=True)
                if log:
                    ref = ma.exp(ref)
                    data = ma.exp(data)
                if npp:
                    npp_data = npp_ds.read(
                        1, masked=True, window=npp_ds.window(*src.bounds)
                    )
                    ref *= npp_data
                    data *= npp_data
                refs.append(ref)
                maps.append(data)
                titles.append(" ".join(scenario.upper().split("_")))

        palette = copy(plt.cm.viridis)
        palette.set_over("b", 1.0)
        palette.set_under("r", 1.0)
        # palette.set_bad('k', 1.0)
        plt.style.use("ggplot")

        params = {"axes.titlesize": "small"}
        plt.rcParams.update(params)

        fig, axes = plt.subplots(3, 2, figsize=(6, 4.5))

        idx = 0
        for row in axes:
            for ax in row:
                # ax.axis('off')
                ax.set_title(titles[idx])
                _ = ax.imshow(
                    maps[idx] / refs[idx],
                    cmap=palette,
                    vmin=0.75,
                    vmax=1.05,
                    extent=extent,
                )
                idx += 1
        # plt.colorbar(orientation='horizontal')
        fig.tight_layout()
        fig.savefig("ab-ssp-1950-2100.png")
        fig.savefig("ab-ssp-1950-2100.pdf")
        plt.show()


if __name__ == "__main__":
    do_plots()
