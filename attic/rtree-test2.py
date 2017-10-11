#!/usr/bin/env python

import fiona
import rtree
from shapely.geometry import shape
import time

def explode(coords):
  """Explode a GeoJSON geometry's coordinates object and yield coordinate
    tuples.  As long as the input is conforming, the type of the
    geometry doesn't matter.
  
  """
  for e in coords:
    if isinstance(e, (float, int, long)):
      yield coords
      break
    else:
      for f in explode(e):
        yield f

def bbox(f):
  x, y = zip(*list(explode(f['geometry']['coordinates'])))
  return min(x), min(y), max(x), max(y)

def generator(layer):
  for idx, feat in enumerate(layer):
    if idx % 1000 == 0:
      print idx
    fid = int(feat['id'])
    #geom = shape(feat['geometry'])
    #yield(fid, geom.bounds, fid)
    yield(fid, bbox(feat['geometry']), fid)

def main():
  roads = fiona.open('/data/groads1.0/groads-v1-global-gdb/gROADS_v1.gdb/')
  start = time.time()
  index = rtree.index.Index(generator(roads))
  end = time.time()
  print "Created index in %5.2s" % (end - start)


if __name__ == '__main__':
  main()
