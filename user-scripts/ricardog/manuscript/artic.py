#!/usr/bin/env python3

import fiona
import os
from pathlib import Path

ARCTIC = (
    "Tundra",
    "Rock and Ice",
)



def is_arctic(eco):
    return eco["properties"]["WWF_MHTNAM"] in ARCTIC


def main():
    fname = Path(
        os.getenv("DATA_ROOT", "/mnt/data"),
        "tnc_terr_ecoregions/" "tnc_terr_ecoregions.shp",
    )
    with fiona.open(fname) as src:
        meta = src.meta.copy()
        meta["schema"]["properties"].update(
            {
                "arctic": "bool",
            }
        )
        outdir = Path(os.getenv("OUTDIR", "/mnt/predicts"),
                      "vector", "arctic")
        if not outdir.exists():
            outdir.mkdir()
        with fiona.open(outdir.joinpath("arctic.shp"), "w", **meta) as dst:
            for eco in src:
                props = eco["properties"]
                props["arctic"] = is_arctic(eco)
                dst.write({"geometry": eco["geometry"], "properties": props})

    return


if __name__ == "__main__":
    main()
