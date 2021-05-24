#!/usr/bin/env python
# -*- coding: utf-8 -*-

from copy import copy
import itertools
import json
import os
import re

import fiona
import matplotlib.colors as colors
import matplotlib.pyplot as plt
import numpy as np
import numpy.ma as ma
import pandas as pd

import click
from pylru import lrudecorator
import rasterio

import projections.utils as utils


def replacer(source, target, replacement, replacements=None):
    return replacement.join(source.rsplit(target, replacements))


@lrudecorator(5)
def carea(bounds=None, height=None):
    with rasterio.open(utils.luh2_static("carea")) as ds:
        if bounds is None:
            return ds.read(1, masked=True)
        return ds.read(1, masked=True, window=ds.window(*bounds))


@lrudecorator(5)
def tarea(bounds=None, height=None):
    area = carea(bounds, height)
    ice_ds = rasterio.open(utils.luh2_static("icwtr"))
    if bounds is None:
        ice = ice_ds.read(1, masked=True)
    else:
        win = ice_ds.window(*bounds)
        ice = ice_ds.read(1, masked=True, window=win)
    return area * (1 - ice)


@lrudecorator(10)
def cnames_df():
    cnames = pd.read_csv(
        os.path.join(utils.data_root(), "ssp-data", "country-names.csv")
    )
    return cnames


@lrudecorator(10)
def gdp_df(fname=None):
    if fname is None:
        fname = utils.gdp_csv()
    return pd.read_csv(fname, index_col=0).T


def gdp(year, fips=None):
    if fips:
        return gdp_df().loc[fips, year]
    else:
        return gdp_df().loc[:, year]


@lrudecorator(10)
def wjp_df():
    df = pd.read_excel(utils.wjp_xls(), sheet_name=5, index_col=0).T
    df = pd.merge(
        df,
        cnames_df().loc[:, ["fips", "iso3c"]],
        left_on="Country Code",
        right_on="iso3c",
    )
    df.set_index("fips", inplace=True)
    return df


def wjp(attrs):
    return wjp_df().loc[:, attrs]


@lrudecorator(10)
def energy_c_df():
    df = pd.read_csv(utils.energy_c_csv())
    del df["Unnamed: 0"]
    df[df == "--"] = np.nan
    return df


def cid_to_x(cid, x):
    if cid == 736:
        cid = 729
    df = cnames_df()
    row = df[df.un == cid]
    if not row.empty:
        return row[x].values[0]
    return str(int(cid))


def cid_to_fips(cid):
    return cid_to_x(cid, "fips")


def cid_to_name(cid):
    return cid_to_x(cid, "country.name.en")


def cid_to_ar5(cid):
    return cid_to_x(cid, "ar5")


def cid_to_iso3(cid):
    return cid_to_x(cid, "iso3c")


def sum_by(ccode, data):
    df = pd.DataFrame({"idx": ccode.reshape(-1), "data": data.reshape(-1)}).dropna()
    agg = df.groupby(["idx"], sort=False).sum()
    return np.column_stack((agg.index.values.astype(int), agg.values))


def sum_by2(ccode, data, weights):
    dd = data * weights
    dd.mask = np.logical_or(data.mask, ccode.mask)
    return sum_by(ccode, dd)


def mean_by(idx, data):
    assert idx.shape == data.shape
    return np.bincount(idx, weights=data)


def weighted_mean_by_country(ccode, data, weights):
    dd = data * weights
    dd.mask = np.logical_or(data.mask, ccode.mask)
    save_mask = ccode.mask
    ccode.mask = ma.getmask(dd)
    ccode_idx = ccode.compressed().astype(int)
    ccode.mask = save_mask
    sums = mean_by(ccode_idx, dd.compressed())
    ncells = np.bincount(ccode_idx)
    idx = np.where(ncells > 0)
    carea = ncells[idx]
    return np.column_stack((idx[0].astype(int), carea, sums[idx] / carea))


