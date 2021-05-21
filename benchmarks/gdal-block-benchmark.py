#!/usr/bin/env python

import subprocess
import sys
import timeit

try:
    import gdal
except:
    from osgeo import gdal

import projections.poly as poly

# Function to read the raster as arrays for the chosen block size.
def read_raster(raster, x_block_size, y_block_size):
    ds = gdal.Open(raster)
    band = ds.GetRasterBand(1)
    xsize = band.XSize
    ysize = band.YSize
    blocks = 0
    for y in range(0, ysize, y_block_size):
        if y + y_block_size < ysize:
            rows = y_block_size
        else:
            rows = ysize - y
        for x in range(0, xsize, x_block_size):
            if x + x_block_size < xsize:
                cols = x_block_size
            else:
                cols = xsize - x
            array = band.ReadAsArray(x, y, cols, rows)
            out = poly.poly(
                array.reshape(-1),
                [3, 1],
                [44840.0, 1941.85401726, 58.0508825943, 1.85514376267],
                [0.228318801448, 0.345506412604, 0.355480646384],
            )
            del out
            del array
            blocks += 1
    band = None
    ds = None
    print("{0} blocks size {1} x {2}:".format(blocks, x_block_size, y_block_size))


# Function to run the test and print the time taken to complete.
def timer(raster, x_block_size, y_block_size):
    purge()
    t = timeit.Timer(
        "read_raster('{0}', {1}, {2})".format(raster, x_block_size, y_block_size),
        setup="from __main__ import read_raster",
    )
    print("\t{:.4f}s\n".format(t.timeit(1)))


def purge():
    subprocess.call(["/usr/bin/sudo", "purge"])


if len(sys.argv) < 2:
    print("Error; please pass the name of a raster file")
    sys.exit(1)

gdal.SetCacheMax(1)
raster = sys.argv[1]
ds = gdal.Open(raster)
band = ds.GetRasterBand(1)

# Get "natural" block size, and total raster XY size.
block_sizes = band.GetBlockSize()
x_block_size = block_sizes[0]
y_block_size = block_sizes[1]
xsize = band.XSize
ysize = band.YSize
band = None
ds = None

# timer(raster, x_block_size, y_block_size * 2)
# sys.exit()

# Tests with different block sizes.
timer(raster, x_block_size, y_block_size)
timer(raster, 128, 128)
# timer(raster, x_block_size*10, y_block_size*10)
# timer(raster, x_block_size*100, y_block_size*100)
# timer(raster, x_block_size*10, y_block_size)
# timer(raster, x_block_size*100, y_block_size)
timer(raster, x_block_size, y_block_size * 10)
timer(raster, x_block_size, y_block_size * 100)
timer(raster, xsize, y_block_size)
timer(raster, x_block_size, ysize)
# timer(raster, xsize, 1)
# timer(raster, 1, ysize)
