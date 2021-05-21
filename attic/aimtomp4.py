#!/usr/bin/env python

from copy import copy
import netCDF4
import numpy as np
import numpy.ma as ma
import os
import rasterio
import re
import sys

import pdb

from projections.mp4_utils import to_mp4
import matplotlib.colors as colors


def main():
    if len(sys.argv) != 3:
        print("Usage: %s <scenario> <directory>" % os.path.basename(sys.argv[0]))
        sys.exit(1)
    title = "Biodiversity Projection"
    oname = "%s.mp4" % sys.argv[1]
    files = sorted(
        filter(
            lambda x: re.match(r"%s-\d{4}.tif$" % sys.argv[1], x),
            os.listdir(sys.argv[2]),
        )
    )
    years = map(lambda x: re.sub(r"%s-(\d{4,4}).tif" % sys.argv[1], "\\1", x), files)
    ds = rasterio.open(os.path.join(sys.argv[2], files[0]))
    data = np.empty((len(files), ds.shape[0], ds.shape[1]))
    for idx, f in enumerate(files):
        ds = rasterio.open(os.path.join(sys.argv[2], files[idx]))
        dd = ds.read(1, masked=True)
        data[idx] = np.exp(ma.where(np.isnan(dd), 1, dd))
    db = 10 * np.log(data / (data[0] + 0.01))
    cnorm = colors.Normalize(vmin=-3, vmax=3)

    for idx, img, text in to_mp4(
        title, oname, len(years), dd, years[0], 10, cnorm=cnorm
    ):
        img.set_array(db[idx])
        text.set_text(years[idx])


if __name__ == "__main__":
    main()