def remap(what, table, nomatch=None):
    f = np.vectorize(lambda x: table.get(x, nomatch), otypes=[np.float32])
    shape = what.shape
    tmp = f(what.reshape(-1))
    return tmp.reshape(*shape)


def gen_mp4(oname, stack, ccode, title="", captions=None):
    from projections.mp4_utils import to_mp4

    all_max = stack[:, 2, :].max()
    all_min = stack[:, 2, :].min()
    cnorm = colors.Normalize(vmin=all_min, vmax=all_max)
    cmap = dict((k, v) for k, v in itertools.izip(stack[:, 0, 0], stack[:, 2, 0]))
    data = remap(ccode, cmap, ccode.fill_value)
    if captions is None:
        captions = tuple(itertools.repeat("", stack.shape[2]))
    elif len(captions) != stack.shape[2]:
        print("Error: not enough captions for all frames")
        return
    for idx, img, text in to_mp4(
        title, oname, stack.shape[2], data, text="LogAbund", fps=10, cnorm=cnorm
    ):
        cmap = dict(
            (k, v) for k, v in itertools.izip(stack[:, 0, idx], stack[:, 2, idx])
        )
        img.set_array(remap(ccode, cmap, ccode.fill_value))
        text.set_text(captions[idx])


def parse_fname(fname):
    m = re.search(
        r"([a-zA-Z0-9.]+)-([a-zA-Z_]+)-([0-9]{4})\.tif$", os.path.basename(fname)
    )
    if m:
        return int(m.group(3))
    return os.path.splitext(os.path.basename(fname))[0]


def parse_fname2(fname):
    return os.path.splitext(os.path.basename(fname))[0].rsplit("-", 2)


def printit(stacked):
    print("%4s %8s %8s %6s" % ("fips", "start", "end", "%"))
    for idx in range(stacked.shape[0]):
        print(
            "%4s %8.2f %8.2f %6.2f%%"
            % (
                cid_to_fips(stacked[idx, 0, 0]),
                stacked[idx, 2, 0],
                stacked[idx, 2, -1],
                (100.0 * stacked[idx, 2, -1] / stacked[idx, 2, 0]),
            )
        )


def to_df(stacked, names):
    hs = {
        "id": stacked[:, 0, 0].astype(int),
        "fips": tuple(map(cid_to_fips, stacked[:, 0, 0])),
        "name": tuple(map(cid_to_name, stacked[:, 0, 0])),
        "ar5": tuple(map(cid_to_ar5, stacked[:, 0, 0])),
        "iso3": tuple(map(cid_to_iso3, stacked[:, 0, 0])),
        "ratio": stacked[:, 2, -1] / stacked[:, 2, 0],
        "percent": (stacked[:, 2, -1] - stacked[:, 2, 0]) / stacked[:, 2, 0],
        "cells": stacked[:, 1, 0].astype(int),
    }
    assert len(names) == stacked.shape[2]
    for idx in range(stacked.shape[2]):
        hs[names[idx]] = stacked[:, 2, idx]
    df = pd.DataFrame(hs, index=stacked[:, 0, 0].astype(int))
    return df


def to_df2(stacked, names):
    hs = {
        "fips": tuple(map(cid_to_fips, stacked[:, 0, 0])),
        "name": tuple(map(cid_to_name, stacked[:, 0, 0])),
        "ar5": tuple(map(cid_to_ar5, stacked[:, 0, 0])),
    }
    assert len(names) == stacked.shape[2]
    for idx in range(stacked.shape[2]):
        hs[names[idx]] = stacked[:, 1, idx]
    df = pd.DataFrame(hs, index=stacked[:, 0, 0].astype(int))
    return df


