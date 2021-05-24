from functools import reduce
import netCDF4
import os

from rasterset import Raster, SimpleExpr

from . import hpd
from . import lu
from . import lui
from . import utils
from .utils import outfn


def rcp(scenario, year, hpd_trend):
    rasters = {}

    lus = [
        SimpleExpr("primary", "gothr - gfvh1 - gfvh2"),
        SimpleExpr("secondary", "max(gsecd - gfsh1 - gfsh2 - gfsh3, 0)"),
        SimpleExpr("cropland", "gcrop"),
        SimpleExpr("pasture", "gpast"),
        SimpleExpr("urban", "gurbn"),
        SimpleExpr("plantation_pri", "min(gothr, gfvh1 + gfvh2)"),
        SimpleExpr("plantation_sec", "min(gsecd, gfsh1 + gfsh2 + gfsh3)"),
    ]

    # Human population density and UN subregions
    rasters["hpd_ref"] = Raster("hpd_ref", outfn("rcp", "gluds00ag.tif"))
    rasters["unSub"] = Raster("unSub", outfn("rcp", "un_subregions.tif"))
    rasters["un_code"] = Raster("un_codes", outfn("rcp", "un_codes.tif"))
    rasters["hpd"] = hpd.WPP(hpd_trend, year, utils.wpp_xls())

    # NOTE: Pass max & min of log(HPD) so hi-res rasters can be processed
    # incrementally.  Recording the max value here for when I create
    # other functions for other resolutions.
    # 0.50 =>  20511.541 / 9.92874298232494
    # 0.25 =>  41335.645 / 10.62948048177454
    # 1km  => 872073.500 / 13.678628988329825
    rasters["logHPD_rs"] = SimpleExpr(
        "logHPD_rs", "scale(log(hpd + 1), 0.0, 1.0, 0.0, 9.93)"
    )
    rasters["logDistRd_rs"] = Raster("logDistRd_rs", outfn("rcp", "roads-final.tif"))

    # Inputs RCP rasters
    names = tuple(set(reduce(lambda x, y: x + y, [list(lu.syms) for lu in lus], [])))

    for name in names:
        path = outfn(
            "lu", "rcp", scenario, "updated_states", "%s.%d.tif" % (name, year)
        )
        rasters[name] = Raster(name, path)

    # Land use intensity rasters
    for landuse in lus:
        rasters[landuse.name] = landuse
        ref_path = outfn("rcp", "%s-recal.tif" % landuse.name)
        for band, intensity in enumerate(lui.intensities()):
            n = landuse.name + "_" + intensity
            rasters[n] = lui.RCP(landuse.name, intensity)
            n2 = n + "_ref"
            if landuse.name[0:11] == "plantation_":
                rasters[n2] = SimpleExpr(n2, "0")
            else:
                rasters[n2] = Raster(n2, ref_path, band + 1)
    return rasters


