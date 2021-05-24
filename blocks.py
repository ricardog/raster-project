#!/usr/bin/env python

import fiona
import numpy as np
import numpy.ma as ma
import rasterio
import rasterio.features
import rasterio.mask
import pandas as pd
import sys


shp_file = "/Users/ricardog/src/eec/data/from-adriana/tropicalforests.shp"
shp_file = "/Users/ricardog/src/eec/predicts/playground/tmp/topical-band34-24.shp"
src_file = "/Users/ricardog/src/eec/data/sources/PAS_1km_2005_0ice.bil"
# src_file = '/Users/ricardog/src/eec/data/sources/pas_1km_2005_0ice.tif'
src_file = (
    "zip:///Users/ricardog/src/eec/data/sources/PAS_2005.zip!" + "PAS_1km_2005_0ice.bil"
)
out_file = "pasture-2005-masked.tif"

with rasterio.Env(GDAL_TIFF_INTERNAL_MASK=True):
    with fiona.open(shp_file) as shp:
        with rasterio.open(src_file, "r", format="GTiff") as src:
            meta = src.meta.copy()
            meta.update({"driver": "GTiff", "compress": "lzw", "predictor": 2})
            blocks = src.block_shapes
            nans = np.full(blocks[0], np.nan, dtype=np.float32)
            with rasterio.open(out_file, "w", **meta) as dst:
                for ji, window in src.block_windows(1):
                    if ji[0] % 100 == 0:
                        sys.stdout.write(".")
                        sys.stdout.flush()
                    out_transform = src.window_transform(window)
                    minx, miny = (window[1][0], window[0][0]) * src.affine
                    maxx, maxy = (window[1][1], window[0][1]) * src.affine
                    cropped = list(shp.items(bbox=(minx, miny, maxx, maxy)))
                    if len(cropped) == 0:
                        pass
                        # print("%d, %d : skip" % (ji[0], ji[1]))
                        dst.write(nans, window=window, indexes=1)
                        continue
                    shapes = [feature[1]["geometry"] for feature in cropped]
                    shape_mask = rasterio.features.geometry_mask(
                        shapes,
                        transform=out_transform,
                        invert=False,
                        out_shape=nans.shape,
                        all_touched=True,
                    )
                    data = src.read(window=window, masked=True)
                    data.mask = data.mask | shape_mask
                    out_shape = data.shape[1:]
                    df = pd.Series(data.reshape(-1))
                    df = df.dropna()
                    # print("%d, %d : %d rows" % (ji[0], ji[1], len(df.index)))
                    out = df.reindex(range(out_shape[0] * out_shape[1])).values
                    out = ma.masked_invalid(out.reshape(out_shape))
                    dst.write(out, window=window, indexes=1)
print("")