def read_rasters(country_file, scale_ds, band, infiles):
    stack = []
    area = None
    scale_res = None
    with rasterio.open(country_file) as cc_ds:
        for arg in infiles:
            with rasterio.open(arg) as src:
                win = cc_ds.window(*src.bounds)
                ccode = cc_ds.read(1, masked=True, window=win)
                ccode = ma.masked_equal(ccode, -99)
                data = src.read(band, masked=True)
                if scale_ds:
                    data *= scale_ds.read(
                        1, masked=True, window=scale_ds.window(*src.bounds)
                    )
                res = weighted_mean_by_country(ccode, data, carea(src.bounds))
                if area is None:
                    ice_ds = rasterio.open(utils.luh2_static("icwtr"))
                    ice = ice_ds.read(1, window=ice_ds.window(*src.bounds))
                    area = ma.MaskedArray(carea(src.bounds) * (1 - ice))
                    area.mask = np.where(ice == 1, True, False)
                    if scale_ds:
                        scale_data = scale_ds.read(
                            1, masked=True, window=scale_ds.window(*src.bounds)
                        )
                        scale_res = weighted_mean_by_country(
                            ccode, scale_data, carea(src.bounds)
                        )
                stack.append(res)
                print(
                    "%40s: %8.2f / %8.2f"
                    % (os.path.basename(arg), res[:, 2].max(), res[:, 2].min())
                )
    stacked = np.dstack(stack)
    names = tuple(map(parse_fname, infiles))
    return to_df(stacked, names), scale_res


@click.group(invoke_without_command=True)
@click.pass_context
def cli(ctx):
    if ctx.invoked_subcommand is None:
        click.echo("I was invoked without subcommand")
    else:
        click.echo("I am about to invoke %s" % ctx.invoked_subcommand)


