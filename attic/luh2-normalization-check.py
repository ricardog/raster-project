#!/usr/bin/env python

# This script checks for every grid cell of every raster that summing up
# all land use components adds up to 1.

from copy import copy
import matplotlib.pyplot as plt
from netCDF4 import Dataset
import numpy as np
import numpy.ma as ma
import os


palette = copy(plt.cm.Greens)
palette.set_over("r", 1.0)
palette.set_under("y", 1.0)
palette.set_bad("k", 1.0)

static = Dataset("../../data/luh2_v2/staticData_quarterdeg.nc")
icwtr = static.variables["icwtr"][:, :]
fstnf = static.variables["fstnf"][:, :]

vars = [
    u"primf",
    u"primn",
    u"secdf",
    u"secdn",
    u"urban",
    u"c3ann",
    u"c4ann",
    u"c3per",
    u"c4per",
    u"c3nfx",
    u"pastr",
    u"range",
]
a = ma.empty_like(icwtr)
a.mask = np.where(icwtr == 1, True, False)
atol = 1e-5

scenarios = [
    "LUH2_v2f_beta_SSP1_RCP2.6_IMAGE",
    "LUH2_v2f_beta_SSP2_RCP4.5_MESSAGE-GLOBIOM",
    "LUH2_v2f_beta_SSP3_RCP7.0_AIM",
    "LUH2_v2f_beta_SSP4_RCP3.4_GCAM",
    "LUH2_v2f_beta_SSP4_RCP6.0_GCAM",
    "LUH2_v2f_beta_SSP5_RCP8.5_REMIND-MAGPIE",
    "historical",
]
file_list = [os.path.join("../../data/luh2_v2", x, "states.nc") for x in scenarios]

for fname in file_list:
    print(fname)
    with Dataset(fname) as ds:
        for idx, year in enumerate(ds.variables["time"]):
            np.copyto(a, icwtr)
            for v in vars:
                a += ds.variables[v][idx]
            xx = ma.masked_where(a.mask, ~np.isclose(a, 2, atol=atol))
            over = np.count_nonzero(ma.where(xx, 1, 0))
            if idx == int(year):
                print("  year %d" % (850 + idx))
            else:
                print("  year %d" % int(year))
            if over > 0:
                print("    non-zero: %d" % over)
                print("    max     : %6.4f" % a.max())
