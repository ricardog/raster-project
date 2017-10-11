#!/usr/bin/env python

import sys
import timeit
import gdal

import projections.tiff_utils as tu

times = timeit.repeat("tu.to_array('test.vrt')",
                      setup="from __main__ import tu", number=100, repeat=3)
print "test.vrt:\n\t", times

times = timeit.repeat("tu.to_array('./ds/lui/cropland.tif')",
                      setup="from __main__ import tu", number=100, repeat=3)
print "cropland.tif:\n\t", times
