from functools import reduce
import netCDF4
import os

from projutils import hpd
from projutils import lu
from projutils import lui
from projutils import utils
from rasterset import Raster, SimpleExpr

from projutils.utils import outfn


def rcp(scenario, year, hpd_trend):
    rasters = {}

    lus = [
        SimpleExpr("gothr - gfvh1 - gfvh2"),
        SimpleExpr("ax(gsecd - gfsh1 - gfsh2 - gfsh3, 0)"),
        SimpleExpr("gcrop"),
        SimpleExpr("gpast"),
        SimpleExpr("gurbn"),
        SimpleExpr("min(gothr, gfvh1 + gfvh2)"),
        SimpleExpr("min(gsecd, gfsh1 + gfsh2 + gfsh3)"),
    ]

    # Human population density and UN subregions
    rasters["hpd_ref"] = Raster(outfn("rcp", "gluds00ag.tif"))
    rasters["unSub"] = Raster(outfn("rcp", "un_subregions.tif"))
    rasters["un_code"] = Raster(outfn("rcp", "un_codes.tif"))
    rasters["hpd"] = hpd.WPP(hpd_trend, year, utils.wpp_xls())

    # NOTE: Pass max & min of log(HPD) so hi-res rasters can be processed
    # incrementally.  Recording the max value here for when I create
    # other functions for other resolutions.
    # 0.50 =>  20511.541 / 9.92874298232494
    # 0.25 =>  41335.645 / 10.62948048177454
    # 1km  => 872073.500 / 13.678628988329825
    rasters["logHPD_rs"] = SimpleExpr(
        "scale(log(hpd + 1), 0.0, 1.0, 0.0, 9.93)"
    )
    rasters["logDistRd_rs"] = Raster(outfn("rcp", "roads-final.tif"))

    # Inputs RCP rasters
    names = tuple(set(reduce(lambda x, y: x + y, [list(lu.syms) for lu in lus], [])))

    for name in names:
        path = outfn(
            "lu", "rcp", scenario, "updated_states", "%s.%d.tif" % (name, year)
        )
        rasters[name] = Raster(path)

    # Land use intensity rasters
    for landuse in lus:
        rasters[landuse.name] = landuse
        ref_path = outfn("rcp", "%s-recal.tif" % landuse.name)
        for band, intensity in enumerate(lui.intensities()):
            n = landuse.name + "_" + intensity
            rasters[n] = lui.RCP(landuse.name, intensity)
            n2 = n + "_ref"
            if landuse.name[0:11] == "plantation_":
                rasters[n2] = SimpleExpr(0)
            else:
                rasters[n2] = Raster(ref_path, band + 1)
    return rasters


