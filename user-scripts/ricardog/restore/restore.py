#!/usr/bin/env python3

import click
import os
import pandas as pd
from pathlib import Path
from pylru import lrudecorator
import rasterio

from projutils import hpd
from rasterset import RasterSet, Raster, SimpleExpr
from projections.utils import data_file, luh2_static, luh2_layer, outfn
import r2py.modelr as modelr

# import pdb
SCENARIOS = ("fc", "fc_no_cra", "fc_no_sfa", "idc_amz", "idc_imp_f3", "no_fc")


class YearRangeParamType(click.ParamType):
    name = "year range"

    def convert(self, value, param, ctx):
        try:
            try:
                return [int(value)]
            except ValueError:
                values = value.split(":")
                if len(values) == 3:
                    low, high, inc = values
                elif len(values) == 2:
                    low, high = values
                    inc = "1"
                else:
                    raise ValueError
                return range(int(low), int(high), int(inc))
        except ValueError:
            self.fail("%s is not a valid year range" % value, param, ctx)


YEAR_RANGE = YearRangeParamType()


def get_model(what, model_dir):
    if what == "bii":
        return None
    if what == "ab":
        mname = "final_abund_model.rds"
    elif what == "cs-ab":
        mname = "final_compsim_model.rds"
    else:
        assert False, f"unknown what {what}"
    return modelr.load(os.path.join(model_dir, mname))


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


@lrudecorator(20)
def year_index(year, scenario):
    df = pd.read_csv(
        data_file("restore", "brazil", brazil_dirname(scenario) + ".CSV"), header=None
    )
    df.columns = ["Country", "Cell", "LandUse", "Year", "Area"]
    years = sorted(df.Year.astype(int).unique())
    try:
        return years.index(year)
    except ValueError:
        print(f"No data for year {year} in scenario {scenario}")
        exit(1)
    return


def globiom_layer(layer, scenario):
    return outfn("luh2", "restore", "brazil", brazil_dirname(scenario), f"{layer}.tif")


def regrowth(scenario):
    return Path(globiom_layer("Regrowth", scenario)).exists()


def rasters(ssp, scenario, year):
    bidx = year_index(year, scenario) + 1
    rasters = {}

    # Compute land area of each cell
    rasters["carea"] = Raster("carea", luh2_static("carea"))
    rasters["icwtr"] = Raster("icwtr", luh2_static("icwtr"))
    rasters["land"] = Raster("land", outfn("luh2", "gpw-land.tif"))

    # UN Subregion and UN country code
    rasters["hpd_ref"] = Raster("hpd_ref", outfn("luh2", "gluds00ag.tif"))
    rasters["unSub"] = Raster("unSub", outfn("luh2", "un_subregions-full.tif"))
    rasters["un_code"] = Raster("un_codes", outfn("luh2", "un_codes-full.tif"))

    rasters["cube_rt_env_dist"] = SimpleExpr("cube_rt_env_dist", 0)
    rasters["log_adj_geog_dist"] = SimpleExpr("log_adj_geog_dist", 0)

    # Compute human population density
    if year < 2015:
        raise IndexError(f"year must be greater than 2014 ({year})")
    else:
        hpd_dict = hpd.sps.raster(ssp, year, "luh2")
    rasters["pop"] = hpd_dict["hpd"]
    rasters["hpd"] = SimpleExpr("hpd", "pop / land")
    rasters["log_hpd30sec"] = SimpleExpr("log_hpd30sec", "log(hpd + 1)")

    # Road density
    rasters["r_dlte2_10"] = Raster(
        "r_dlte2_10", outfn("luh2", "RDlte2_10km-avgerage.tif")
    )
    rasters["log_r_dlte2_10"] = SimpleExpr("log_r_dlte2_10", "log(r_dlte2_10 + 1)")

    # import pdb; pdb.set_trace()
    if not regrowth(scenario):
        rasters["secdi"] = SimpleExpr("secdi", 0)
        rasters["secdy"] = SimpleExpr("secdy", 0)
    else:
        rasters["secdi"] = Raster(
            "secdi",
            outfn("luh2", "restore", "brazil", brazil_dirname(scenario), "secdi.tif"),
            band=bidx,
        )
        rasters["regrowth"] = Raster(
            "regrowth", globiom_layer("Regrowth", scenario), band=bidx
        )
        rasters["secdy"] = SimpleExpr("secdy", "regrowth - secdi")

    # Read the raw GLOBIOM rasters.  These may be scaled to add urban
    # from the LUH2 dataset.
    rasters["cropland"] = Raster(
        "cropland", globiom_layer("CropLand", scenario), band=bidx
    )
    rasters["forest"] = Raster("forest", globiom_layer("Forest", scenario), band=bidx)
    rasters["oth_agri"] = Raster(
        "oth_agri", globiom_layer("OthAgri", scenario), band=bidx
    )
    rasters["pasture"] = Raster(
        "pasture", globiom_layer("Pasture", scenario), band=bidx
    )
    rasters["plt_for"] = Raster("plt_for", globiom_layer("PltFor", scenario), band=bidx)

    ssp_scenario = "SSP2_RCP4.5_MESSAGE-GLOBIOM"
    rasters["urban"] = Raster(
        "urban", luh2_layer(ssp_scenario, "urban"), band=year - 2015 + 1
    )
    rasters["scale"] = SimpleExpr("scale", "(1)")
    rasters["unscale"] = SimpleExpr("unscale", 0)

    # Land-use layers.  Iterate twice with different prefix; one is for
    # the abundance model the other is for the compositional similarity
    # model.
    for prefix in ("globiom_lu_proj", "contrast_proj_p_as"):
        rasters[f"{prefix}_cropland"] = SimpleExpr(
            f"{prefix}_cropland", "cropland * scale"
        )
        rasters[f"{prefix}_forest"] = SimpleExpr(f"{prefix}_forest", "forest * scale")
        rasters[f"{prefix}_oth_agri"] = SimpleExpr(
            f"{prefix}_oth_agri", "oth_agri * scale"
        )
        rasters[f"{prefix}_pasture"] = SimpleExpr(
            f"{prefix}_pasture", "pasture * scale"
        )
        rasters[f"{prefix}_plt_for"] = SimpleExpr(
            f"{prefix}_plt_for", "plt_for * scale"
        )
        rasters[f"{prefix}_urban"] = SimpleExpr(f"{prefix}_urban", "urban * unscale")
        rasters[f"{prefix}_secondary_intermediate"] = SimpleExpr(
            f"{prefix}_secdi", "secdi * scale"
        )
        rasters[f"{prefix}_secondary_young"] = SimpleExpr(
            f"{prefix}_secdy", "secdy * scale"
        )
    return rasters


