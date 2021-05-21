#!/usr/bin/env python

from copy import copy
import rasterio
import matplotlib.pyplot as plt

import numpy as np
import numpy.ma as ma
import pandas as pd
from rasterio.plot import show
import re

import pdb

import projections.pd_utils as pd_utils
from projections.lu.luh2 import LU

shape = (567, 1440)
bounds = (-180, -58, 180, 83.75)

palette = copy(plt.cm.viridis)
# palette.set_over('g', 1.0)
palette.set_under("r", 1.0)
palette.set_bad("k", 1.0)

palette2 = copy(plt.cm.viridis)
palette2.set_over("b", 1.0)
palette2.set_under("r", 1.0)
palette2.set_bad("k", 1.0)


def rcs(height, res, left, bottom, right, top):
    er = 6378137.0
    lats = np.linspace(top, bottom + res[1], height)
    vec = (
        (
            np.sin(np.radians(lats + res[1] / 2.0))
            - np.sin(np.radians(lats - res[1] / 2.0))
        )
        * (res[0] * np.pi / 180)
        * er ** 2
        / 1e6
    )
    return vec.reshape((vec.shape[0], 1))


def check_hpd(df):
    scale = rcs(shape[0], (0.25, 0.25), *bounds)
    hpd = ma.masked_invalid(df["hpd"].values.reshape(shape))
    total = (hpd * scale).sum()
    # pdb.set_trace()
    print("hpd: %10.2e" % total)


def check(lu, df):
    if lu == "timber":
        return
    if lu + "_minimal" in df.columns:
        minimal = ma.masked_invalid(df[lu + "_minimal"].values.reshape(shape))
    else:
        minimal = 0
    # if lu + '_light' in df.columns:
    light = ma.masked_invalid(df[lu + "_light"].values.reshape(shape))
    # else:
    #  light = 0
    # if lu + '_intense' in df.columns:
    intense = ma.masked_invalid(df[lu + "_intense"].values.reshape(shape))
    # else:
    #  intense = 0
    data = ma.masked_invalid(df[lu].values.reshape(shape))
    total = minimal + light + intense
    print("checking: %s [%6.4f | %8.3f]" % (lu, total.max(), (data - total).sum()))
    assert np.all(data - total > -0.01)
    if (data - total).sum() > 2:
        # pdb.set_trace()
        pass
    # assert total.max() > 0.9
    assert np.isclose(total.min(), 0)
    pass


def check_sum(lus, df):
    total = ma.masked_invalid(df[lus[0]].values.reshape(shape))
    for lu in lus[1:]:
        total += ma.masked_invalid(df[lu].values.reshape(shape))
    print("%6.4f" % total.max())
    print(
        map(
            lambda x: "%s, %6.4f" % (x, df[x].values.reshape(shape)[444, 1208]),
            LU.keys(),
        )
    )
    pdb.set_trace()
    # assert np.allclose(total, 1, equal_nan=True)
    pass


def area(lu, df):
    pass


def doit():
    df1950 = pd_utils.load_pandas("/Volumes/Vagrant 155/playground/1950.pyd")
    df2009 = pd_utils.load_pandas("/Volumes/Vagrant 155/playground/2009.pyd")

    assert np.all(df1950.columns == df2009.columns)

    check_hpd(df1950)
    check_hpd(df2009)

    check_sum(LU.keys(), df1950)
    check_sum(LU.keys(), df2009)

    for lu in LU.keys():
        check(lu, df1950)
        check(lu, df2009)

    for col in df1950.columns:
        t1 = ma.masked_invalid(df1950[col].values.reshape(shape))
        t2 = ma.masked_invalid(df2009[col].values.reshape(shape))
        if re.search(r"_ref$", col):
            assert np.allclose(t1, t2, equal_nan=True)
        else:
            r = t2 / t1
            r.mask = np.logical_or(
                r.mask,
                np.logical_and(
                    np.where(t1 == 0, True, False), np.where(t2 == 0, True, False)
                ),
            )
            mm = min(r.max(), 15)
            show(r, title=str(col), vmin=0.99, vmax=1.01, cmap=palette)


doit()
