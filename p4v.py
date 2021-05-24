#!/usr/bin/env python3

import glob
import os
import re

import matplotlib.pyplot as plt
from netCDF4 import Dataset
import numpy as np
import numpy.ma as ma
import pandas as pd
import projections.utils as utils
from pylru import lrudecorator
import rasterio
import seaborn as sns

import pdb


def sum_by(regions, data):
    mask = np.logical_or(data.mask, regions.mask)
    # regions.mask = ma.getmask(data)
    # regions_idx = regions.compressed().astype(int)
    mask_idx = np.where(mask == False)                      # noqa E712
    regions_idx = regions[mask_idx]
    summ = np.bincount(regions_idx, data[mask_idx])
    ncells = np.bincount(regions_idx)
    idx = np.where(ncells > 0)
    return idx[0], summ[idx]


@lrudecorator(10)
def cnames_df():
    return pd.read_csv(utils.cnames_csv())


@lrudecorator(300)
def cname_to_fips(name):
    def rematch(regexp, name):
        if isinstance(regexp, str):
            return re.search(regexp, name, re.I) is not None
        return False

    def cleanup(index):
        row = df[index]["fips"]
        if len(row) > 1:
            return row.values
        return row.values[0]

    if not isinstance(name, (str)):
        return None

    df = cnames_df()
    index = df["cow.name"] == name
    if index.any():
        return cleanup(index)
    index = df["country.name.en.regex"].apply(rematch, args=(name,))
    if index.any():
        return cleanup(index)
    index = df["country.name.de.regex"].apply(rematch, args=(name,))
    if index.any():
        return cleanup(index)
    return name


@lrudecorator(300)
def iso3_to_fips(iso3):
    def cleanup(index):
        row = df[index]["fips"]
        if len(row) > 1:
            return row.values
        return row.values[0]

    if not isinstance(iso3, (str)):
        return None
    df = cnames_df()
    rows = df[df.iso3c == iso3.upper()]
    if rows.empty:
        return None
    return rows["fips"].values[0]


@lrudecorator(300)
def wb3_to_cid(wb3):
    def cleanup(index):
        row = df[index]["fips"]
        if len(row) > 1:
            return row.values
        return row.values[0]

    if not isinstance(wb3, (str)):
        return None
    df = cnames_df()
    rows = df[df.wb_api3c == wb3.upper()]
    if rows.empty:
        return None
    return rows["un"].values[0]


def cid_to_x(cid, x):
    if cid is None:
        return None
    if np.isnan(cid):
        return cid
    if cid == 736:
        cid = 729
    df = cnames_df()
    row = df[df.un == cid]
    if not row.empty:
        return row[x].values[0]
    try:
        return str(int(cid))
    except ValueError:
        pdb.set_trace()
        pass


def cid_to_fips(cid):
    return cid_to_x(cid, "fips")


def cid_to_iso3(cid):
    return cid_to_x(cid, "iso3c")


def iso2_to_cid(iso2):
    df = cnames_df()
    row = df.un[df.iso2c == iso2.upper()]
    if row.empty or np.isnan(row).any():
        return -1
    return int(row.values[0])


def fips_to_cid(fips):
    df = cnames_df()
    row = df.un[df.fips == fips.upper()]
    if row.empty or np.isnan(row).any():
        return -1
    return int(row.values[0])


def fips_to_iso3(fips):
    return cid_to_iso3(fips_to_cid(fips))


def cid_to_name(cid):
    return cid_to_x(cid, "country.name.en")


def iso2_to_fips(iso2):
    return cid_to_x(iso2_to_cid(iso2), "fips")


def wb3_to_fips(wb3):
    return cid_to_x(wb3_to_cid(wb3), "fips")


