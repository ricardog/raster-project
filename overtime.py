#!/usr/bin/env python3

import math
import sys

import click
import fiona
import joblib
import matplotlib.pyplot as plt
from multiprocessing import Pool as ThreadPool
from netCDF4 import Dataset
import numpy as np
import numpy.ma as ma
import pandas as pd
import rasterio

import projections.utils as utils

import pdb


class YearRangeParamType(click.ParamType):
    name = "year range"

    def convert(self, value, param, ctx):
        try:
            try:
                return [int(value)]
            except ValueError:
                low, high = value.split(":")
                return range(int(low), int(high))
        except ValueError:
            self.fail("%s is not a valid year range" % value, param, ctx)


YEAR_RANGE = YearRangeParamType()


def sum_by(regions, data):
    data.mask = np.logical_or(data.mask, regions.mask)
    regions.mask = ma.getmask(data)
    regions_idx = regions.compressed().astype(int)
    summ = np.bincount(regions_idx, data.compressed())
    ncells = np.bincount(regions_idx)
    idx = np.where(ncells > 0)
    return summ[idx]


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


def compute_data(scene, storage, total, regions=None):
    with Dataset(utils.luh2_static()) as static:
        carea = static.variables["carea"][:]

    with Dataset(utils.luh2_states(scene)) as ds:
        base_year = 850 if scene == "historical" else 2015
        years = ds.variables["time"][:] + base_year
        crop = np.zeros((len(years), total.shape[0]))
        past = np.zeros((len(years), total.shape[0]))
        prim = np.zeros((len(years), total.shape[0]))
        secd = np.zeros((len(years), total.shape[0]))
        urbn = np.zeros((len(years), total.shape[0]))

        for year in years:
            idx = int(year) - base_year
            click.echo("year: %d" % int(year))
            cr = (
                ds.variables["c3ann"][idx, :, :]
                + ds.variables["c4ann"][idx, :, :]
                + ds.variables["c3per"][idx, :, :]
                + ds.variables["c4per"][idx, :, :]
                + ds.variables["c3nfx"][idx, :, :]
            )
            pa = ds.variables["range"][idx, :, :] + ds.variables["pastr"][idx, :, :]
            pr = ds.variables["primf"][idx, :, :] + ds.variables["primn"][idx, :, :]
            se = ds.variables["secdf"][idx, :, :] + ds.variables["secdn"][idx, :, :]
            ur = ds.variables["urban"][idx, :, :]

            crop[idx, 0] = (carea * cr).sum() / total[0] * 100
            past[idx, 0] = (carea * pa).sum() / total[0] * 100
            prim[idx, 0] = (carea * pr).sum() / total[0] * 100
            secd[idx, 0] = (carea * se).sum() / total[0] * 100
            urbn[idx, 0] = (carea * ur).sum() / total[0] * 100

            if regions is not None:
                crop[idx, 1:] = sum_by(regions, carea * cr) / total[1:] * 100
                past[idx, 1:] = sum_by(regions, carea * pa) / total[1:] * 100
                prim[idx, 1:] = sum_by(regions, carea * pr) / total[1:] * 100
                secd[idx, 1:] = sum_by(regions, carea * se) / total[1:] * 100
                urbn[idx, 1:] = sum_by(regions, carea * ur) / total[1:] * 100

    dim2 = total.shape[0]
    yy = np.repeat(years, dim2).reshape(years.shape[0], dim2)
    storage[scene] = np.stack((yy, crop, past, prim, secd, urbn))


@click.group(invoke_without_command=False)
@click.pass_context
def cli(ctx):
    pass


@cli.command()
@click.argument("scenario", type=click.Choice(utils.luh2_scenarios() + ("all",)))
@click.argument("years", type=YEAR_RANGE)
def means(scenario, years):
    """Calculate and plot land use over time.

    Also compute what fraction of NPP is taken by humans.

    """

    if scenario != "all":
        utils.luh2_check_year(min(years), scenario)
        utils.luh2_check_year(max(years), scenario)

    with Dataset(utils.luh2_static()) as static:
        carea = static.variables["carea"][:]
        land = 1 - static.variables["icwtr"][:]

    total = (carea * land).sum()

    if scenario != "all":
        scenarios = (scenario,)
    else:
        scenarios = ("historical",) + tuple(
            filter(lambda s: s != "historical", utils.luh2_scenarios())
        )
        print(scenarios)

    storage = {}
    for scene in scenarios:
        compute_data(scene, storage, np.array([total]))
    joblib.dump(storage, "overtime.dat", compress=True)


@cli.command()
@click.argument("scenario", type=click.Choice(utils.luh2_scenarios() + ("all",)))
@click.argument("years", type=YEAR_RANGE)
@click.option(
    "--regions",
    "-r",
    type=click.Path(dir_okay=False),
    help="Specify regions to categorize land-use by.",
)
def sums(scenario, years, regions):
    """Calculate and plot land use over time, broken up by IPBES region."""

    df = get_ipbes_regions()

    if scenario != "all":
        utils.luh2_check_year(min(years), scenario)
        utils.luh2_check_year(max(years), scenario)

    with Dataset(utils.luh2_static()) as static:
        carea = static.variables["carea"][:]
        land = 1 - static.variables["icwtr"][:]

    if regions:
        with rasterio.open(regions) as regions_ds:
            # Adjust read area so raster is the full 1440x720 resolution
            regions = regions_ds.read(
                1, masked=True, window=((-25, 695), (0, 1440)), boundless=True
            )
    total = np.zeros(len(df) + 1)
    total_land = ma.masked_array(carea * land)
    total[0] = total_land.sum()
    if regions is not None:
        total[1:] = sum_by(regions, total_land)
        total = np.where(total == 0.0, 1e-5, total)
        print(total)
        print(total[0])
        print(total[1:].sum())

    if scenario != "all":
        scenarios = (scenario,)
    else:
        scenarios = ("historical",) + tuple(
            filter(lambda s: s != "historical", utils.luh2_scenarios())
        )

    storage = {}
    for scene in scenarios:
        compute_data(scene, storage, total, regions)
    joblib.dump(storage, "overtime.dat", compress=True)


if __name__ == "__main__":
    # pylint: disable-msg=no-value-for-parameter
    cli()
# pylint: enable-msg=no-value-for-parameter