def luh5(scenario, year, plus3):
    rasters = {}

    lus = [
        SimpleExpr("primary", "primf + primn"),
        SimpleExpr("cropland", "c3ann + c4ann + c3nfx"),
        SimpleExpr("pasture", "range + pastr"),
        SimpleExpr("plantation_pri", "c3per + c4per"),
        SimpleExpr("plantation_sec", "0"),
    ]

    if plus3:
        lus += [
            SimpleExpr("secdm", "secdmf + secdmn"),
            SimpleExpr("secdi", "secdif + secdin"),
            SimpleExpr("secdy", "secdyf + secdyn"),
        ]
        rasters["secondary"] = SimpleExpr("secondary", "secdy + secdi + secdm")
    else:
        lus += [SimpleExpr("secondary", "secdf + secdn")]

    # Human population density and UN subregions
    rasters["unSub"] = Raster("unSub", outfn("luh2", "un_subregions.tif"))
    rasters["un_code"] = Raster("un_codes", outfn("luh2", "un_codes.tif"))
    # rasters.update(hpd.sps.raster(ssp, year))
    if year < 2015:
        rasters["hpd_ref"] = Raster("hpd_ref", outfn("luh2", "gluds00ag.tif"))
        rasters["hpd"] = hpd.WPP("historical", year, utils.wpp_xls())
    else:
        rasters.update(hpd.sps.scale_grumps(utils.luh2_scenario_ssp(scenario), year))
    # The values in the expression of hpd_max need to be updated when the
    # predicts DB changes.
    rasters["hpd_max"] = SimpleExpr(
        "hpd_max",
        "(primary * 39.810) + (cropland * 125.40) + "
        "(pasture * 151.500) + (plantation_pri * 140.70) + "
        "(secondary * 98.400) + (urban * 2443.0)",
    )

    # NOTE: Pass max & min of log(HPD) so hi-res rasters can be processed
    # incrementally.  Recording the max value here for when I create
    # other functions for other resolutions.
    # 0.50 =>  20511.541 / 9.92874298232494
    # 0.25 =>  41335.645 / 10.62948048177454 (10.02 for Sam)
    # 1km  => 872073.500 / 13.678628988329825
    maxHPD = 10.02083
    rasters["logHPD_rs"] = SimpleExpr(
        "logHPD_rs", "scale(log(hpd + 1), 0.0, 1.0, 0.0, %f)" % maxHPD
    )

    fname = utils.luh2_states(scenario)
    for fname in (
        utils.luh2_states(scenario),
        outfn("luh2", "secd-" + scenario + ".nc"),
    ):
        try:
            ds = netCDF4.Dataset(fname)
        except IOError:
            print("Error: opening '%s'" % fname)
            raise IOError("Error: opening '%s'" % fname)
        ds_vars = set(ds.variables.keys())
        names = set(
            reduce(lambda x, y: x + y, [list(lu.syms) for lu in lus], ["urban"])
        )
        for name in set.intersection(names, ds_vars):
            band = year - 849 if scenario == "historical" else year - 2014
            rasters[name] = Raster(name, "netcdf:%s:%s" % (fname, name), band=band)

    for landuse in lus:
        rasters[landuse.name] = landuse
        for band, intensity in enumerate(lui.intensities()):
            n = landuse.name + "_" + intensity
            rasters[n] = lui.LUH5(landuse.name, intensity)
            n2 = n + "_ref"
            if landuse.name[0:11] == "plantation_":
                rasters[n2] = SimpleExpr(n2, "0")
            elif landuse.name[-10:] != "_secondary":
                if landuse.name in ("annual", "cropland", "nitrogen",
                                    "perennial", "timber"):
                    ref_path = outfn("luh2", "%s-recal.tif" % landuse.name)
                else:
                    ref_path = outfn("luh2", "%s-recal.tif" % landuse.syms[0])
                rasters[n2] = Raster(n2, ref_path, band + 1)

    for band, intensity in enumerate(lui.intensities()):
        n = "urban_" + intensity
        rasters[n] = lui.LUH5("urban", intensity)
        n2 = n + "_ref"
        rasters[n2] = Raster(n2, outfn("luh2", "urban-recal.tif"), band + 1)

    name = "%s_light_and_intense" % "primary"
    rasters[name] = SimpleExpr(name, "primary_light + primary_intense")

    return rasters


