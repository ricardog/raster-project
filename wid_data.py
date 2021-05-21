#!/usr/bin/env python3

import pdb

import numpy as np
import pandas as pd
from pylru import lrudecorator
import seaborn as sns

BII_URL = (
    "http://ipbes.s3.amazonaws.com/weighted/"
    "historical-BIIAb-npp-country-1880-2014.csv"
)


@lrudecorator(20)
def read_remote_csv(url, **kwargs):
    return pd.read_csv(url, **kwargs)


def findt(ss):
    rval = [None] * len(ss)
    rval[0] = True
    for i in range(1, len(ss)):
        rval[i] = not pd.isnull(ss.iloc[i]) and ss.iloc[i] != ss.iloc[i - 1]
    return pd.Series(rval)


def get_bii_data(dropna=True):
    bii = read_remote_csv(BII_URL)
    cols = list(
        filter(lambda nn: nn[0:6] == "BIIAb_" or nn[0:4] == "GDP_", bii.columns)
    )
    bii2 = bii.loc[:, ["fips", "ar5", "name", "iso3", "npp_mean"] + cols]
    if dropna:
        bii2.dropna(inplace=True)
    cols = tuple(filter(lambda col: col[0:6] == "BIIAb_", bii2.columns))
    for col in bii2.loc[:, cols].columns:
        bii2.insert(5, col.replace("Ab_", "Ab2_"), bii2[col].div(bii2.npp_mean))
    t7 = pd.wide_to_long(
        bii2, ["BIIAb", "BIIAb2", "GDP"], i=["name"], j="Year", sep="_"
    )
    t7.reset_index(inplace=True)
    t7 = t7.assign(year=t7.Year.astype(int))
    del t7["Year"]
    return t7


def get_bii_summary():
    def cleanup(df):
        df = df.iloc[0:16, 1:]
        df = pd.melt(
            df,
            value_vars=df.columns[3:],
            id_vars="Name",
            value_name="BIIAb",
            var_name="Year",
        )
        df = df.assign(Year=df.Year.astype(int))
        df.columns = ["name", "year", "BIIAb"]
        return df

    url = "http://ipbes.s3.amazonaws.com/weighted/historical-BIIAb-npp-%s-0900-2014.csv"
    subreg = cleanup(read_remote_csv(url % "subreg"))
    glob = cleanup(read_remote_csv(url % "global"))
    return pd.concat([glob, subreg])


def get_wid_data():
    url_temp = "http://ipbes.s3.amazonaws.com/by-country/%s.csv"
    metrics = ("sfiinc992j", "afiinc992t", "afiinc992j", "afiinc992i")
    data = dict()
    for metric in metrics:
        data[metric] = read_remote_csv(url_temp % metric, encoding="utf-8")
    return data


def get_eci_data(dropna=False):
    bii = read_remote_csv(BII_URL)
    cols = list(filter(lambda nn: nn[0:4] == "ECI_", bii.columns))
    bii2 = bii.loc[
        :,
        [
            "fips",
            "ar5",
            "name",
            "iso3",
        ]
        + cols,
    ]
    if dropna:
        bii2.dropna(inplace=True)
    t7 = pd.wide_to_long(bii2, "ECI", i=["name"], j="Year", sep="_")
    t7.reset_index(inplace=True)
    t7 = t7.assign(year=t7.Year.astype(int))
    del t7["Year"]
    return t7


def get_rol_data(dropna=False):
    bii = read_remote_csv(BII_URL)
    cols = {
        "WJP Rule of Law Index: Overall Score": "ROLI",
        "Factor 1: Constraints on Government Powers": "ROLI_1",
        "Factor 2: Absence of Corruption": "ROLI_2",
        "Factor 3: Open Government ": "ROLI_3",
        "Factor 4: Fundamental Rights": "ROLI_4",
        "Factor 5: Order and Security": "ROLI_5",
        "Factor 6: Regulatory Enforcement": "ROLI_6",
        "Factor 7: Civil Justice": "ROLI_7",
        "Factor 8: Criminal Justice": "ROLI_8",
    }
    bii2 = bii.loc[:, ["fips", "ar5", "name", "iso3"] + list(cols.keys())]
    if dropna:
        bii2.dropna(inplace=True)
    bii2.rename(columns=cols, inplace=True)
    return bii2


