#!/usr/bin/env python3

from bokeh.io import output_file, show, save
from bokeh.layouts import gridplot
from bokeh.models import Range1d, ColumnDataSource, HoverTool, CrosshairTool
from bokeh.palettes import Category20, brewer, viridis
from bokeh.plotting import figure

import click
import fiona
import matplotlib.pyplot as plt
import joblib
import numpy as np
import pandas as pd

import projections.utils as utils

import pdb


def get_ipbes_regions():
    with fiona.open(
        utils.outfn("vector", "ipbes_land_shape", "ipbes_land.shp")
    ) as shapes:
        props = tuple(
            filter(lambda x: x.get("type") == "Land", (s["properties"] for s in shapes))
        )
        return pd.DataFrame(
            {
                "ID": tuple(int(s.get("OBJECTID")) for s in props),
                "Name": tuple(s.get("IPBES_sub") for s in props),
            }
        )


def stacked(df):
    """Convert a Pandas df to a stacked structure suitable for plotting."""
    df_top = df.cumsum(axis=1)
    df_bottom = df_top.shift(axis=1).fillna(0)[::-1]
    df_stack = pd.concat([df_bottom, df_top], ignore_index=True)
    return df_stack


def with_bokeh(scene, data):
    df = pd.DataFrame(data)
    df[0] = pd.to_numeric(df[0], downcast="integer")
    df.set_index(0, inplace=True)
    df.columns = ["Cropland", "Pasture", "Primary", "Secondary", "Urban", "Human NPP"]
    areas = stacked(df)
    colors = viridis(areas.shape[1])
    x2 = np.hstack((df.index[::-1], df.index))

    source = ColumnDataSource(
        data={
            "year": [x2] * areas.shape[1],
            "data": [areas[c].values for c in areas],
            "color": viridis(areas.shape[1]),
            "label": areas.columns,
        }
    )

    p = figure(title=scene)
    p.y_range = Range1d(0, 100)
    for idx, col in enumerate(subset.columns):
        if col in ("Year", "Excluded"):
            continue
        pline(p, subset, col, mypalette[idx], 4)
    pline(p, glob, "Global", "black")
    p.add_tools(
        HoverTool(
            tooltips=[("Year", "@year"), (indicator, "@data"), ("Region", "@name")]
        )
    )
    row.append(p)
    plots.append(row)
    grid = gridplot(plots, sizing_mode="scale_width")
    if out:
        output_file(out)
    save(grid)

    ax = all_axes.pop(0)
    ax.stackplot(
        years,
        (crop, past, prim, secd, urbn),
        labels=["Cropland", "Pasture", "Primary", "Secondary", "Urban"],
    )
    ax.plot(years, human, "k-", linewidth=3, label="Human NPP")
    ax.set_ylabel("Fraction of land surface (%)")
    ax.set_xlabel("Year")
    ax.set_title(scene)
    ax.grid("on")
    if add_legend:
        ax.legend(loc="center left")
        add_legend = False


@click.group()
def cli():
    pass


@cli.command()
@click.option(
    "--data-file", "-d", type=click.Path(dir_okay=False), default="overtime.dat"
)
@click.option("--use_bokeh", "-b", is_flag=True, default=False)
def overplot(data_file, use_bokeh):
    storage = joblib.load(data_file)
    historical = storage["historical"].T
    del storage["historical"]

    pdb.set_trace()
    fig, axes = plt.subplots(2, 3)
    all_axes = [ax for sublist in axes for ax in sublist]

    add_legend = True
    for scene in sorted(storage.keys()):
        arr = np.vstack((historical, storage[scene].T))
        if use_bokeh:
            with_bokeh(scene, arr)
            continue

        years, crop, past, prim, secd, urbn, human = tuple(
            map(
                lambda v: v.reshape(
                    v.shape[0],
                ),
                np.hsplit(arr, arr.shape[1]),
            )
        )
        ax = all_axes.pop(0)
        ax.stackplot(
            years,
            (crop, past, prim, secd, urbn),
            labels=["Cropland", "Pasture", "Primary", "Secondary", "Urban"],
        )
        ax.plot(years, human, "k-", linewidth=3, label="Human NPP")
        ax.set_ylabel("Fraction of land surface (%)")
        ax.set_xlabel("Year")
        ax.set_title(scene)
        ax.grid("on")
        if add_legend:
            ax.legend(loc="center left")
            add_legend = False

    for ax in all_axes:
        fig.delaxes(ax)
    plt.show()


@cli.command()
@click.option(
    "--data-file", "-d", type=click.Path(dir_okay=False), default="overtime.dat"
)
def to_csv(data_file):
    df = get_ipbes_regions()
    columns = ["Global"] + df.Name.values.tolist()
    storage = joblib.load(data_file)
    historical = storage["historical"].T
    del storage["historical"]

    # pdb.set_trace()
    for scene in sorted(storage.keys()):
        # arr = np.vstack((historical, storage[scene].T))
        arr = storage[scene]
        years = arr[0, :, 0].astype(int)
        for idx, name in enumerate(
            ("Cropland", "Pasture", "Primary", "Secondary", "Urban")
        ):
            data = arr[idx + 1, :, :]
            lu = pd.DataFrame(arr[idx + 1, :, :], index=years, columns=columns)
            lu.to_csv("%s-%s.csv" % (scene, name))


if __name__ == "__main__":
    cli()
