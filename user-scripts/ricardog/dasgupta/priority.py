#!/usr/bin/env python

import numpy.ma as ma
import rasterio
from projections.utils import outfn

with rasterio.open(outfn("luh2", "rsr-land.tif")) as rsr_ds:
    with rasterio.open(
        outfn("luh2", "ssp2_rcp4.5_message-globiom-BIIAb-2020.tif")
    ) as bii_ds:
        meta = bii_ds.meta.copy()
        meta.update({"driver": "GTiff", "compress": "lzw", "predictor": 3})
        rsr = rsr_ds.read(1)  # , window=rsr_ds.window(*bii_ds.bounds))
        rsr = rsr.astype("float32")
        rsr = ma.masked_where(rsr == rsr_ds.nodata, rsr, copy=True)
        rsr.fill_value = -9999
        bii = bii_ds.read(1, masked=True)
priority = rsr * (1 - bii)

with rasterio.open(outfn("luh2", "priority.tif"), "w", **meta) as out:
    out.write(priority.filled(), indexes=1)