def get_wgi_data():
    url = "http://ipbes.s3.amazonaws.com/by-country/wgi.csv"
    wgi = read_remote_csv(url)
    return wgi


def get_language_data():
    url = "http://ipbes.s3.amazonaws.com/by-country/language-distance.csv"
    return read_remote_csv(url, encoding="utf-8")


def get_area_data():
    url = "http://ipbes.s3.amazonaws.com/by-country/wb-area.csv"
    return read_remote_csv(url, encoding="utf-8")


def area_order():
    return ("V. Small", "Small", "Medium", "Large", "V. Large")


def get_p4_data(avg=False):
    bins = [-100, -10, -6, 6, 10]
    labels = ["Other", "Autocracy", "Anocracy", "Democracy"]

    url = "http://ipbes.s3.amazonaws.com/by-country/polityv4.csv"
    p4v = read_remote_csv(url, encoding="utf-8")
    if avg:
        grouped = p4v.sort_values(["year"]).groupby("fips")
        window = grouped.rolling(window=5, min_periods=5)
        df = window.agg({"polity": np.mean, "polity2": np.mean, "year": np.min})
        df.reset_index(inplace=True)
        p4v = pd.merge(
            p4v,
            df[["fips", "year", "polity", "polity2"]],
            on=["fips", "year"],
            suffixes=["_old", ""],
        )
        del p4v["polity_old"]
        del p4v["polity2_old"]
    p4v = p4v.assign(
        government=pd.cut(p4v.polity, right=True, bins=bins, labels=labels)
    )

    return p4v


def gov_order():
    return ("Other", "Autocracy", "Anocracy", "Democracy")


def get_hpop_data():
    url = "http://ipbes.s3.amazonaws.com/by-country/hpop.csv"
    hpop = read_remote_csv(url)
    return hpop[hpop.fips != "Global"]


def get_gdp_data():
    url = "http://ipbes.s3.amazonaws.com/by-country/gdp-1800.csv"
    gdp = read_remote_csv(url)
    return gdp


def gdp_tresholds(df):
    bins = [0, 500, 1000, 2000, 4000, 8000, 16000, 32000]
    labels = ["0", "0.5k", "1k", "2k", "4k", "8k", "16k"]

    df["GDPq"] = pd.cut(df.GDP, right=False, bins=bins, labels=labels)
    grouped = df.sort_values(["fips", "year"]).groupby("fips")
    df["threshold"] = grouped["GDPq"].transform(findt)
    return df


def gdp_tresholds_plot():
    def set_alpha(ax, a):
        for art in ax.get_children():
            if isinstance(art, PolyCollection):
                art.set_alpha(a)

    bii5 = gdp_tresholds(get_bii_data(False))
    bii5 = bii5[bii5.threshold == True]
    biit = biit.assign(Decade=(biit.Year / 10).astype(int) * 10)
    bii = bii.assign(Decade=(bii.Year / 10).astype(int) * 10)

    hue_order = tuple(reversed(sorted(biit.Decade.unique())))
    for metric in ("BIIAb2", "BIIAb"):
        g = sns.catplot(
            x="GDPq",
            y=metric,
            data=biit,
            col="ar5",
            col_wrap=3,
            hue="Decade",
            hue_order=hue_order,
            # palette=sns.color_palette(n_colors=15),
            # palette='tab20c',
            palette=sns.color_palette("coolwarm", 15),
            sharey=True,
            kind="violin",
            inner="point",
            dodge=False,
            scale="count",
            cut=0,
        )
        g.set_xlabels("Quantized GDP per capita (log-scale)")
        g.set_ylabels("Mean NPP-weighted BII (fraction)")
        for ax in g.fig.get_axes():
            set_alpha(ax, 0.8)


if __name__ == "__main__":
    pass