@cli.command()
@click.argument("country-file", type=click.Path(dir_okay=False))
@click.argument("infiles", nargs=-1, type=click.Path(dir_okay=False))
@click.option(
    "--npp",
    type=click.Path(dir_okay=False),
    help="Weight the abundance data with NPP per cell",
)
@click.option(
    "--vsr",
    type=click.Path(dir_okay=False),
    help="Weight the richness data with vertebrate richness per cell",
)
@click.option(
    "-b",
    "--band",
    type=click.INT,
    default=1,
    help="Index of band to process (default: 1)",
)
@click.option(
    "--mp4",
    type=click.Path(dir_okay=False),
    help="Generate a video (in mp4 format) of the by country"
    + "weighted mean (default: False)",
)
@click.option(
    "-l",
    "--log",
    is_flag=True,
    default=False,
    help="When set the data is in log scale and must be "
    + "converted to linear scale (default: False)",
)
def countrify(infiles, band, country_file, npp, vsr, mp4, log):
    stack = []
    maps = []
    extent = None
    area = None
    if npp:
        npp_ds = rasterio.open(npp)
    if vsr:
        vsr_ds = rasterio.open(vsr)
    with rasterio.open(country_file) as cc_ds:
        for arg in infiles:
            with rasterio.open(arg) as src:
                win = cc_ds.window(*src.bounds)
                ccode = cc_ds.read(1, masked=True, window=win)
                ccode = ma.masked_equal(ccode, -99)
                if extent is None:
                    extent = (
                        src.bounds.left,
                        src.bounds.right,
                        src.bounds.bottom,
                        src.bounds.top,
                    )
                data = src.read(band, masked=True)
                if log:
                    data = ma.exp(data)
                if npp:
                    npp_data = npp_ds.read(
                        1, masked=True, window=npp_ds.window(*src.bounds)
                    )
                    data *= npp_data
                if vsr:
                    vsr_data = vsr_ds.read(
                        1, masked=True, window=vsr_ds.window(*src.bounds)
                    )
                    data *= vsr_data
                res = weighted_mean_by_country(
                    ccode, data, carea(src.bounds, src.height)
                )
                if area is None:
                    ice_ds = rasterio.open(utils.luh2_static("icwtr"))
                    ice = ice_ds.read(1, window=ice_ds.window(*src.bounds))
                    area = ma.MaskedArray(carea(src.bounds, src.height))
                    area.mask = np.where(ice == 1, True, False)
                    intercept = np.exp(3.477987) * area
                    if npp:
                        npp_data = npp_ds.read(
                            1, masked=True, window=npp_ds.window(*src.bounds)
                        )
                        intercept *= npp_data
                    if vsr:
                        vsr_data = vsr_ds.read(
                            1, masked=True, window=vsr_ds.window(*src.bounds)
                        )
                        intercept *= vsr_data

                # res = weighted_mean_by_country(ccode, data, 1)
                stack.append(res)
                maps.append(data)
                print(
                    "%40s: %8.2f / %8.2f"
                    % (os.path.basename(arg), res[2, :].max(), res[2, :].min())
                )
        stacked = np.dstack(stack)
        names = tuple(map(parse_fname, infiles))
        df = to_df(stacked, names)

        ratio = maps[-1] / maps[0]
        a = ma.where(ratio > 1.05)
        b = ma.where(ratio < 0.85)
        w = ma.where((ratio >= 0.85) & (ratio <= 1.05))
        area.mask = ratio.mask

        above = ma.sum(area[a])
        below = ma.sum(area[b])
        within = ma.sum(area[w])
        total = ma.sum(area)
        print(
            "Area: %6.4f / %6.4f / %6.4f"
            % (above / total, below / total, within / total)
        )

        total1950 = ma.sum(ma.masked_invalid(maps[0] * area))
        # newbold-a intercept is 4.63955498
        pristine = ma.sum(intercept)

        npp_df = pd.DataFrame(
            weighted_mean_by_country(ccode, npp_data, area),
            columns=["ID", "Cells", "npp_mean"],
        )
        npp_df.index = npp_df.ID

        print("loss w.r.t. primary: %6.4f" % (total / pristine))
        print("loss w.r.t. 1950   : %6.4f" % (total / total1950))
        gdp_1950 = gdp([1950, 1970, 2010])
        gdp_1950.columns = ("gdp_1950", "gdp_1970", "gdp_2014")
        merged = pd.merge(
            df, gdp_1950, left_on="fips", right_index=True, sort=False
        )  # .sort_values(by=['gdp'])
        merged = merged.merge(npp_df, how="inner", left_index=True, right_index=True)
        merged["ab_delta"] = np.log(merged[2014] / merged[1970])

        title = u"Abundance gain (loss) 1950 — 2014"
        idx = 0
        syms = ["x", "o", "+", "v", "^", "*"]
        cols = ["r", "g", "blue", "b", "purple", "y"]

        plt.style.use("ggplot")
        fig1 = plt.figure(figsize=(6, 4))
        ax1 = plt.gca()
        for name, group in merged.groupby("ar5"):
            ax1.plot(
                group.pindex,
                group.ratio,
                label=name,
                marker=syms[idx],
                linestyle="",  # ms=11,
                c=cols[idx],
            )
            idx += 1
        ax1.plot([0, len(df)], [1.0, 1.0], color="k", linestyle="-", linewidth=2)

        ax1.set_title(title)
        ax1.set_ylabel("Mean area weighted abundance gain (%)")
        ax1.set_xlabel("Country sorted by GDP (1950)")
        ax1.xaxis.set_major_locator(plt.NullLocator())
        ax1.legend()
        fig1.savefig("ab-by-gdp.png")
        fig1.savefig("ab-by-gdp.pdf")
        plt.show()

        palette = copy(plt.cm.viridis)
        palette.set_over("w", 1.0)
        palette.set_under("r", 1.0)
        palette.set_bad("k", 1.0)

        fig2 = plt.figure(figsize=(6, 4))
        ax2 = plt.gca()
        title = u"Abundance ratio 2014 / 1950"
        ax2.set_title(title)
        ax2.axis("off")
        _ = plt.imshow(
            maps[-1] / maps[0], cmap=palette, vmin=0.75, vmax=1.05, extent=extent
        )
        plt.colorbar(orientation="horizontal")
        fig2.savefig("ab-1950-2010.png")
        fig2.savefig("ab-1950-2010.pdf")
        plt.show()

        if mp4:
            gen_mp4(mp4, stacked, ccode)


