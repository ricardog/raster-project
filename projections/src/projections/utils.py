import argparse
import errno
import os
from pylru import lrudecorator
import re
import subprocess
import sys
import threading


class FullPaths(argparse.Action):
    """Expand user- and relative-paths"""

    def __call__(self, parser, namespace, values, option_string=None):
        setattr(namespace, self.dest, os.path.abspath(os.path.expanduser(values)))


def is_dir(dirname):
    """Checks if a path is an actual directory"""
    if not os.path.isdir(dirname):
        msg = "{0} is not a directory".format(dirname)
        raise argparse.ArgumentTypeError(msg)
    else:
        return dirname


def mkpath(path):
    try:
        os.makedirs(path)
    except OSError as exc:  # Python >2.5
        if exc.errno == errno.EEXIST and os.path.isdir(path):
            pass
        else:
            raise


def outfn(res, *args):
    """Return the name of an output file as a string.  The first argument is
    the 'resolution'.  All subsequent (optional) arguments are appended as a
    path (similar to calling os.path.join()).

    """
    return os.path.join(outdir(), res, *args)


@lrudecorator(10)
def outdir():
    """Returns the root of the output folder."""
    if "OUTDIR" in os.environ:
        outdir = os.environ["OUTDIR"]
    elif os.path.isdir("/mnt/predicts"):
        outdir = "/mnt/predicts"
        os.environ["OUTDIR"] = os.path.abspath(outdir)
    else:
        raise RuntimeError("please set OUTDIR")
    return os.path.abspath(outdir)


def lui_model_dir():
    """Returns the directory where to find the land-use intensity models.
    Assumed to be OUTDIR/lui_models.

    """
    return os.path.join(data_root(), "lui_models")


@lrudecorator(10)
def data_root():
    """Returns the root of the data folder.  All data sources are assumed
    relative to this folder.

    """
    if "DATA_ROOT" in os.environ:
        dr = os.environ["DATA_ROOT"]
    elif os.path.isdir("/mnt/data"):
        dr = "/mnt/data"
        os.environ["DATA_ROOT"] = os.path.abspath(dr)
    else:
        raise RuntimeError("please set DATA_ROOT")
    return os.path.abspath(dr)


def data_file(*args):
    """Return the name of an data file as a string.  It creates a path by joining all the argument with DATA_ROOT prepended."""
    return os.path.join(data_root(), *args)


def cnames_csv():
    return data_file("ssp-data", "country-names.csv")


def gdp_csv():
    return os.path.join(data_root(), "econ", "gdp-per-capita.csv")


def eci_csv():
    return os.path.join(data_root(), "econ", "eci_country_rankings_changed.csv")


def wjp_xls():
    return os.path.join(
        data_root(),
        "rule-of-law",
        "FINAL_2017-2018_wjp_rule_of_law_index_HISTORICAL_DATA_FILE.xlsx",
    )


def cpi_csv():
    return os.path.join(data_root(), "econ", "cpi.csv")


def energy_c_csv():
    return os.path.join(data_root(), "econ", "energy-consumption.csv")


def energy_p_csv():
    return os.path.join(data_root(), "econ", "energy-production.csv")


def wpp_xls():
    """Returns file name of UN WPP spreadsheet."""
    return os.path.join(
        data_root(), "wpp", "WPP2017_POP_F01_1_TOTAL_POPULATION_BOTH_SEXES.xlsx"
    )


def luh2_prefix():
    """Prefix of all LUH2 data file names."""
    return "LUH2_v2f_"


def luh2_dir():
    return os.path.join(data_root(), "luh2_v2")


def luh2_scenarios():
    prefix = luh2_prefix() + "SSP"
    ll = len(prefix)
    scenarios = sorted(
        filter(
            lambda p: (p == "historical" or p[0:ll] == prefix), os.listdir(luh2_dir())
        )
    )
    return tuple(re.sub("^" + luh2_prefix(), "", x).lower() for x in scenarios)


def luh2_check_year(year, scenario):
    if scenario == "historical" and year >= 850 and year < 2015:
        return
    if scenario != "historical" and year >= 2015 and year <= 2100:
        return
    assert False, "Invalid (year, scenario) tuple (%d, %s)" % (year, scenario)


def luh2_scenario_ssp(scenario):
    ssp, rcp, iam = scenario.split("_")
    return ssp


def _luh2_file(scenario, fname):
    if scenario == "historical":
        return os.path.join(luh2_dir(), scenario, fname)
    return os.path.join(luh2_dir(), luh2_prefix() + scenario.upper(), fname)


def luh2_static(what=None):
    if what:
        return "NETCDF:" + os.path.join(
            luh2_dir(), "staticData_quarterdeg.nc:%s" % what
        )
    return os.path.join(luh2_dir(), "staticData_quarterdeg.nc")


def luh2_states(scenario):
    return _luh2_file(scenario, "states.nc")


def luh2_transitions(scenario):
    return _luh2_file(scenario, "transitions.nc")


def luh2_management(scenario):
    return _luh2_file(scenario, "management.nc")


def luh2_layer(scenario, layer):
    return "netcdf:" + luh2_states(scenario) + f":{layer}"


def grumps1():
    return os.path.join(data_root(), "grump1.0", "gluds00ag")


def grumps4():
    return os.path.join(
        data_root(),
        "grump4.0",
        "gpw-v4-population-density-adjusted-to-2015-" + "unwpp-country-totals_2015.tif",
    )


def sps(scenario, year):
    path = os.path.join(
        data_root(), "sps", "%s_NetCDF" % scenario.upper(), "total/NetCDF"
    )
    name = "%s_%d" % (scenario, year)
    return "netcdf:%s/%s.nc:%s" % (path, name, name)


def hyde_varions():
    return ("32", "31_final")


def hyde_dir(version):
    if version == "32":
        return os.path.join(data_root(), "hyde" + version, "baseline")
    return os.path.join(data_root(), "hyde" + version)


def hyde_area():
    return os.path.join(data_root(), "hyde31_final", "garea_cr.asc")


def hyde_variables():
    return ("popc", "popd", "rurc", "uopp", "urbc")


def hyde_raw(version, year, variable):
    if year < 0:
        suffix = "bc"
        year *= -1
    else:
        suffix = "ad"
    if version == "32":
        suffix = suffix.upper()
        p = os.path.join(
            data_root(), "hyde" + version, "baseline", "%d%s_pop.zip" % (year, suffix)
        )
    else:
        p = os.path.join(data_root(), "hyde" + version, "%d%s_pop.zip" % (year, suffix))
    if variable:
        return "zip:" + p + "!%s_%d%s.asc" % (variable, year, suffix.upper())
    return p


def run(cmd, sem=None):
    try:
        if sem is None:
            out = subprocess.check_output(cmd, shell=False, stderr=subprocess.STDOUT)
        else:
            with sem:
                out = subprocess.check_output(
                    cmd, shell=False, stderr=subprocess.STDOUT
                )
    except subprocess.CalledProcessError as e:
        print(e.output)
        sys.exit(1)
    return out


def run_parallel(cmds, j):
    threads = []
    sem = threading.Semaphore(j)
    for cmd in cmds:
        t = threading.Thread(target=run, args=[cmd, sem])
        threads.append(t)
        t.start()
    return threads