def cleanup_p4v(fname, avg=True):
    bins = [-100, -10, -6, 6, 10]
    labels = ["Other", "Autocracy", "Anocracy", "Democracy"]
    p4 = pd.read_excel(fname)
    p4s = p4.loc[:, ["scode", "country", "year", "polity", "polity2"]]
    # Select countries we find a name match for
    cfips = map(lambda cc: cname_to_fips(cc), p4s.country.tolist())
    csel = map(
        lambda cc: cc if (isinstance(cc, str) and len(cc) == 2) else False, cfips
    )
    p4s2 = p4s.assign(fips=tuple(csel))
    p4s3 = p4s2[p4s2.fips != False]                         # noqa E712
    if avg:
        df = (
            p4s3.loc[:, ["fips", "polity", "polity2"]]
            .groupby("fips")
            .rolling(window=5, fill_method="bfill")
            .mean()
            .reset_index()
        )
        p4s3["polity"] = df.polity.values
        p4s3["polity2"] = df.polity2.values
    p4s3 = p4s3.assign(
        government=pd.cut(p4s3.polity2, right=True, bins=bins, labels=labels)
    )
    return p4s3


def cleanup_language():
    lang = pd.read_csv(utils.data_file("policy", "language-distance.csv"), index_col=0)
    lang.drop(["USSR", "Gran Colombia", "Montenegro"], axis=0, inplace=True)
    lang.drop(["USSR", "Gran Colombia", "Montenegro"], axis=1, inplace=True)
    cfips = map(lambda cc: cname_to_fips(cc), lang.index.tolist())
    csel = map(
        lambda cc: cc if (isinstance(cc, str) and len(cc) == 2) else False, cfips
    )
    fips = tuple(csel)
    lang.columns = fips
    lang = lang.assign(fips=fips)
    lang.index = fips
    lang = lang.loc[lang.fips != False, lang.columns != False] # noqa E712
    del lang["fips"]
    return lang


def cleanup_wb_area(fname):
    wb_area = pd.read_csv(fname)
    wb_area = wb_area.loc[:, ["Country Name", "Country Code", "2017"]]
    wb_area["2017"] /= 1000
    wb_area.columns = ["Country Name", "Country Code", "WB Area"]
    wb_area = wb_area.assign(
        area_q=pd.qcut(
            wb_area["WB Area"],
            q=5,
            labels=["V. Small", "Small", "Medium", "Large", "V. Large"],
        )
    )
    return wb_area.dropna()


def read_wid_csvs():
    data = dict()
    for fname in glob.glob(
        os.path.join(utils.data_root(), "wid", "Data", "WID_*_InequalityData.csv")
    ):
        bname = os.path.basename(fname)
        _, iso2, _ = bname.split("_", 3)
        iso2 = iso2.lower()
        df = pd.read_csv(fname, sep=";", encoding="latin1", low_memory=False)
        df.columns = df.iloc[6, :]
        data[iso2] = df
    return data


def get_var(vname, data):
    countries = tuple(filter(lambda cc: vname in data[cc].columns, data.keys()))
    return dict((cc, data[cc]) for cc in countries)


def get_wid_data(vname, perc, data, min_len=0):
    rdata = None
    for cc in data.keys():
        cid = iso2_to_cid(cc)
        if cid == "-1":
            continue
        fips = cid_to_fips(cid)
        iso3 = cid_to_iso3(cid)
        df = data[cc].loc[:, ["year", "perc", vname]][data[cc].perc == perc]
        df.dropna(inplace=True)
        if len(df) > min_len:
            df["fips"] = fips
            df["iso3"] = iso3
            df["country"] = cid_to_name(iso2_to_cid(cc))
            df["variable"] = vname
            df.rename(columns={vname: perc}, inplace=True)
            df[perc] = df[perc].astype(float)
            df.year = df.year.astype(int)
            del df["perc"]
            if rdata is None:
                rdata = df
            else:
                rdata = rdata.append(df, ignore_index=True)
    return rdata


def cleanup_wid_data():
    perc = "p90p100"
    data = dict()
    raw_data = read_wid_csvs()
    if raw_data == {}:
        return raw_data
    for vname in ["sfiinc992j"]:
        data[vname] = get_wid_data(vname, perc, get_var(vname, raw_data))
    for vname in ["afiinc992i", "afiinc992j", "afiinc992t"]:
        vdata = get_var(vname, raw_data)
        p90 = get_wid_data(vname, perc, vdata)
        p0 = get_wid_data(vname, "p0p100", vdata)
        del p0["variable"]
        del p0["country"]
        del p0["iso3"]
        vv = p90.merge(
            p0, how="inner", left_on=["year", "fips"], right_on=["year", "fips"]
        )
        vv["ratio"] = vv.p90p100 / vv.p0p100
        data[vname] = vv
    return data


