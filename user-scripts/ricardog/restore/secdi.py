#!/usr/bin/env python3

import click
import numpy as np
import numpy.ma as ma
from pathlib import Path
import rasterio

from projections.utils import outfn

SCENARIOS = ("fc", "fc_no_cra", "fc_no_sfa", "idc_amz", "idc_imp_f3", "no_fc")


def brazil_dirname(scenario):
    if scenario == "fc":
        return "LANDUSE_FC"
    if scenario == "fc_no_cra":
        return "LANDUSE_FCnoCRA"
    if scenario == "fc_no_sfa":
        return "LANDUSE_FCnoSFA"
    if scenario == "idc_amz":
        return "LANDUSE_IDCAMZ"
    if scenario == "idc_imp_f3":
        return "LANDUSE_IDCImpf3"
    if scenario == "no_fc":
        return "LANDUSE_NOFC"
    return "sample"


def rotate(array, places):
    new_arr = np.roll(array, places, axis=0)
    new_arr[:places] = ma.zeros((new_arr[:places].shape))
    return new_arr


@click.command()
@click.argument("scenario", type=click.Choice(SCENARIOS))
def gen_secdi(scenario):
    """Generate intermediate secondary raster

    "Age" the Restore layer to calculate intermediate secondary
    fraction.  When a Restore cell fraction is 15 years old, it converts
    to intermediate secondary.  The script is straightforward because
    the Restore layer is monotonically increasing so we don't have to
    handle conversion to a third land-use class.

    """
    if not Path(
        outfn("luh2", "restore", "brazil", brazil_dirname(scenario), "Regrowth.tif")
    ).exists():
        print(f"Skiping scenario {scenario}; no regrowth")
        return
    print(f"Aging secondary rasters for scenario {scenario}")
    with rasterio.open(
        outfn("luh2", "restore", "brazil", brazil_dirname(scenario), "Regrowth.tif")
    ) as src:
        meta = src.meta
        meta.update({"driver": "GTiff", "compress": "lzw", "predictor": 3})
        data = src.read(masked=True)
        out = ma.empty_like(data)
        for idx in range(out.shape[0]):
            out[idx, :, :] = data[0 : idx + 1, :, :].sum(axis=0)
        out = rotate(out, 3)
        out.mask = data.mask
        with rasterio.open(
            outfn("luh2", "restore", "brazil", brazil_dirname(scenario), "secdi.tif"),
            "w",
            **meta,
        ) as dst:
            dst.write(out.filled())
    print("done")
    return


if __name__ == "__main__":
    gen_secdi()
