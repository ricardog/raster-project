#!/usr/bin/env python

import timeit


times = timeit.repeat(
    "tu.to_array('test.vrt')", setup="import pojections.tiff_utils tu",
    number=100, repeat=3
)
print("test.vrt:\n\t", times)

times = timeit.repeat(
    "tu.to_array('/out/lui/cropland.tif')",
    setup="from __main__ import tu",
    number=100,
    repeat=3,
)
print("cropland.tif:\n\t", times)