def luh2(scenario, year, hpd_trend):
    rasters = {}
    if scenario not in utils.luh2_scenarios():
        raise ValueError("Unknown scenario %s" % scenario)
    ssp = scenario[0:4]

    lus = [
        SimpleExpr("annual", "c3ann + c4ann"),
        SimpleExpr("nitrogen", "c3nfx"),
        SimpleExpr("cropland", "c3ann + c4ann + c3nfx"),
        SimpleExpr("pasture", "pastr"),
        SimpleExpr("perennial", "c3per + c4per"),
        SimpleExpr("primary", "primf + primn"),
        SimpleExpr("rangelands", "range"),
        SimpleExpr("timber", "0"),
        SimpleExpr("young_secondary", "secdyf + secdyn"),
        SimpleExpr("intermediate_secondary", "secdif + secdin"),
        SimpleExpr("mature_secondary", "secdmf + secdmn"),
    ]
    rasters["secondary"] = SimpleExpr(
        "secondary", "young_secondary + intermediate_secondary + mature_secondary"
    )

    # Human population density and UN subregions
    rasters["unSub"] = Raster("unSub", outfn("luh2", "un_subregions.tif"))
    rasters["un_code"] = Raster("un_codes", outfn("luh2", "un_codes.tif"))
    # rasters.update(hpd.sps.raster(ssp, year))
    if year < 2015:
        if hpd_trend == "wpp":
            rasters["hpd_ref"] = Raster("hpd_ref", outfn("luh2", "gluds00ag.tif"))
            rasters["hpd"] = hpd.WPP("historical", year, utils.wpp_xls())
        else:
            rasters.update(hpd.hyde.scale_grumps(year))
    else:
        rasters.update(hpd.sps.scale_grumps(ssp, year))

    # Agricultural suitability
    # rasters['ag_suit'] = Raster('ag_suit', outfn('luh2', 'ag-suit-zero.tif'))
    rasters["ag_suit"] = Raster("ag_suit", outfn("luh2", "ag-suit-0.tif"))
    rasters["ag_suit_rs"] = SimpleExpr("ag_suit_rs", "ag_suit")
    rasters["logAdjDist"] = SimpleExpr("logAdjDist", "0")
    rasters["cubrtEnvDist"] = SimpleExpr("cubrtEnvDist", "0")
    rasters["studymean_logHPD_rs"] = SimpleExpr("studymean_logHPD_rs", "0")

    # NOTE: Pass max & min of log(HPD) so hi-res rasters can be processed
    # incrementally.  Recording the max value here for when I create
    # other functions for other resolutions.
    # 0.50 =>  20511.541 / 9.92874298232494
    # 0.25 =>  41335.645 / 10.62948048177454 (10.02 for Sam)
    # 1km  => 872073.500 / 13.678628988329825
    maxHPD = 10.02083
    rasters["logHPD_rs"] = SimpleExpr(
        "logHPD_rs", "scale(log(hpd + 1), 0.0, 1.0, 0.0, %f)" % maxHPD
    )
    rasters["logHPD_s2"] = SimpleExpr("LogHPD_s2", "log(hpd + 1)")
    rasters["logHPD_diff"] = SimpleExpr("logHPD_diff", "0 - logHPD_s2")
    rasters["logDTR_rs"] = Raster("logDTR_rs", outfn("luh2", "roads-final.tif"))
    for fname in (
        utils.luh2_states(scenario),
        outfn("luh2", "secd-" + scenario + ".nc"),
    ):
        try:
            ds = netCDF4.Dataset(fname)
        except IOError:
            print("Error: opening '%s'" % fname)
            raise IOError("Error: opening '%s'" % fname)
        ds_vars = set(ds.variables.keys())
        names = set(
            reduce(lambda x, y: x + y, [list(lu.syms) for lu in lus], ["urban"])
        )
        for name in set.intersection(names, ds_vars):
            band = year - 849 if scenario == "historical" else year - 2014
            rasters[name] = Raster(name, "netcdf:%s:%s" % (fname, name), band=band)

    for landuse in lus:
        rasters[landuse.name] = landuse
        if landuse.name in ("annual", "cropland", "nitrogen", "perennial", "timber"):
            ref_path = outfn("luh2", "%s-recal.tif" % landuse.name)
        else:
            ref_path = outfn("luh2", "%s-recal.tif" % landuse.syms[0])
        for band, intensity in enumerate(lui.intensities()):
            n = landuse.name + "_" + intensity
            n2 = n + "_ref"
            if landuse.name == "timber":
                rasters[n] = SimpleExpr(n, "0")
                rasters[n2] = SimpleExpr(n2, "0")
            else:
                rasters[n] = lui.LUH2(landuse.name, intensity)
                rasters[n2] = Raster(n2, ref_path, band + 1)

    ref_path = outfn("luh2", "urban-recal.tif")
    for band, intensity in enumerate(lui.intensities()):
        n = "urban_" + intensity
        rasters[n] = lui.LUH2("urban", intensity)
        n2 = n + "_ref"
        rasters[n2] = Raster(n2, ref_path, band + 1)

    for landuse in ("annual", "pasture"):
        name = "%s_minimal_and_light" % landuse
        rasters[name] = SimpleExpr(name, "%s_minimal + %s_light" % (landuse, landuse))
    rasters["mature_secondary_intense_and_light"] = SimpleExpr(
        "mature_secondary_intense_and_light", "mature_secondary_light_and_intense"
    )

    for landuse in ("mature_secondary", "nitrogen", "rangelands", "urban"):
        name = "%s_light_and_intense" % landuse
        rasters[name] = SimpleExpr(name, "%s_light + %s_intense" % (landuse, landuse))

    for intensity in ["light", "intense"]:
        expr = " + ".join(
            [
                "%s_%s" % (name, intensity)
                for name in [lu.name for lu in lus] + ["urban"]
            ]
        )
        rasters[intensity] = SimpleExpr(intensity, expr)

    return rasters


