#!/usr/bin/env python3

import rasterio
from rasterio.profiles import DefaultGTiffProfile

from projutils import hpd
from rasterset import RasterSet

def doit(year):
    rs = RasterSet(hpd.hyde.scale_grumps(year))
    import pdb; pdb.set_trace()
    data, meta = rs.eval("hpd")
    kwargs = DefaultGTiffProfile(count=1,
                                 dtype="float32",
                                 nodata=meta["nodata"],
                                 predictor=3,
                                 crs=meta["crs"],
                                 transform=meta["transform"],
                                 width=meta["width"],
                                 height=meta["height"],
                                 interleave="pixel")
    with rasterio.open("historical-hpd-2010.tif", "w", **kwargs) as dst:
        dst.write(data.squeeze().filled(), indexes=1)
    return


if __name__ == "__main__":
    doit(2010)
