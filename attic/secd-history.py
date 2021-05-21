#!/usr/bin/env python

from netCDF4 import Dataset
import numpy as np
import numpy.ma as ma
import os
import re

import pdb


def sumv(ds, idx, vs):
    shape = ds.variables[vs[0]].shape[1:]
    out = ma.zeros(shape)
    for v in vs:
        out += ds.variables[v][idx]
    return out


static = Dataset("../../data/luh2_v2/staticData_quarterdeg.nc")
icwtr = static.variables["icwtr"][:, :]
fstnf = static.variables["fstnf"][:, :]
atol = 5e-5

scenarios = ["historical"]
states = [os.path.join("../../data/luh2_v2", x, "states.nc") for x in scenarios]
transitions = [
    os.path.join("../../data/luh2_v2", x, "transitions.nc") for x in scenarios
]
file_list = zip(states, transitions)

sidx = 0
for sname, tname in file_list:
    print(sname)
    print(tname)
    with Dataset(tname) as trans:
        with Dataset(sname) as state:
            shp = state.variables["secdf"].shape
            currf = ma.empty_like(icwtr)
            currf.mask = icwtr == 1.0
            currn = ma.empty_like(currf)
            secdf = ma.empty_like(currf)
            secdn = ma.empty_like(currf)
            posf = filter(
                lambda x: re.search(r"(?!secdf)_to_secdf$|primf_harv$", x),
                trans.variables.keys(),
            )
            posn = filter(
                lambda x: re.search(r"(?!secdn)_to_secdn$|primn_harv$", x),
                trans.variables.keys(),
            )
            negf = filter(
                lambda x: re.match(r"secdf_to_(?!secdf)", x), trans.variables.keys()
            )
            negn = filter(
                lambda x: re.match(r"secdn_to_(?!secdn)", x), trans.variables.keys()
            )
            print("posf: ", posf, "\n")
            print("posn: ", posn, "\n")
            print("negf: ", negf, "\n")
            print("negn: ", negn, "\n")
            currf = state.variables["secdf"][sidx]
            currn = state.variables["secdn"][sidx]
            for idx, yy in enumerate(trans.variables["time"]):
                year = int(yy)
                if idx == int(yy):
                    year += 850
                print("  year %d" % year)
                if yy < sidx:
                    continue
                secdf = state.variables["secdf"][idx]
                secdn = state.variables["secdn"][idx]
                difff = np.fabs(currf - secdf)
                diffn = np.fabs(currn - secdn)
                # print("    f : %7f" % difff.max())
                # print("    nf: %7f" % diffn.max())
                assert np.allclose(difff, 0, atol=atol)
                assert np.allclose(diffn, 0, atol=atol)

                for l in negf:
                    currf -= trans.variables[l][idx]
                for l in posf:
                    currf += trans.variables[l][idx]

                for l in negn:
                    currn -= trans.variables[l][idx]
                for l in posn:
                    currn += trans.variables[l][idx]
                pass
print("done")
