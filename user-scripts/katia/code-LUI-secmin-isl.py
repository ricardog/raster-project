#!/usr/bin/env python3

import os

import rasterio

from projections import predicts, utils
from rasterset import RasterSet

# Import standard PREDICTS rasters
rasters = predicts.rasterset("1km", "medium", year=2005)

for suffix in ("islands", "mainland"):
    # Open the BII raster file
    mask_file = (
        "C:/Users/katis2/Desktop/Final_projections/Clip_variables/abundance-based-bii-%s.tif"
        % suffix
    )
    mask_ds = rasterio.open(mask_file)

    # set up the rasterset, cropping to mainlands
    rs = RasterSet(rasters, mask=mask_ds, maskval=-9999, crop=True)

    # Run through each land-use
    for lu in ("cropland", "pasture", "primary", "secondary", "urban"):
        # And every use intensity
        for ui in ("minimal", "light", "intense"):
            name = "%s_%s" % (lu, ui)
            print(name)
            oname = utils.outfn("katia", "%s-%s.tif" % (name, suffix))
            if os.path.isfile(oname) or name in ("secondary_intense", "urnan_light"):
                continue
            rs.write(name, oname)