@cli.command()
@click.argument("country-file", type=click.Path(dir_okay=False))
@click.argument("infiles", nargs=-1, type=click.Path(dir_okay=False))
@click.option(
    "--npp",
    type=click.Path(dir_okay=False),
    help="Weight the abundance data with NPP per cell",
)
@click.option(
    "--vsr",
    type=click.Path(dir_okay=False),
    help="Weight the richness data with vertebrate richness per cell",
)
@click.option(
    "-b",
    "--band",
    type=click.INT,
    default=1,
    help="Index of band to process (default: 1)",
)
@click.option(
    "-o", "--out", type=click.File("w"), help="A file to write the merged data to"
)
def export(infiles, band, country_file, npp, vsr, out):
    if npp:
        scale_ds = rasterio.open(npp)
    elif vsr:
        scale_ds = rasterio.open(vsr)
    else:
        scale_ds = None
    types = list(set((x[0], x[1]) for x in map(parse_fname2, infiles)))
    assert len(types) == 1
    scenario = types[0][0]
    metric = types[0][1]
    print("%s -- %s" % (scenario, metric))
    df, scale_res = read_rasters(country_file, scale_ds, band, infiles)

    del df["percent"]
    del df["ratio"]

    df.rename(
        columns=dict(
            (x, metric + "_" + str(x))
            for x in filter(lambda x: isinstance(x, int), df.columns)
        ),
        inplace=True,
    )
    if npp:
        df["npp_mean"] = scale_res[:, 2]
    if vsr:
        df["vsr_mean"] = scale_res[:, 2]

    #
    # Fix a few mising FIPS codes.
    #
    df.loc[df.name == "South Sudan", "fips"] = "OD"
    df.loc[df.name == "Curaçao", "fips"] = "UC"
    df.loc[df.name == "Åland Islands", "fips"] = "AX"  # ISO 3166 code

    #
    # Compute the fraction of land that was primary in 1950
    #
    with rasterio.open(country_file) as cc_ds:
        prim_fn = os.path.join(utils.outdir(), "luh2", "historical-primary-1950.tif")
        with rasterio.open(prim_fn) as src:
            ccode = cc_ds.read(1, masked=True, window=cc_ds.window(*src.bounds))
            ccode = ma.masked_equal(ccode, -99)
            with rasterio.open(utils.luh2_static("icwtr")) as ice_ds:
                ice = ice_ds.read(1, window=ice_ds.window(*src.bounds))
            prim = src.read(1, masked=True)
            area = ma.MaskedArray(carea(src.bounds) * (1 - ice), mask=prim.mask)
        prim_by_cc = sum_by2(ccode, prim, area)
        area_by_cc = sum_by(ccode, area)
        prim_df = pd.DataFrame(
            {"Primary": prim_by_cc[:, 1], "Area": area_by_cc[:, 1]},
            index=prim_by_cc[:, 0].astype(int),
        ).sort_index()
        prim_df["prim_ratio"] = prim_df.Primary / prim_df.Area
        prim_df = prim_df.apply(pd.to_numeric)
        merged = df.merge(prim_df, how="left", left_index=True, right_index=True)

    #
    # Read GDP data.
    # Source: https://www.rug.nl/ggdc/historicaldevelopment/maddison/
    # For this source I had to slightly massage the data (see the
    # cleanup-maddison.py script) which extracts data since 1950 and
    # adds a FIPS attribute to each country.
    #
    merged2 = merged.merge(
        gdp_df().add_prefix("GDP_"), how="left", left_on="fips", right_index=True
    )

    #
    # Read Rule of Law data (World Justice Project).
    # Source: http://data.worldjusticeproject.org/#table
    #
    wjp_attrs = [
        "WJP Rule of Law Index: Overall Score",
        "Factor 1: Constraints on Government Powers",
        "Factor 2: Absence of Corruption",
        "Factor 3: Open Government ",
        "Factor 4: Fundamental Rights",
        "Factor 5: Order and Security",
        "Factor 6: Regulatory Enforcement",
        "Factor 7: Civil Justice",
        "Factor 8: Criminal Justice",
    ]
    wjp_data = wjp(wjp_attrs)
    wjp_data[wjp_attrs] = wjp_data[wjp_attrs].apply(pd.to_numeric)
    merged3 = merged2.merge(wjp_data, how="left", left_on="fips", right_index=True)

    #
    # Read human population density data and compute
    # human population (per year).
    # Source: projections
    #
    hp_stk = []
    years = []
    with rasterio.open(country_file) as cc_ds:
        for fname in infiles:
            fname = replacer(fname, metric, "hpd", 1)
            year = parse_fname(fname)
            years.append(year)
            print("hpd: ", year)
            with rasterio.open(fname) as src:
                hpd = src.read(1, masked=True)
                hp = hpd * carea(src.bounds)
                ccode = cc_ds.read(1, masked=True, window=cc_ds.window(*src.bounds))
                ccode = ma.masked_equal(ccode, -99)
                hp_stk.append(sum_by(ccode, hp))
        hp_df = to_df2(np.dstack(hp_stk), ["HP_" + str(yy) for yy in years])
        del hp_df["fips"], hp_df["name"], hp_df["ar5"]
        merged4 = merged3.merge(hp_df, how="left", left_index=True, right_index=True)
        merged4["CID"] = merged4.index

    #
    # Read Energy consumption data.
    # Source: https://www.eia.gov/beta/international/
    #
    energy = energy_c_df()
    energy.rename(
        columns=dict((x, "BTU_" + x) for x in energy.columns[2:]), inplace=True
    )
    del energy["Units"]
    merged5 = merged4.merge(energy, how="left", left_on="name", right_on="Country")

    #
    # Combine energy consumption and human population into
    # energy consumption per capita.
    #
    hp_cols = [col for col in merged5.columns if "HP_" in col]
    hp_years = [int(x[-4:]) for x in hp_cols]
    btu_cols = [col for col in merged5.columns if "BTU_" in col]
    btu_years = [int(x[-4:]) for x in btu_cols]
    years = sorted(set(hp_years).intersection(set(btu_years)))
    for year in years:
        yy = str(year)
        print("BTU / person: " + yy)
        merged5["BTU_PC_" + yy] = (
            merged5["BTU_" + yy].astype(float) * 1e6 / merged5["HP_" + yy]
        )

    #
    # Read economic complexity index (ECI) data and add it to DF.
    # Source: https://atlas.media.mit.edu/en/
    #
    cnames = cnames_df()
    eci = pd.read_csv(utils.eci_csv())
    eciw = eci.pivot(index="Country", values="ECI", columns="Year")
    eciw = eciw.add_prefix("ECI_")
    eci_plus = eciw.merge(
        cnames.loc[:, ["country.name.en", "un"]],
        how="inner",
        left_index=True,
        right_on="country.name.en",
    )
    eci_plus.index = eci_plus.un.astype(int)
    eci_plus.index.name = None
    del eci_plus["un"]
    del eci_plus["country.name.en"]
    merged6 = merged5.merge(eci_plus, how="left", left_on="CID", right_index=True)

    if out:
        merged6.to_csv(out.name, index=False, encoding="utf-8")