def cleanup_wgi_data():
    wgi = pd.read_excel(utils.data_file("policy", "wgidataset.xlsx"), "RuleofLaw")
    wgi.loc[12, "Rule of Law":"Unnamed: 1"] = ["name", "wb_api3c"]
    wgi2 = wgi.iloc[12:, :]
    wgi3 = wgi2.loc[
        :, wgi2.loc[13, :].isin(["Country/Territory", "WBCode", "Estimate"])
    ]
    wgi3.columns = wgi3.loc[12, :].astype(str)
    wgi4 = wgi3.loc[14:, :]
    wgi4 = wgi4.assign(fips=wgi4.wb_api3c.apply(wb3_to_fips))
    wgi5 = wgi4[~wgi4.fips.isna()]
    wgi_long = pd.melt(
        wgi5,
        value_vars=wgi4.columns[2:-1],
        id_vars=["name", "fips"],
        value_name="RoLI",
        var_name="year",
    )
    return wgi_long


def read_hpd_rasters(years, regions):
    if regions:
        with rasterio.open(regions) as regions_ds:
            # Adjust read area so raster is the full 1440x720 resolution
            regions = regions_ds.read(
                1,
                masked=True,
                boundless=True,
                window=regions_ds.window(*(-180, -90, 180, 90)),
            )
            regions = ma.masked_equal(regions, -99)
            regions = ma.masked_equal(regions, regions_ds.nodata)
    with Dataset(utils.luh2_static()) as static:
        carea = static.variables["carea"][:]
    # hpop = np.zeros((len(years), len(np.unique(regions.compressed())) + 1))
    hpop = np.zeros((len(years), 196))
    for idx, year in enumerate(years):
        with rasterio.open(utils.outfn("luh2", "historical-hpd-%d.tif" % year)) as ds:
            hpd = ds.read(
                1, masked=True, boundless=True, window=ds.window(*(-180, -90, 180, 90))
            )
            hp = carea * hpd
            hpop[idx, 0] = hp.sum()
            cids, hpop[idx, 1:] = sum_by(regions, hp)
    fips = list(map(cid_to_fips, cids))
    hpd = pd.DataFrame(hpop, index=years, columns=["Global"] + fips)
    hpd = hpd.T
    hpd["fips"] = hpd.index
    hpd = hpd.melt(
        id_vars="fips",
        value_vars=range(1950, 2011, 10),
        var_name="year",
        value_name="HPD",
    )
    hpd.year = hpd.year.astype(int)
    return hpd


def read_data():
    print("Cleaning up WB area")
    area = cleanup_wb_area(
        utils.data_file("area", "API_AG.LND.TOTL.K2_DS2_en_csv_v2_10181480.csv")
    )
    print("Cleaning up language distance matrix")
    language = cleanup_language()
    print("Cleaning up polity v4 data")
    p4v = cleanup_p4v(utils.data_file("policy", "p4v2017.xls"), False)
    print("Cleaning up world inequality database data")
    wid = cleanup_wid_data()
    print("Cleaning up world governance index data")
    wgi = cleanup_wgi_data()
    print("Summarizing human population data")
    hpop = read_hpd_rasters(
        tuple(range(1800, 2000, 10)) + tuple(range(2000, 2015, 1)),
        utils.outfn("luh2", "un_codes-full.tif"),
    )
    return area, language, p4v, wid, wgi, hpop


def swarm_plot(data, labels):
    g = sns.FacetGrid(data, col="ar5", col_wrap=3, hue="area_q")
    g = g.map(sns.swarmplot, "government", "BIIAb_diff", order=labels)
    g.map(plt.axhline, y=1.0, lw=2).add_legend()
    plt.show()


if __name__ == "__main__":
    area, language, p4v, wid, wgi, hpop = read_data()
    area.to_csv("summary-data/wb-area.csv", index=False)
    language.to_csv("summary-data/language-distance.csv", index=False)
    p4v.to_csv("summary-data/polityv4.csv", index=False)
    for metric in wid.keys():
        wid[metric].to_csv("summary-data/%s.csv" % metric, index=False)
    wgi.to_csv("summary-data/wgi.csv", index=False)
    hpop.to_csv("summary-data/hpop.csv", index=False)
