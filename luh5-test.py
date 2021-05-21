#!/usr/bin/env python

import click
import fiona
import itertools
import matplotlib.colors as colors
import matplotlib.pyplot as plt
import multiprocessing
import numpy as np
import numpy.ma as ma
import os
import sys
import time
import rasterio
from rasterio.plot import show, show_hist

import pdb

from rasterset import RasterSet, Raster, SimpleExpr

import projections.r2py.modelr as modelr
from projections.r2py import pythonify
import projections.utils as utils


class YearRangeParamType(click.ParamType):
    name = "year range"

    def convert(self, value, param, ctx):
        try:
            try:
                return [int(value)]
            except ValueError:
                l, h = value.split(":")
                return range(int(l), int(h))
        except ValueError:
            self.fail("%s is not a valid year range" % value, param, ctx)


YEAR_RANGE = YearRangeParamType()


def select_models(model, model_dir):
    if model == "ab":
        mod = "ab-model.rds"
    elif model == "sr":
        mod = "sr-model.rds"
    else:
        mod = "bii-model.rds"
    return [os.path.join(model_dir, mod)]


def project_year(model, model_dir, what, scenario, year):
    print("projecting %s for %d using %s" % (what, year, scenario))

    models = select_models(model, model_dir)
    # Read Sam's abundance model (forested and non-forested)
    mod = modelr.load(models[0])
    pythonify(mod)

    # Import standard PREDICTS rasters
    by_age = "young_secondary" in mod.syms
    print("by_age: %s" % str(by_age))
    rasters = predicts.rasterset("luh5", scenario, year, by_age)
    rs = RasterSet(rasters)

    if what == "bii":
        vname = "bii"
        rs[vname] = SimpleExpr(vname, "%s / %f" % (mod.output, intercept))
    else:
        vname = mod.output
    rs[vname] = mod

    if what not in rs:
        print("%s not in rasterset" % what)
        print(", ".join(sorted(rs.keys())))
        sys.exit(1)

    stime = time.time()
    data, meta = rs.eval(what, quiet=False)
    etime = time.time()
    print("executed in %6.2fs" % (etime - stime))
    oname = os.path.join(
        os.environ["OUTDIR"], "luh5/%s-%s-%d.tif" % (scenario, what, year)
    )
    # hpd, _ = rs.eval('hpd', quiet=False)
    # hpd_max, meta2 = rs.eval('hpd_max', quiet=False)
    with rasterio.open(oname, "w", **meta) as dst:
        # bb = dst.bounds
        # ul = map(int, ~meta2['affine'] * (bb[0], bb[3]))
        # lr = map(int, ~meta2['affine'] * (bb[2], bb[1]))
        # cap = ma.where(hpd > hpd_max[ul[1]:lr[1], ul[0]:lr[0]], True, False)
        # show(hpd, norm=colors.PowerNorm(gamma=0.2))
        # show(cap * 1)
        # data.mask = np.logical_or(data.mask, cap)
        dst.write(data.filled(meta["nodata"]), indexes=1)
    if None:
        fig = plt.figure(figsize=(8, 6))
        ax = plt.gca()
        show(data, cmap="viridis", ax=ax)
        plt.savefig("luh2-%s-%d.png" % (scenario, year))
    return


def unpack(args):
    project_year(*args)


@click.command()
# @click.argument('what', type=click.Choice(['ab', 'sr']))
@click.argument("model", type=click.Choice(["ab", "sr", "bii"]))
@click.argument("what", type=str)
@click.argument("scenario", type=click.Choice(utils.luh2_scenarios()))
@click.argument("years", type=YEAR_RANGE)
@click.option(
    "--model-dir",
    "-m",
    type=click.Path(file_okay=False),
    default=os.path.join("..", "models"),
    help="Directory where to find the models " + "(default: ../models)",
)
@click.option(
    "--parallel",
    "-p",
    default=1,
    type=click.INT,
    help="How many projections to run in parallel (default: 1)",
)
def project(model, what, scenario, years, model_dir, parallel=1):
    if parallel == 1:
        for y in years:
            project_year(model, model_dir, what, scenario, y)
        return
    pool = multiprocessing.Pool(processes=parallel)
    pool.map(
        unpack,
        itertools.izip(
            itertools.repeat(model),
            itertools.repeat(model_dir),
            itertools.repeat(what),
            itertools.repeat(scenario),
            years,
        ),
    )


if __name__ == "__main__":
    project()