@cli.command()
@click.argument("country-file", type=click.Path(dir_okay=False))
@click.argument("infiles", nargs=-1, type=click.Path(dir_okay=False))
@click.option(
    "--gdp",
    type=click.Path(dir_okay=False),
    default=utils.gdp_csv(),
    help="CSV file with per capital GDP data.",
)
@click.option(
    "--scale",
    type=click.Path(dir_okay=False),
    help="Weight the metric values with a per cell factor, "
    "e.g. NPP na dvertebrate species richness.",
)
@click.option(
    "-b",
    "--band",
    type=click.INT,
    default=1,
    help="Index of band to process (default: 1)",
)
@click.option(
    "-o", "--out", type=click.File("w"), help="A file to write the merged data to"
)
def export2(infiles, band, country_file, gdp, scale, out):
    if scale:
        scale_ds = rasterio.open(scale)
    else:
        scale_ds = None
    types = list(set((x[0], x[1]) for x in map(parse_fname2, infiles)))
    assert len(types) == 1
    scenario = types[0][0]
    metric = types[0][1]
    print("%s -- %s" % (scenario, metric))
    df, scale_res = read_rasters(country_file, scale_ds, band, infiles)

    del df["percent"]
    del df["ratio"]

    df.rename(
        columns=dict(
            (x, metric + "_" + str(x))
            for x in filter(lambda x: isinstance(x, int), df.columns)
        ),
        inplace=True,
    )
    if scale and "npp" in scale:
        df["npp_mean"] = scale_res[:, 2]
    if scale and "vsr" in scale:
        df["vsr_mean"] = scale_res[:, 2]

    #
    # Fix a few mising FIPS codes.
    #
    df.loc[df.name == "South Sudan", "fips"] = "OD"
    df.loc[df.name == "Curaçao", "fips"] = "UC"
    df.loc[df.name == "Åland Islands", "fips"] = "AX"  # ISO 3166 code

    #
    # Read GDP data.
    # Source: https://www.rug.nl/ggdc/historicaldevelopment/maddison/
    # For this source I had to slightly massage the data (see the
    # cleanup-maddison.py script) which extracts data since 1950 and
    # adds a FIPS attribute to each country.
    #
    my_gdp = gdp_df(gdp).add_prefix("GDP_")
    my_gdp = my_gdp.rolling(5, min_periods=1, axis=1).mean()
    merged = df.merge(my_gdp, how="inner", left_on="fips", right_index=True)
    if out:
        merged.to_csv(out.name, index=False, encoding="utf-8")


