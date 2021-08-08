#!/usr/bin/env python3

import datetime
import click
from pathlib import Path
import rasterio
import rioxarray as rxr

from rasterset import RasterSet, Raster
from projutils import hpd, lui, utils
from projutils.utils import data_file, luh2_states, outfn
import r2py.modelr as modelr


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
        mname = "soil_abundance.rds"
    elif what == "sr":
        mname = "soil_richness.rds"
    else:
        assert False, f"unknown what {what}"
    return modelr.load(model_dir.joinpath(mname))


def get_link(what):
    if what == "bii":
        return None
    if what == "ab":
        link = "expm1"
    elif what == "sr":
        link = "expm1"
    else:
        assert False, f"unknown what {what}"
    return link


def get_name(what):
    if what == "bii":
        return "BII"
    if what == "ab":
        return "Abundance"
    if what == "sr":
        return "Richness"
    assert False, f"unknown what {what}"


def read_states(scenario, years=None):
    states = rxr.open_rasterio(luh2_states(scenario), lock=False,
                               decode_times=False)[0]
    states = states.assign_coords(coords={"time": [datetime.datetime(850 + x, 1, 1)
                                                   for x in states.time]})
    if years:
        states = states.sel(time=[datetime.datetime(y, 1, 1) for y in years])
    return states


def add_ui(rs):
    for landuse in ["cropland", "pasture", "primary", "plantation_pri",
                    "secondary", "urban"]:
        for band, intensity in enumerate(lui.intensities()):
            rs[f"{landuse}_{intensity}"] = lui.LUH5(landuse, intensity)
        if landuse != "plantation_pri":
            # plantation_pri doesn't have a UI model.
            if landuse == "secondary":
                ref_path = outfn("luh2", "secdyf-recal.tif")
            else:
                ref_path = outfn("luh2", "%s-recal.tif" % landuse)
            rs[f"{landuse}_ref"] = Raster(ref_path, band + 1)
    return


def rasters(scenario, year):
    rs = RasterSet({
        "unSub": Raster(outfn("luh2", "un_subregions.tif")),
        "un_code": Raster(outfn("luh2", "un_codes.tif")),
        "hpd_ref": Raster(outfn("luh2", "gluds00ag.tif")),
    })

    states = read_states(scenario, (year, ))
    secd = rxr.open_rasterio(outfn("luh2", f"secd-{scenario}.nc"),
                             lock=False, decode_times=0)
    secd = secd.assign_coords(coords={"time": [datetime.datetime(850 + x, 1, 1)
                                               for x in secd.time]})
    secd = secd.sel(time=[datetime.datetime(year, 1, 1)])
    rs.update(states)
    rs.update(secd)

    rs["raw_bd"] = Raster(outfn("luh2", "soil-grids",
                                "bdod.tif"))
    rs["raw_clay"] = Raster(outfn("luh2", "soil-grids",
                                "clay.tif"))
    rs["raw_phho"] = Raster(outfn("luh2", "soil-grids",
                                "phh2o.tif"))

    rs["bd"] = "scale(raw_bd, 0, 1)"
    rs["clay"] = "scale(raw_clay, 0, 1)"
    rs["phho"] = "scale(raw_phho, 0, 1)"
    rs["oc"] = 0.1907555

    if year < 2015:
        rs["hpd"] = hpd.WPP("historical", year, utils.wpp_xls())
    else:
        rasters.update(hpd.sps.scale_grumps(utils.luh2_scenario_ssp(scenario),
                                            year))

    add_ui(rs)
    
    rs["cropland"] = "c3ann + c4ann + c3nfx"
    rs["pasture"] = "range + pastr"
    rs["plantation_pri"] =  "c3per + c4per"
    rs["primary"] = "primf + primn"
    rs["secondary"] = "secdf + secdn"

    rs["land_use_cropland"] = "cropland"
    rs["land_use_pasture"] = "pasture"
    rs["land_use_plantation_forest"] = "plantation_pri"
    rs["land_use_primary"] = "primary"
    rs["land_use_secondary_vegetation"] = "secondary"
    rs["land_use_urban"] = "urban"

    rs["u_imin_urban"] = "urban"
    rs["u_imin_cropland_minimal_use"] = "cropland_minimal"
    rs["u_imin_cropland_light_use"] = "cropland_light"
    rs["u_imin_cropland_intense_use"] = "cropland_intense"
    rs["u_imin_pasture_minimal_use"] = "pasture_minimal"
    rs["u_imin_pasture_light_use"] = "pasture_light"
    rs["u_imin_pasture_intense_use"] = "pasture_intense"
    rs["u_imin_primary_vegetation_minimal_use"] = "primary_minimal"
    rs["u_imin_primary_vegetation_light_use"] = "primary_light"
    rs["u_imin_primary_vegetation_intense_use"] = "primary_intense"
    rs["u_imin_secondary_vegetation_minimal_use"] = "secondary_minimal"
    rs["u_imin_secondary_vegetation_light_use"] = "secondary_light"
    rs["u_imin_secondary_vegetation_intense_use"] = "secondary_intense"
    rs["u_imin_plantation_forest_minimal_use"] = "plantation_pri_minimal"
    rs["u_imin_plantation_forest_light_use"] = "plantation_pri_light"
    rs["u_imin_plantation_forest_intense_use"] = "plantation_pri_intense"
    
    return rs


def do_model(what, scenario, year, model_dir, tree):
    name = get_name(what)
    link = get_link(what)
    mod = get_model(what, model_dir)
    rs = rasters(scenario, year)
    rs[mod.output] = mod
    rs[what] = f"{link}({mod.output})"
    if tree:
        print(rs.tree(what))
        return
    data, meta = rs.eval(what)
    with rasterio.open(outfn("luh2", "soilbii",
                             f"{scenario}-{name}-{year}.tif"),
                       "w", **meta) as dst:
        dst.write(data.filled().squeeze(), indexes=1)
    return


@click.command()
@click.argument("what", type=click.Choice(("ab", "sr")))
@click.argument(
    "scenario",
    type=click.Choice(utils.luh2_scenarios()),
    default="historical"
)
@click.argument("years", type=YEAR_RANGE)
@click.option(
    "-m",
    "--model-dir",
    type=click.Path(file_okay=False),
    default=Path(".").resolve(),
    help="Directory where to find the models " + "(default: ./models)",
)
@click.option("-t", "--tree", is_flag=True, default=False)
def project(what, scenario, years, model_dir, tree):
    for year in years:
        do_model(what, scenario, year, Path(model_dir), tree)
    return


if __name__ == '__main__':
    project()
