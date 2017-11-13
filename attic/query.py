#!/usr/bin/env python3

from affine import Affine
import numpy as np
import numpy.ma as ma
import os
import psycopg2
import rasterio
from rasterio.plot import show
import re
import sys
import time

import pdb

#
# To create the DB:
# CREATE DATABASE groads WITH ENCODING='UTF8' LC_CTYPE='en_US.UTF-8' LC_COLLATE='en_US.UTF-8' OWNER=vagrant TEMPLATE=template0 CONNECTION LIMIT=-1;
#
# To insert roads data into database
# ogr2ogr -f "PostgreSQL" PG:"host=hostname port=5432 dbname=groads user=username password=passwd" groads1.0/groads-v1-global-gdb/gROADS_v1.gdb Global_Roads
#
# To create the index
# CREATE INDEX global_roads_gidx ON global_roads USING GIST (wkb_geometry);
#
#
DB_NAME = 'groads'
USER = 'vagrant'
PASSWORD = 'vagrant'
HOST = '192.168.0.155'

def get_srid(crs):
  if crs == {}:
    return 4326
  m = re.match(r'epsg:(\d+)$', crs['init'])
  if m:
    return int(m.group(1))
  raise RuntimeError("Unknow CRS: %s" % str(crs))

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
  
def do_query(bounds, affine, srid, nodata, dtype):
  query_sql = read_query()
  params = bounds_to_params(bounds, affine)
  params['srid'] = srid
  nrows = params['nrows']
  ncols = params['ncols']
  shape = (nrows, ncols)
  ul = (bounds[0], bounds[3])  * ~affine
  
  params['nrows'] = min(int(1e6 / nrows), nrows)
  params.update({'xoff': bounds[0]})
  out = np.full(shape, nodata, dtype=dtype)
  
  conn = psycopg2.connect(dbname=DB_NAME, user=USER, host=HOST,
                          password=PASSWORD)
  cursor = conn.cursor()

  stime = time.time()
  for yoff in range(int(ul[1]), int(ul[1]) + nrows, params['nrows']):
    print("rows: %d:%d" % (yoff, yoff + params['nrows']))
    _, y0 = (0, yoff) * affine
    _, y1 = (0, yoff + params['nrows']) * affine
    print("bbox: %5.2f:%5.2f" % (y0, y1))
    params['yoff'] = y0
    query_str = query_sql % params
    print(query_str)
    cursor.execute(query_sql, params)
    while True:
      data = cursor.fetchmany(params['nrows'] * params['ncols'])
      if len(data) == 0:
        break
      put(out, data)
  masked = ma.masked_equal(out, nodata)
  etime = time.time()
  print("executed in %7.2fs" % (etime - stime))
  return masked

if __name__ == '__main__':
  #do_query((-180, -90, 180, 90), Affine(0.5, 0, -180, 0, -0.5, 90))
  ref = '/Users/ricardog/src/eec/predicts/playground/ds/rcp/un_codes.tif'
  #ref = '/Users/ricardog/src/eec/predicts/playground/ds/luh2/un_codes.tif'
  with rasterio.open(ref) as ds:
    meta = ds.meta
    meta.update({'dtype': 'float32', 'nodata': -1.0})
    out = do_query(ds.bounds, ds.meta['affine'], get_srid(ds.crs), -1.0,
                   'float32')
    with rasterio.open('road-length.tif', 'w', **meta) as dst:
      dst.write(out, 1)
    show(out)