@cli.command()
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
def timeline(infiles, npp, band):
    area = None
    if npp:
        npp_ds = rasterio.open(npp)
    parsed = map(lambda fname: parse_fname2(fname), infiles)
    scenarios, whats, years = zip(*parsed)
    yy = sorted(set(map(int, years)))
    assert len(set(whats)) == 1
    keys = tuple(set(scenarios))
    out = dict((key, [0.0] * len(yy)) for key in keys)
    out = [{"name": xx, "data": [0.0] * len(yy)} for xx in keys]
    for scenario, year, arg in zip(scenarios, years, infiles):
        print(scenario, year)
        with rasterio.open(arg) as src:
            data = src.read(band, masked=True)
            if npp:
                npp_data = npp_ds.read(
                    1, masked=True, window=npp_ds.window(*src.bounds)
                )
                data *= npp_data
            area = tarea(src.bounds, src.height)
            data *= area
            out[keys.index(scenario)]["data"][years.index(year)] = float(ma.sum(data))

    if "historical" in keys:
        # ref = out[keys.index('historical')]['data'][0]
        ref = ma.sum(area)
        for jj, k in enumerate(out):
            for ii, v in enumerate(k["data"]):
                out[jj]["data"][ii] /= ref
    print(json.dumps({"years": yy, "data": out}))
    print("")


