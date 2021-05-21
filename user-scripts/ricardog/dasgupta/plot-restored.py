#!/usr/bin/env python3

import click
import matplotlib.pyplot as plt
from pathlib import Path
import pandas as pd
import rasterio
import seaborn as sns


@click.command()
@click.argument("scenario", type=str)
def doit(scenario):
    base_dir = "/Users/ricardog/src/eec/data/vivid"
    scene_dir = Path(base_dir, scenario)
    if not scene_dir.is_dir():
        print(f"No data for {scenario} found")
        return
    dname = f"{base_dir}/{scenario}/spatial_files/restored_land"
    outdir = "/Users/ricardog/src/eec/predicts/playground/ds"
    odir = f"{outdir}/rcp"
    land_file = f"{odir}/land.tif"
    df = pd.DataFrame(columns=["Year", "LU", "Area"])

    with rasterio.open(land_file) as src:
        land = src.read(1, masked=True)
    land_sum = land.sum()

    with rasterio.open(f"{odir}/nonforested.tif") as ds:
        nonforest = ds.read(1, masked=True)

    for year in range(2020, 2061, 5):
        for lu in ("sf", "mf"):
            with rasterio.open(f"{dname}/restored_{lu}_{year}.tif") as src:
                data = src.read(1, masked=True)
                df = df.append(
                    {"Year": year, "LU": lu, "Area": data.sum() / land_sum * 100.0},
                    ignore_index=True,
                )
                df = df.append(
                    {
                        "Year": year,
                        "LU": f"{lu}-nf",
                        "Area": (data * nonforest).sum() / land_sum * 100.0,
                    },
                    ignore_index=True,
                )
    print(df)
    print(df.Area.sum())
    sns.lineplot("Year", "Area", hue="LU", data=df)
    ax = plt.gca()
    ax.set_title(f"Restored Land ({scenario})")
    ax.set_ylabel("Area (%)")
    plt.show()
    return


if __name__ == "__main__":
    doit()
