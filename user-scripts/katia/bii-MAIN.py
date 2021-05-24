#!/usr/bin/env python

from projections import utils
from rasterset import RasterSet, Raster, SimpleExpr

CLIP = "no-clip"

# pull in all the rasters for computing bii
bii_rs = RasterSet(
    {
        "abundance": Raster(
            "abundance", utils.outfn("katia", CLIP, "bii-ab-mainlands.tif")
        ),
        "comp_sim": Raster("comp_sim", utils.outfn("katia", "bii-ab-cs-mainlands.tif")),
        "clip_ab": SimpleExpr("clip_ab", "clip(abundance, 0, 1.655183)"),
        "bii_ab": SimpleExpr("bii_ab", "abundance * comp_sim"),
        "bii_ab2": SimpleExpr("bii_ab2", "clip_ab * comp_sim"),
    }
)

# write out bii raster
bii_rs.write(
    "bii_ab" if CLIP == "clip" else "bii_ab2",
    utils.outfn("katia", CLIP, "abundance-based-bii-mainlands.tif"),
)

# do the same for species richness
# pull in all the rasters for computing bii
bii_rs = RasterSet(
    {
        "sp_rich": Raster(
            "sp_rich", utils.outfn("katia", CLIP, "bii-sr-mainlands.tif")
        ),
        "comp_sim": Raster("comp_sim", utils.outfn("katia", "bii-sr-cs-mainlands.tif")),
        "clip_sr": SimpleExpr("clip_sr", "clip(sp_rich, 0, 1.636021)"),
        "bii_sr": SimpleExpr("bii_sr", "sp_rich * comp_sim"),
        "bii_sr2": SimpleExpr("bii_sr2", "clip_sr * comp_sim"),
    }
)

# write out bii raster
bii_rs.write(
    "bii_sr" if CLIP == "clip" else "bii_sr2",
    utils.outfn("katia", CLIP, "speciesrichness-based-bii-mainlands.tif"),
)
