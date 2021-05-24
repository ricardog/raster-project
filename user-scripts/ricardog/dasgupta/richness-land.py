#!/usr/bin/env python

import numpy as np
import rasterio

iucn_dir = "/Users/ricardog/src/eec/data/iucn-richness-all-2018"
with rasterio.open(iucn_dir + "/Richness_all.tif") as rich_ds:
    meta = rich_ds.meta.copy()
    meta.update({"driver": "GTiff", "compress": "lzw", "predictor": 2})
    with rasterio.open(iucn_dir + "/icwtr.tif") as icwtr_ds:
        data = rich_ds.read(1, masked=True)
        icwtr = icwtr_ds.read(1, masked=True)
data.mask = np.logical_or(icwtr.mask, icwtr == 1)

with rasterio.open(iucn_dir + "/richness-land.tif", "w", **meta) as out:
    out.write(data.filled(), indexes=1)
