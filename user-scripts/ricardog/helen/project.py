#!/usr/bin/env python3

import datetime
import click
from pathlib import Path
import rasterio
import rioxarray as rxr


from rasterset import RasterSet, Raster
from projutils import hpd, lui, utils
from projutils.utils import luh2_states, outfn
from projutils.lu.luh2 import LU
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
        mname = "AbundanceModel.rds"
    elif what == "cs-ab":
        mname = "CompositionalSimModel.rds"
    else:
        assert False, f"unknown what {what}"
    return modelr.load(model_dir / mname)


def get_scale_vars(what, model_dir):
    if what == "bii":
        return None
    if what == "ab":
        fname = "AbundanceModel_variables.csv"
    elif what == "cs-ab":
        fname = "CompositionalSimModel_variables.csv"
    else:
        assert False, f"unknown what {what}"
    return pd.read_csv(model_dir / fname)


def get_link(what):
    if what == "bii":
        return None
    if what == "ab":
        link = "pow"
    elif what == "cs-ab":
        link = "inv_logit"
    else:
        assert False, f"unknown what {what}"
    return link


def get_name(what):
    if what == "bii":
        return "BII"
    if what == "ab":
        return "Abundance"
    if what == "cs-ab":
        return "ComSimAb"
    assert False, f"unknown what {what}"


def read_states(scenario, years=None):
    if scenario == "historical":
        start_year = 850
    else:
        start_year = 2015
    states = rxr.open_rasterio(luh2_states(scenario), lock=False,
                               decode_times=False)[0]
    states = states.assign_coords(coords={"time": [datetime.datetime(start_year + x, 1, 1)
                                                   for x in states.time]})
    if years:
        states = states.sel(time=[datetime.datetime(y, 1, 1) for y in years])
    return states


def add_lu(rs):
    for name, expr in LU.items():
        if name != "urban":
            rs[name] = expr
    return


def add_ui(rs, prefix, suffix):
    for landuse in filter(lambda x: x != "timber", LU.keys()):
        #import pdb; pdb.set_trace()
        for band, intensity in enumerate(lui.intensities()):
            rs[f"{landuse}_{intensity}"] = lui.LUH2(landuse, intensity)
            ref_path = outfn("luh2", "%s-recal.tif" % landuse)
            rs[f"{landuse}_{intensity}_ref"] = Raster(ref_path, band + 1)
            if landuse[-9:] == "secondary":
                rs[f"{prefix}{landuse}_vegetation_{intensity}{suffix}"] = f"{landuse}_{intensity}"
            elif landuse == "primary":
                rs[f"{prefix}{landuse}_vegetation_{intensity}{suffix}"] = f"{landuse}_{intensity}"
            elif landuse == "pasture":
                rs[f"{prefix}managed_{landuse}_{intensity}{suffix}"] = f"{landuse}_{intensity}"
            else:
                rs[f"{prefix}{landuse}_{intensity}{suffix}"] = f"{landuse}_{intensity}"
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

    rs["secdy"] = "secdyf + secdyn"
    rs["secdi"] = "secdif + secdin"
    rs["secdm"] = "secdmf + secdmn"
    
    if year < 2015:
        rs["hpd"] = hpd.WPP("historical", year, utils.wpp_xls())
    else:
        rasters.update(hpd.sps.scale_grumps(utils.luh2_scenario_ssp(scenario),
                                            year))
    rs["scale_logstudy_hpd"] = 0
    
    # Add road density
    rs["road_length"] = Raster(outfn("luh2", "helen", "road-length-50.tif"))
    rs["road_density"] = "road_length / 7853981633.98"
    rs["scale_logstudy_roads"] = 0

    # Add natural habitat
    rs["natural_habitat"] = "primary + secondary"

    # Add climate anomaly
    rs["tmp_1930_mean"] = Raster(outfn("luh2", "helen", "tmp-1900-1930.tif"),
                                 band=1)
    rs["tmp_1930_std"] = Raster(outfn("luh2", "helen", "tmp-1900-1930.tif"),
                                band=2)
    add_lu(rs)
    add_ui(rs, "new_ui_", "_use")

    return rs


def scale_vars(what, model_dir, rs):
    df = get_scale_vars(what, model_dir)

    hpd = df.loc[df.variableName == "HPD"]
    rs["scale_log_hpd"] = "(log1p(hpd) - %f) / %f" % (hpd.mean, hpd.SD)

    roads = df.loc[df.variableName == "Road density in 50km"]
    rs["scale_log_roads"] = "(log1p(hpd) - %f) / %f" % (roads.mean, roads.SD)

    nathab = df.loc[df.variableName == "Proportion of natural habitat in 25km"]
    rs["scale_log_natural_habitat"] = "(log(natural_habitat) - %f) / %f" % (nathab.mean, nathab.SD)
    return

    
def do_model(what, scenario, year, model_dir, tree):
    name = get_name(what)
    link = get_link(what)
    mod = get_model(what, model_dir)
    rs = rasters(scenario, year)
    rs[mod.output] = mod
    if link == "pow":
        rs[what] = f"{link}({mod.output}, 2)"
    else:
        rs[what] = f"{link}({mod.output})"
    if tree:
        print(rs.tree(what))
        return
    import pdb; pdb.set_trace()
    data, meta = rs.eval(what)
    with rasterio.open(outfn("luh2", "helen",
                             f"{scenario}-{name}-{year}.tif"),
                       "w", **meta) as dst:
        dst.write(data.filled().squeeze(), indexes=1)
    return


@click.command()
@click.argument("what", type=click.Choice(("ab", "cs-ab", "bii")))
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