@cli.command()
@click.argument("country-file", type=click.Path(dir_okay=False))
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
@click.option("-o", "--out", type=click.File("wb"))
def country_timeline(infiles, band, country_file, npp, out):
    stack = []
    maps = []
    extent = None
    area = None
    if npp:
        npp_ds = rasterio.open(npp)
    with rasterio.open(country_file) as cc_ds:
        for arg in infiles:
            with rasterio.open(arg) as src:
                ccode = cc_ds.read(1, masked=True, window=cc_ds.window(*src.bounds))
                ccode = ma.masked_equal(ccode, -99)
                if extent is None:
                    extent = (
                        src.bounds.left,
                        src.bounds.right,
                        src.bounds.bottom,
                        src.bounds.top,
                    )
                data = src.read(band, masked=True)
                if npp:
                    npp_data = npp_ds.read(
                        1, masked=True, window=npp_ds.window(*src.bounds)
                    )
                    if npp_data.shape != data.shape:
                        import pdb

                        pdb.set_trace()
                    data *= npp_data
                res = weighted_mean_by_country(
                    ccode, data, carea(src.bounds, src.height)
                )
                if area is None:
                    ice_ds = rasterio.open(utils.luh2_static("icwtr"))
                    ice = ice_ds.read(1, window=ice_ds.window(*src.bounds))
                    area = ma.MaskedArray(carea(src.bounds, src.height))
                    area.mask = np.where(ice == 1, True, False)
                    intercept = np.exp(4.63955498) * area
                    if npp:
                        npp_data = npp_ds.read(
                            1, masked=True, window=npp_ds.window(*src.bounds)
                        )
                        intercept *= npp_data

                # res = weighted_mean_by_country(ccode, data, 1)
                stack.append(res)
                maps.append(data)
                print(
                    "%40s: %8.2f / %8.2f"
                    % (os.path.basename(arg), res[2, :].max(), res[2, :].min())
                )
        stacked = np.dstack(stack)
        names = tuple(map(parse_fname, infiles))
        df = to_df(stacked, names)
        if out:
            out.write(df.to_csv(index=False, encoding="utf-8").encode())
        print(df)


@cli.command()
@click.argument("biomes-file", type=click.Path(dir_okay=False))
@click.argument("biomes-shapes", type=click.Path(dir_okay=False))
@click.argument("infiles", nargs=-1, type=click.Path(dir_okay=False))
@click.option(
    "--npp",
    type=click.Path(dir_okay=False),
    help="Weight the abundance data with NPP per cell",
)
@click.option(
    "--vsr",
    type=click.Path(dir_okay=False),
    help="Weight the richness data with vertebrate richness per cell",
)
@click.option(
    "-b",
    "--band",
    type=click.INT,
    default=1,
    help="Index of band to process (default: 1)",
)
@click.option(
    "-o", "--out", type=click.File("w"), help="A file to write the merged data to"
)
def biomes(infiles, band, biomes_file, biomes_shapes, npp, vsr, out):
    if npp:
        scale_ds = rasterio.open(npp)
    elif vsr:
        scale_ds = rasterio.open(vsr)
    else:
        scale_ds = None
    types = list(set((x[0], x[1]) for x in map(parse_fname2, infiles)))
    assert len(types) == 1
    scenario = types[0][0]
    metric = types[0][1]
    print("%s -- %s" % (scenario, metric))
    df, scale_res = read_rasters(biomes_file, scale_ds, band, infiles)

    del df["percent"]
    del df["ratio"]
    del df["ar5"]
    del df["iso3"]
    del df["fips"]
    del df["cells"]

    df.rename(
        columns=dict(
            (x, metric + "_" + str(x))
            for x in filter(lambda x: isinstance(x, int), df.columns)
        ),
        inplace=True,
    )
    if npp:
        df["npp_mean"] = scale_res[:, 2]
    if vsr:
        df["vsr_mean"] = scale_res[:, 2]

    with fiona.open(biomes_shapes) as src:
        biome_names = dict(
            (
                (shp["properties"]["WWF_MHTNUM"], shp["properties"]["WWF_MHTNAM"])
                for shp in src
            )
        )
    df = df.assign(name=df.id.apply(lambda cc: biome_names[int(cc)]))
    cols = tuple(filter(lambda col: col[0:6] == "BIIAb_", df.columns))
    for col in df.loc[:, cols].columns:
        df.insert(5, col.replace("Ab_", "Ab2_"), df[col].div(df.npp_mean))
    data = pd.wide_to_long(
        df, ["BIIAb", "BIIAb2"], i=["name"], j="year", sep="_"
    ).reset_index()
    if out:
        data.to_csv(out, index=False)


if __name__ == "__main__":
    cli()
