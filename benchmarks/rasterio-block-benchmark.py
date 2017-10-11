#!/usr/bin/env python

import subprocess
import sys
import time
import timeit
import rasterio

import projections.poly as poly

def read_raster(raster, x_block_size, y_block_size):
  with rasterio.open(raster) as src:
    width = src.width
    height = src.height
    blocks = 0
    for y in xrange(0, height, y_block_size):
      y_end = min(y + y_block_size, height)
      for x in xrange(0, width, x_block_size):
        x_end = min(x + x_block_size, width)
        array = src.read(1, window=((y, y_end), (x, x_end)))
        out = poly.poly(array.reshape(-1), [3, 1],
                        [44840.0, 1941.85401726, 58.0508825943, 1.85514376267],
                        [0.228318801448, 0.345506412604, 0.355480646384])
        del array
        blocks += 1
  print "{0} blocks size {1} x {2}:".format(blocks, x_block_size, y_block_size)

# Function to run the test and print the time taken to complete.
def timer(raster, x_block_size, y_block_size):
  purge()
  t = timeit.Timer("read_raster('{0}', {1}, {2})".format(raster, x_block_size,
                                                       y_block_size),
                   setup="from __main__ import read_raster")
  print "\t{:.4f}s\n".format(t.timeit(1))

def purge():
  subprocess.call(['/usr/bin/sudo', 'purge'])

if len(sys.argv) < 2:
  print "Error; please pass the name of a raster file"
  sys.exit(1)

raster = sys.argv[1]
with rasterio.open(raster) as src:
  # Get "natural" block size, and total raster XY size. 
  block_shape = src.block_shapes[0]
  x_block_size = block_shape[1]
  y_block_size = block_shape[0]
  xsize = src.width
  ysize = src.height

#timer(raster, x_block_size, y_block_size * 2)
#sys.exit()

# Tests with different block sizes.
timer(raster, x_block_size, y_block_size)
timer(raster, 128, 128)
#timer(raster, x_block_size*10, y_block_size*10)
#timer(raster, x_block_size*100, y_block_size*100)
#timer(raster, x_block_size*10, y_block_size)
#timer(raster, x_block_size*100, y_block_size)
timer(raster, x_block_size, y_block_size*10)
timer(raster, x_block_size, y_block_size*100)
timer(raster, xsize, y_block_size)
timer(raster, x_block_size, ysize)
#timer(raster, xsize, 1)
#timer(raster, 1, ysize)
  
