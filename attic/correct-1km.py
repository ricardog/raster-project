#!/usr/bin/env python

import numpy as np
import numpy.ma as ma
import os
import rasterio


def window_shape(win):
    return (win[0][1] - win[0][0], win[1][1] - win[1][0])


in_dir = "/data/version3.3/tif"
out_dir = "/home/vagrant/trop"
lus = ["crp", "pas", "pri", "sec", "urb"]
for year in range(2001, 2013):
    print(year)
    inputs = {}
    outputs = {}
    for lu in lus:
        inputs[lu] = rasterio.open(os.path.join(in_dir, "%s-trop-%d.tif" % (lu, year)))
        outputs[lu] = rasterio.open(
            os.path.join(out_dir, "%s-trop-adj-%d.tif" % (lu, year)),
            "w",
            **inputs[lu].meta
        )
    bounds = set([ras.bounds for ras in inputs.values()])
    assert len(bounds) == 1
    block_shapes = set([ras.block_shapes for ras in inputs.values()])
    assert len(block_shapes) == 1
    shape = inputs[lus[0]].block_shapes[0]
    data = ma.empty((len(lus), shape[0], shape[1]), dtype=np.float32)
    total = ma.empty(shape, dtype=np.float32)
    wins = len(tuple(inputs[lus[0]].block_windows()))
    for ij, win in inputs[lus[0]].block_windows():
        if win[0][0] % 100 == 0:
            print(win)
        for idx, lu in enumerate(lus):
            data[idx] = inputs[lu].read(1, masked=True, window=win)
        data.sum(axis=0, out=total)
        assert ma.allclose(total, 1.0)
        # print("stats: %6.4f, %6.4f" % (total.min(), total.max()))
        # for idx, lu in enumerate(lus):
        #  data[idx] /= total
        #  outputs[lu].write(data[idx], window=win, indexes=1)
