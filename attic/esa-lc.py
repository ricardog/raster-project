#!/usr/bin/env python3

import math

import click
import fiona
import numpy as np
import pandas as pd
import rasterio
from rasterio.io import MemoryFile
import rasterio.mask


R_MAJOR = 6378137.0000
R_MINOR = 6356752.3142


def band_area(lats):
    rlats = np.radians(lats)
    e = math.sqrt(1 - (R_MINOR / R_MAJOR) ** 2)
    zm = 1 - e * np.sin(rlats)
    zp = 1 + e * np.sin(rlats)
    c = 2 * np.arctanh(e * np.sin(rlats))
    area = np.pi * R_MINOR ** 2 * (c / (2 * e) + np.sin(rlats) / (zp * zm))
    return area


def slice_area(lats):
    area = band_area(lats)
    return np.abs(np.diff(area, 1))


def cell_area(lats, lons):
    width = lons.shape[0] - 1
    height = lats.shape[0] - 1
    slices = slice_area(lats).reshape(height, 1)
    return (np.diff(lons, 1) / 360.0).reshape(1, width) * slices


def raster_cell_area(src, full=False):
    left, bottom, right, top = src.bounds
    lats = np.linspace(top, bottom, src.height + 1)
    if full:
        lons = np.linspace(left, right, src.width + 1)
    else:
        lons = np.linspace(left, left + src.transform[0], 2)
    return cell_area(lats, lons)


def crop(src, features):
    dst_data, dst_transform = rasterio.mask.mask(src, features, crop=True)
    dst_meta = src.meta.copy()
    idx = 0 if len(dst_data.shape) == 2 else 1
    dst_meta.update(
        {
            "transform": dst_transform,
            "height": dst_data.shape[idx + 0],
            "width": dst_data.shape[idx + 1],
            "compress": "lzw",
            "predictor": 2,
        }
    )
    return dst_data, dst_meta


def calc_hist(dst, data):
    carea = raster_cell_area(dst, full=True)
    hist = np.zeros((data.shape[0], data.max() + 1), dtype=float)
    for idx in range(data.shape[0]):
        hist[idx, :] = np.bincount(
            data[idx, :, :].reshape(dst.width * dst.height),
            carea.reshape(dst.width * dst.height),
        )
    return hist


def doit(cname):
    ne_fname = (
        "/data/natural-earth/ne_10m_admin_0_countries/" "ne_10m_admin_0_countries.shp"
    )
    esa_lc_fname = (
        "/data/esacci-lc/scratch/" "ESACCI-LC-L4-LCCS-Map-300m-P1Y-1992_2015-v2.0.7.tif"
    )
    esa_lc_legend_fname = "/data/esacci-lc/scratch/" "ESACCI-LC-Legend.csv"
    print("Finding country shape")
    with fiona.open(ne_fname) as ne:
        features = [
            feat["geometry"] for feat in ne if feat["properties"]["NAME"] == cname
        ]
    print("Croping LC raster to country")
    with rasterio.open(esa_lc_fname) as esa_lc:
        dst_data, dst_meta = crop(esa_lc, features)
    with MemoryFile().open(**dst_meta) as dst:
        print("Dimensions: %d x %d" % (dst.width, dst.height))
        print("Generating histograms of LC for country")
        # dst.write(dst_data)
        hist = calc_hist(dst, dst_data)
    df = pd.DataFrame(hist.T)
    df = df[(df.T != 0).any()].drop(0)
    df.columns = range(1992, 2016)
    legend_df = pd.read_csv(esa_lc_legend_fname, sep=";")[["NB_LAB", "LCCOwnLabel"]]
    df = pd.merge(legend_df, df, left_on="NB_LAB", right_index=True).drop(
        "NB_LAB", axis=1
    )
    long_df = pd.melt(
        df,
        value_vars=tuple(range(1992, 2015)),
        id_vars="LCCOwnLabel",
        value_name="area",
        var_name="year",
    )
    return long_df


@click.command()
@click.argument("country-name", type=str)
@click.option("-percent", "-p", is_flag=True, default=False)
@click.option("--save", "-s", is_flag=True, default=False)
def lc_histo(country_name, percent, save):
    df = doit(country_name)
    if percent:
        df["area %"] = df.groupby("year").transform(lambda s: s / s.sum() * 100)
        df = df.drop("area", axis=1)
    if save:
        df.to_csv("%s-lc-hist.csv" % country_name, index=False)


if __name__ == "__main__":
    lc_histo()
