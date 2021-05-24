#!/usr/bin/env python

import netCDF4
import os
import sys

from projections.mp4_utils import to_mp4


def fraction(ds, idx):
    rndwd = ds.variables["rndwd"][idx]
    fulwd = ds.variables["fulwd"][idx]
    combf = ds.variables["combf"][idx]
    return (rndwd + combf) / (rndwd + fulwd + combf)


if len(sys.argv) != 2:
    print("Usage: %s <file.nc>" % os.path.basename(sys.argv[0]))
    sys.exit(1)
fname = sys.argv[1]
title = "Fraction of commercial wood harvest"
oname = "%s.mp4" % "wood-harv"
manage = netCDF4.Dataset(fname)
years = manage.variables["time"][:]
if years[0] < 850:
    years = [int(y + 850) for y in years]
else:
    years = map(int, years)

frac = fraction(manage, 0)
for idx, img, text in to_mp4(title, oname, len(years), frac, str(years[0]), 10):
    img.set_array(fraction(manage, idx))
    text.set_text(str(years[idx]))