def luh5(scenario, year, plus3):                            # noqa C901
    import projutils.lu.luh5 as luh5
    rasters = {}

    lus = [
        SimpleExpr("primf + primn"),
        SimpleExpr("c3ann + c4ann + c3nfx"),
        SimpleExpr("range + pastr"),
        SimpleExpr("c3per + c4per"),
        SimpleExpr(0),
    ]

    if plus3:
        lus += [
            SimpleExpr("secdmf + secdmn"),
            SimpleExpr("secdif + secdin"),
            SimpleExpr("secdyf + secdyn"),
        ]
        rasters["secondary"] = SimpleExpr("secdy + secdi + secdm")
    else:
        lus += [SimpleExpr("secdf + secdn")]

    # Human population density and UN subregions
    rasters["unSub"] = Raster(outfn("luh2", "un_subregions.tif"))
    rasters["un_code"] = Raster(outfn("luh2", "un_codes.tif"))
    # rasters.update(hpd.sps.raster(ssp, year))
    if year < 2015:
        rasters["hpd_ref"] = Raster(outfn("luh2", "gluds00ag.tif"))
        rasters["hpd"] = hpd.WPP("historical", year, utils.wpp_xls())
    else:
        rasters.update(hpd.sps.scale_grumps(utils.luh2_scenario_ssp(scenario), year))
    # The values in the expression of hpd_max need to be updated when the
    # predicts DB changes.
    rasters["hpd_max"] = SimpleExpr(
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
        "scale(log(hpd + 1), 0.0, 1.0, 0.0, %f)" % maxHPD
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
        ds_vars = filter(lambda v: v not in ("time", "lat", "lon", "crs"),
                         ds.variables.keys())
        for name in ds_vars:
            band = year - 849 if scenario == "historical" else year - 2014
            rasters[name] = Raster("netcdf:%s:%s" % (fname, name),
                                   band=band, decode_times=False)

    for landuse, sexpr in luh5.types2(True).items():
        rasters[landuse] = SimpleExpr(sexpr)
        for band, intensity in enumerate(lui.intensities()):
            n = landuse + "_" + intensity
            rasters[n] = lui.LUH5(landuse, intensity)
            n2 = n + "_ref"
            if landuse[0:11] == "plantation_":
                rasters[n2] = 0
            elif landuse[-10:] != "_secondary":
                if landuse in ("annual", "cropland", "nitrogen",
                               "perennial", "timber"):
                    ref_path = outfn("luh2", "%s-recal.tif" % landuse)
                else:
                    print(landuse)
                    ref_path = outfn("luh2", "%s-recal.tif" %
                                     rasters[landuse].syms[0])
                rasters[n2] = Raster(ref_path, band + 1)

    for band, intensity in enumerate(lui.intensities()):
        n = "urban_" + intensity
        rasters[n] = lui.LUH5("urban", intensity)
        n2 = n + "_ref"
        rasters[n2] = Raster(outfn("luh2", "urban-recal.tif"), band + 1)

    return rasters


def luh2(scenario, year, hpd_trend):                        # noqa C901
    rasters = {}
    if scenario not in utils.luh2_scenarios():
        raise ValueError("Unknown scenario %s" % scenario)
    ssp = scenario[0:4]

    lus = [
        SimpleExpr("c3ann + c4ann"),
        SimpleExpr("c3nfx"),
        SimpleExpr("c3ann + c4ann + c3nfx"),
        SimpleExpr("pastr"),
        SimpleExpr("c3per + c4per"),
        SimpleExpr("primf + primn"),
        SimpleExpr("range"),
        SimpleExpr(0),
        SimpleExpr("secdyf + secdyn"),
        SimpleExpr("secdif + secdin"),
        SimpleExpr("secdmf + secdmn"),
    ]
    rasters["secondary"] = SimpleExpr(
        "young_secondary + intermediate_secondary + mature_secondary"
    )

    # Human population density and UN subregions
    rasters["unSub"] = Raster(outfn("luh2", "un_subregions.tif"))
    rasters["un_code"] = Raster(outfn("luh2", "un_codes.tif"))
    # rasters.update(hpd.sps.raster(ssp, year))
    if year < 2015:
        if hpd_trend == "wpp":
            rasters["hpd_ref"] = Raster(outfn("luh2", "gluds00ag.tif"))
            rasters["hpd"] = hpd.WPP("historical", year, utils.wpp_xls())
        else:
            rasters.update(hpd.hyde.scale_grumps(year))
    else:
        rasters.update(hpd.sps.scale_grumps(ssp, year))

    # Agricultural suitability
    # rasters['ag_suit'] = Raster(outfn('luh2', 'ag-suit-zero.tif'))
    rasters["ag_suit"] = Raster(outfn("luh2", "ag-suit-0.tif"))
    rasters["ag_suit_rs"] = SimpleExpr("ag_suit")
    rasters["logAdjDist"] = SimpleExpr(0)
    rasters["cubrtEnvDist"] = SimpleExpr(0)
    rasters["studymean_logHPD_rs"] = SimpleExpr(0)

    # NOTE: Pass max & min of log(HPD) so hi-res rasters can be processed
    # incrementally.  Recording the max value here for when I create
    # other functions for other resolutions.
    # 0.50 =>  20511.541 / 9.92874298232494
    # 0.25 =>  41335.645 / 10.62948048177454 (10.02 for Sam)
    # 1km  => 872073.500 / 13.678628988329825
    maxHPD = 10.02083
    rasters["logHPD_rs"] = SimpleExpr(
        "scale(log(hpd + 1), 0.0, 1.0, 0.0, %f)" % maxHPD
    )
    rasters["logHPD_s2"] = SimpleExpr("log(hpd + 1)")
    rasters["logHPD_diff"] = SimpleExpr("0 - logHPD_s2")
    rasters["logDTR_rs"] = Raster(outfn("luh2", "roads-final.tif"))
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
            rasters[name] = Raster("netcdf:%s:%s" % (fname, name), band=band)

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
                rasters[n] = SimpleExpr(0)
                rasters[n2] = SimpleExpr(0)
            else:
                rasters[n] = lui.LUH2(landuse.name, intensity)
                rasters[n2] = Raster(ref_path, band + 1)

    ref_path = outfn("luh2", "urban-recal.tif")
    for band, intensity in enumerate(lui.intensities()):
        n = "urban_" + intensity
        rasters[n] = lui.LUH2("urban", intensity)
        n2 = n + "_ref"
        rasters[n2] = Raster(ref_path, band + 1)

    for landuse in ("annual", "pasture"):
        name = "%s_minimal_and_light" % landuse
        rasters[name] = SimpleExpr("%s_minimal + %s_light" % (landuse, landuse))
    rasters["mature_secondary_intense_and_light"] = SimpleExpr(
        "mature_secondary_light_and_intense"
    )

    for landuse in ("mature_secondary", "nitrogen", "rangelands", "urban"):
        name = "%s_light_and_intense" % landuse
        rasters[name] = SimpleExpr("%s_light + %s_intense" % (landuse, landuse))

    for intensity in ["light", "intense"]:
        expr = " + ".join(
            [
                "%s_%s" % (name, intensity)
                for name in [lu.name for lu in lus] + ["urban"]
            ]
        )
        rasters[intensity] = SimpleExpr(expr)

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
        lus.append(Raster("zip://" + os.path.join(ddir, fname)))
    rasters["plantation_pri"] = SimpleExpr(0)
    rasters["plantation_sec"] = SimpleExpr(0)

    # UN country code and subregions
    rasters["unSub"] = Raster(outfn("1km", "un_subregions.tif"))
    rasters["un_code"] = Raster(outfn("1km", "un_codes.tif"))

    # Human population density
    if scenario == "version3.3":
        fname = (
            "zip://" + os.path.join(ddir, "HPD.zip") + "!" + "HPD/yr%4d/hdr.adf" % year
        )
        rasters["hpd"] = Raster(fname)
    else:
        rasters["hpd_ref"] = Raster(
            os.path.join(utils.data_root(), "grump1.0/gluds00ag")
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
                rasters[name] = SimpleExpr(0)
            else:
                rasters[name] = lui.OneKm(lu_type.name, intensity)

    name = "%s_light_and_intense" % "primary"
    rasters[name] = SimpleExpr("primary_light + primary_intense")

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
