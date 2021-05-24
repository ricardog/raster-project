#!/usr/bin/env python

# This script checks that secma is <= 1 when secdf + secdn == 0.

from netCDF4 import Dataset
import numpy as np
import numpy.ma as ma
import os

static = Dataset("../../data/luh2_v2/staticData_quarterdeg.nc")
icwtr = static.variables["icwtr"][:, :]
secd = ma.empty_like(icwtr)
secd.mask = np.where(icwtr == 1, True, False)
secma = ma.empty_like(icwtr)
secma.mask = secd.mask
atol = 1e-5

scenarios = [  # 'LUH2_v2f_beta_SSP1_RCP2.6_IMAGE',
    # 'LUH2_v2f_beta_SSP2_RCP4.5_MESSAGE-GLOBIOM',
    # 'LUH2_v2f_beta_SSP3_RCP7.0_AIM',
    # 'LUH2_v2f_beta_SSP4_RCP3.4_GCAM',
    # 'LUH2_v2f_beta_SSP4_RCP6.0_GCAM',
    # 'LUH2_v2f_beta_SSP5_RCP8.5_REMIND-MAGPIE',
    "historical"
]
file_list = [os.path.join("../../data/luh2_v2", x, "states.nc") for x in scenarios]

total = 0
for fname in file_list:
    print(fname)
    with Dataset(fname) as ds:
        for idx, yy in enumerate(ds.variables["time"]):
            year = int(yy)
            if idx == int(yy):
                year = 850 + int(yy)
            print("  year %d" % year)
            secd = ds.variables["secdf"][idx]
            secd += ds.variables["secdn"][idx]
            secma = ma.where(
                np.isclose(secd, 0, atol=atol), ds.variables["secma"][idx], 0
            )
            nz = np.count_nonzero(secma > 1.0 + atol)
            total += nz
            assert nz == 0, "secma > 1.0 when secdf + secdn == 0"
            if None and nz > 0:
                indeces = zip(*ma.where(secma > 1 + atol))
                tp = ((xx, secd[xx], secma[xx]) for xx in indeces)
                for t in sorted(tp, key=lambda x: x[2])[0:10]:
                    print("%3d, %4d: %6.4f => %6.4f" % (t[0][0], t[0][1], t[1], t[2]))
                    pass

    print("total: %d" % total)


def unused(filelist):
    total = 0
    for fname in file_list:
        print(fname)
        with Dataset(fname) as ds:
            secdf = ds.variables["secdf"][:, :, :]
            secdn = ds.variables["secdn"][:, :, :]
            secma = ma.where(
                np.isclose(secdf + secdn, 0, atol=atol),
                ds.variables["secma"][:, :, :],
                0,
            )
            nz = np.count_nonzero(secma > 1.0 + atol)
            total += nz
            assert nz == 0, "secma > 1.0 when secdf + secdn == 0"
        print("total: %d" % total)
