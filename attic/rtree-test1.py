#!/usr/bin/env python

import fiona
import rtree
from shapely.geometry import shape
import time

def generator(layer):
  for feat in layer:
    geom = shape(feat['geometry'])
    fid = int(feat['id'])
    yield(fid, geom.bounds, fid)

def main():
  roads = fiona.open('/data/groads1.0/groads-v1-global-gdb/gROADS_v1.gdb/')
  start = time.time()
  index = rtree.index.Index(generator(roads))
  end = time.time()
  print "Created index in %5.2s" % (end - start)


if __name__ == '__main__':
  main()