def inv_transform(what, output, intercept):
    if what == "ab":
        oname = "Abundance"
        expr = SimpleExpr(oname, "pow(%s, 2) / pow(%f, 2)" % (output, intercept))
    else:
        oname = "CompSimAb"
        expr = SimpleExpr(
            oname,
            "(inv_logit(%s) - 0.01) /" "(inv_logit(%f) - 0.01)" % (output, intercept),
        )
    return oname, expr


def do_model(what, ssp, scenario, year, model, tree):
    rs = RasterSet(rasters(ssp, scenario, year))
    rs[model.output] = model
    intercept = model.intercept
    oname, expr = inv_transform(what, model.output, intercept)
    rs[oname] = expr
    if tree:
        print(rs.tree(oname))
        return
    data, meta = rs.eval(oname, quiet=True)
    fname = f"restore-{scenario}-{oname}-{year}.tif"
    with rasterio.open(outfn("luh2", "restore", "brazil", fname), "w", **meta) as dst:
        dst.write(data.filled(), indexes=1)
    return


def do_bii(oname, scenario, years):
    for year in years:
        rs = RasterSet(
            {
                oname: SimpleExpr("bii", "ab * cs"),
                "cs": Raster(
                    "cs",
                    outfn(
                        "luh2",
                        "restore",
                        "brazil",
                        f"restore-{scenario}-CompSimAb-{year}.tif",
                    ),
                ),
                "ab": Raster(
                    "ab",
                    outfn(
                        "luh2",
                        "restore",
                        "brazil",
                        f"restore-{scenario}-Abundance-{year}.tif",
                    ),
                ),
            }
        )
        # print(rs.tree(oname))
        data, meta = rs.eval(oname, quiet=True)
        with rasterio.open(
            outfn(
                "luh2", "restore", "brazil", f"restore-{scenario}-{oname}-{year}.tif"
            ),
            "w",
            **meta,
        ) as dst:
            dst.write(data.filled(), indexes=1)
    return


def do_other(vname, ssp, scenario, year, tree):
    rs = RasterSet(rasters(ssp, scenario, year))
    if tree:
        print(rs.tree(vname))
        return
    data, meta = rs.eval(vname, quiet=True)
    with rasterio.open(
        outfn("luh2", "restore", "brazil", f"restore-{scenario}-{vname}-{year}.tif"),
        "w",
        **meta,
    ) as dst:
        dst.write(data.filled(), indexes=1)
    return


@click.group(invoke_without_command=True)
@click.pass_context
def cli(ctx):
    if ctx.invoked_subcommand is None:
        click.echo("I was invoked without subcommand")
        project()
    else:
        # click.echo('I am about to invoke %s' % ctx.invoked_subcommand)
        pass


@cli.command()
@click.argument("what", type=click.Choice(("ab", "cs-ab", "other")))
@click.argument("scenario", type=click.Choice(SCENARIOS))
@click.argument("years", type=YEAR_RANGE)
@click.option(
    "-m",
    "--model-dir",
    type=click.Path(file_okay=False),
    default=os.path.abspath("."),
    help="Directory where to find the models " + "(default: ./models)",
)
@click.option(
    "-v",
    "--vname",
    type=str,
    default=None,
    help="Variable to project when specifying other.",
)
@click.option("-t", "--tree", is_flag=True, default=False)
def project(what, scenario, years, model_dir, vname, tree):
    ssp = "ssp2"
    if what == "other":
        if vname is None:
            raise ValueError("Please specify a variable name")

    for year in years:
        if what == "other":
            do_other(vname, ssp, scenario, year, tree)
        else:
            model = get_model(what, model_dir)
            do_model(what, ssp, scenario, year, model, tree)
    return


@cli.command()
@click.argument("what", type=click.Choice(("bii",)))
@click.argument("scenario", type=click.Choice(SCENARIOS))
@click.argument("years", type=YEAR_RANGE)
def combine(what, scenario, years):
    if what == "bii":
        do_bii("BIIAb", scenario, years)
    return


if __name__ == "__main__":
    cli()
