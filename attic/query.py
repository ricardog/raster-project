#!/usr/bin/env python3

from affine import Affine
import numpy as np
import numpy.ma as ma
import os
import psycopg2
import rasterio
from rasterio.plot import show
import sys

import pdb

#
# To create the DB:
# CREATE DATABASE groads WITH ENCODING='UTF8' LC_CTYPE='en_US.UTF-8' LC_COLLATE='en_US.UTF-8' OWNER=vagrant TEMPLATE=template0 CONNECTION LIMIT=-1;
#
# To create the index
# CREATE INDEX global_roads_gidx ON global_roads USING GIST (wkb_geometry);
#
#
DB_NAME = 'groads'
USER = 'vagrant'
PASSWORD = 'vagrant'
HOST = '192.168.0.155'

def bounds_to_params(bounds, affine):
  l, b, r, t = bounds
  (x0, y0) = (l, t) * ~affine
  (x1, y1) = (r, b) * ~affine
  ncols = int(x1 - x0)
  nrows = int(y1 - y0)
  xres = affine[0]
  yres = affine[4]
  return {'ncols': ncols, 'nrows': nrows, 'xres': xres, 'yres': yres}

def read_query():
  my_dir = os.path.dirname(__file__)
  fname = os.path.join(my_dir, 'query.psql')
  with open(fname) as f:
    query_sql = f.read()
  return query_sql

def put(array, data):
  y = tuple(map(lambda x: x[0] - 1, data))
  x = tuple(map(lambda x: x[1] - 1, data))
  v = tuple(map(lambda x: x[2] / 1000, data))
  idx = np.ravel_multi_index((y, x), array.shape)
  np.put(array, idx, v)
  
def do_query(bounds, affine):
  query_sql = read_query()
  params = bounds_to_params(bounds, affine)
  nrows = params['nrows']
  ncols = params['ncols']
  shape = (nrows, ncols)
  
  params['nrows'] = min(int(1e6 / nrows), nrows)
  params.update({'xoff': -180})
  out = np.full(shape, -1.0, dtype=float)
  
  conn = psycopg2.connect(dbname=DB_NAME, user=USER, host=HOST,
                          password=PASSWORD)
  cursor = conn.cursor()

  for yoff in range(0, nrows, params['nrows']):
    print("rows: %d:%d" % (yoff, yoff + params['nrows']))
    xb0, yb0 = (0, yoff) * affine
    xb1, yb1 = (0, yoff + params['nrows']) * affine
    print("bbox: %5.2f:%5.2f" % (yb0, yb1))
    params['yoff'] = yb0
    query_str = query_sql % params
    print(query_str)
    cursor.execute(query_sql, params)
    while True:
      data = cursor.fetchmany(params['nrows'] * params['ncols'])
      if len(data) == 0:
        break
      put(out, data)
  masked = ma.masked_equal(out, -1)
  show(masked)
  sys.exit()

if __name__ == '__main__':
  #do_query((-180, -90, 180, 90), Affine(0.5, 0, -180, 0, -0.5, 90))
  with rasterio.open('/Users/ricardog/src/eec/predicts/playground/ds/rcp/un_codes.tif') as ds:
    do_query(ds.bounds, ds.meta['affine'])