def oneKm(year, scenario, hpd_trend):
    rasters = {}
    if scenario == "version3.3":
        ddir = os.path.join(utils.data_root(), "version3.3")
        pattern = "{short}.zip!{short}/{short}_MCDlu_(v3_3_Trop)_%d.bil" % year
    else:
        ddir = os.path.join(utils.data_root(), "1km")
        pattern = "{short}_%d.zip!{short}_1km_%d_0ice.bil" % (year, year)
    lus = []
    for name in lu.types():
        short = name[0:3].upper()
        short = "CRP" if short == "CRO" else short
        fname = pattern.format(short=short)
        lus.append(Raster(name, "zip://" + os.path.join(ddir, fname)))
    rasters["plantation_pri"] = SimpleExpr("plantation_pri", "0")
    rasters["plantation_sec"] = SimpleExpr("plantation_sec", "0")

    # UN country code and subregions
    rasters["unSub"] = Raster("unSub", outfn("1km", "un_subregions.tif"))
    rasters["un_code"] = Raster("un_codes", outfn("1km", "un_codes.tif"))

    # Human population density
    if scenario == "version3.3":
        fname = (
            "zip://" + os.path.join(ddir, "HPD.zip") + "!" + "HPD/yr%4d/hdr.adf" % year
        )
        rasters["hpd"] = Raster("hpd", fname)
    else:
        rasters["hpd_ref"] = Raster(
            "hpd_ref", os.path.join(utils.data_root(), "grump1.0/gluds00ag")
        )
        rasters["hpd"] = hpd.WPP(
            hpd_trend,
            year,
            os.path.join(
                utils.data_root(),
                "wpp",
                "WPP2010_DB2_F01_TOTAL_POPULATION_BOTH_SEXES.xls",
            ),
        )

    # Land use intensity rasters
    for lu_type in lus:
        rasters[lu_type.name] = lu_type
        for _, intensity in enumerate(lui.intensities()):
            name = lu_type.name + "_" + intensity
            if lu_type == "plantation_pri":
                rasters[name] = SimpleExpr(name, "0")
            else:
                rasters[name] = lui.OneKm(lu_type.name, intensity)

    name = "%s_light_and_intense" % "primary"
    rasters[name] = SimpleExpr(name, "primary_light + primary_intense")

    return rasters


def rasterset(lu_src, scenario, year, hpd_trend="medium"):
    if lu_src == "rcp":
        return rcp(scenario, year, hpd_trend)
    if lu_src == "luh5":
        return luh5(scenario, year, hpd_trend)
    if lu_src == "luh2":
        assert hpd_trend in ("wpp", "medium")
        return luh2(scenario, year, hpd_trend)
    if lu_src == "1km":
        return oneKm(year, scenario, hpd_trend)
