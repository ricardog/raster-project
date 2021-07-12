#!/usr/bin/env python3

import click
from fnmatch import fnmatch
import matplotlib
import matplotlib.pyplot as plt
import numpy as np
import numpy.ma as ma
import os
import pandas as pd
from pathlib import Path
import rasterio
import seaborn as sns


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


def name_to_short(indicator):
    if indicator == "BIIAb":
        return "BII", "bii"
    if indicator == "CompSimAb":
        return "CompSim", "cs-ab"
    if indicator == "Abundance":
        return "Abundance", "ab"
    if indicator == "Abundance-te":
        return "Temperate Abundance", "ab-te"
    if indicator == "Abundance-tr":
        return "Tropical Abundance", "ab-tr"
    if indicator == "Abundance-nf":
        return "Non-forest Abundance", "ab-nf"
    return None, None


def plot_all(data, indicator, npp):
    t_ind, f_ind = name_to_short(indicator)
    if npp is None:
        npp_text = " "
    else:
        npp_text = "NPP-weighted "

    _ = plt.figure(figsize=(6, 4), dpi=100.0)
    ax = plt.gca()
    colors = ["windows blue", "amber", "dusty purple"]
    colors = [
        "windows blue",
        "amber",
        "greyish",
        "faded green",
        "dusty purple",
        "scarlet",
    ]
    # colors = ['#a6cee3', '#1f78b4', '#b2df8a', '#33a02c', '#fb9a99',
    #          '#e31a1c', '#fdbf6f', '#ff7f00', '#cab2d6', '#6a3d9a',
    #          '#ffff99', '#b15928']
    palette = sns.xkcd_palette(colors)
    sns.lineplot(x="Year", y="Mean", data=data, hue="Scenario",
                 linewidth=2, palette=palette, ax=ax)
    ax.set_title(f"Mean {npp_text}{t_ind}")
    ax.set_ylabel(f"Mean {npp_text}{t_ind}")
    ax.set_xlabel("Year")
    plt.savefig("Figure-1.png")
    plt.show()
    plt.close()
    return


def get_npp(land, npp, src):
    with rasterio.open(land) as ds:
        land = ds.read(1, masked=True, window=ds.window(*src.bounds))
    if npp:
        with rasterio.open(npp) as ds:
            npp = ds.read(1, masked=True, window=ds.window(*src.bounds))
    else:
        npp = ma.empty_like(land)
        npp.mask = land.mask
    return npp, land


@click.command()
@click.option("--npp", type=click.Path(dir_okay=False))
@click.option("--indicator", "-i", type=click.Choice(("BIIAb",
                                                      "Abundance",
                                                      "CompSimAb")),
              default="BIIAb")
@click.option("--raster-dir", "-r", type=click.Path(file_okay=False),
              default=Path(os.environ.get("OUTDIR", "/mnt/predicts"),
                           "rcp", "restore", "brazil"))
def worldwide(npp, indicator, raster_dir):
    land_area = None
    outdir = Path(os.environ.get("OUTDIR", "/mnt/predicts"), "rcp")
    df = pd.DataFrame(columns=["Year", "Scenario", "Mean"])
    if isinstance(raster_dir, str):
        raster_dir = Path(raster_dir)
    for path in filter(
        lambda p: fnmatch(p.name, f"*-{indicator}-20*.tif"),
        raster_dir.iterdir(),
    ):
        print(path)
        scenario, _, year= path.stem.split("-")
        with rasterio.open(path) as src:
            if not land_area:
                npp, land = get_npp(Path(outdir, "land.tif"), npp, src)
                land_area = (land * npp).sum()
            data = src.read(1, masked=True) * npp
            df = df.append(
                {
                    "Year": int(year),
                    "Scenario": scenario,
                    "Mean": ((data * land).sum() / (npp * np.where(data.mask, 0, 1) * land).sum()),
                },
                ignore_index=True,
            )

    data = df.sort_values(["Year", "Scenario"]).reset_index(drop=True)
    # print(df.loc[df.Scenario == 'early'])
    # print(df.loc[df.Scenario == 'late'])
    # print(data.loc[df.Scenario == 'base'])
    print(data)
    data.to_csv("brazil-summary.csv", index=False)
    plot_all(data, indicator, npp)
    return


if __name__ == "__main__":
    matplotlib.style.use("ggplot")
    sns.set_style("darkgrid")
    worldwide()
