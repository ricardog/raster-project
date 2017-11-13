#!/usr/bin/env python3

from affine import Affine
import click
import collections
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
os.environ['DB_NAME'] = 'groads'
os.environ['DB_HOST'] = '192.168.0.155'
os.environ['DB_USER'] = 'vagrant'
os.environ['PASSWORD'] = 'vagrant'

# From https://stackoverflow.com/questions/41268949/python-click-option-with-a-prompt-and-default-hidden
class HiddenPassword(object):
  def __init__(self, password=''):
    self.password = password
  def __str__(self):
    return '*' * len(self.password)

# From https://stackoverflow.com/questions/45868549/creating-a-click-option-with-prompt-that-shows-only-if-default-value-is-empty
class OptionPromptNull(click.Option):
  _value_key = '_default_val'

  def get_default(self, ctx):
    if not hasattr(self, self._value_key):
      default = super(OptionPromptNull, self).get_default(ctx)
      setattr(self, self._value_key, default)
    return getattr(self, self._value_key)

  def prompt_for_value(self, ctx):
    default = self.get_default(ctx)
    # only prompt if the default value is None
    if default in (None, ''):
      return super(OptionPromptNull, self).prompt_for_value(ctx)

    return default
  
GisInfo = collections.namedtuple('GisInfo', ['bounds', 'affine', 'srid',
                                             'dtype', 'nodata'])
ConnInfo = collections.namedtuple('ConnInfo', ['db', 'host', 'user',
                                               'password'])

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
  
def do_query(gis_info, conn_info):
  query_sql = read_query()
  params = bounds_to_params(gis_info.bounds, gis_info.affine)
  params['srid'] = gis_info.srid
  nrows = params['nrows']
  ncols = params['ncols']
  shape = (nrows, ncols)
  ul = (gis_info.bounds[0], gis_info.bounds[3])  * ~gis_info.affine
  
  params['nrows'] = min(int(1e6 / nrows), nrows)
  params.update({'xoff': gis_info.bounds[0]})
  out = np.full(shape, gis_info.nodata, dtype=gis_info.dtype)

  conn = psycopg2.connect(dbname=conn_info.db, user=conn_info.user,
                          host=conn_info.host, password=conn_info.password)
  cursor = conn.cursor()

  stime = time.time()
  for yoff in range(int(ul[1]), int(ul[1]) + nrows, params['nrows']):
    print("rows: %d:%d" % (yoff, yoff + params['nrows']))
    _, y0 = (0, yoff) * gis_info.affine
    _, y1 = (0, yoff + params['nrows']) * gis_info.affine
    print("bbox: %5.2f:%5.2f" % (y0, y1))
    params['yoff'] = y0
    query_str = query_sql % params
    #print(query_str)
    cursor.execute(query_sql, params)
    while True:
      data = cursor.fetchmany(params['nrows'] * params['ncols'])
      if len(data) == 0:
        break
      put(out, data)
  masked = ma.masked_equal(out, gis_info.nodata)
  etime = time.time()
  print("executed in %7.2fs" % (etime - stime))
  return masked

@click.command()
@click.argument('reference', type=click.Path(dir_okay=False))
@click.argument('out-file', type=click.Path(dir_okay=False),
                default='road-length.tif')
@click.option('--db', cls=OptionPromptNull, prompt=True,
              default=lambda: os.environ.get('DB_NAME', ''))
@click.option('--host', cls=OptionPromptNull, prompt=True,
              default=lambda: os.environ.get('DB_HOST', ''))
@click.option('--user', cls=OptionPromptNull, prompt=True,
              default=lambda: os.environ.get('DB_USER', ''))
@click.option('--password',
              default=lambda: HiddenPassword(os.environ.get('PASSWORD', '')),
              hide_input=True)
def generate(reference, out_file, db, host, user, password):
  if isinstance(password, HiddenPassword):
    password = password.password
  with rasterio.open(reference) as ds:
    gis_info = GisInfo(bounds=ds.bounds, affine=ds.meta['affine'],
                       srid=get_srid(ds.crs), dtype='float32', nodata=-9999)
    conn_info = ConnInfo(db=db, host=host, user=user, password=password)
    out = do_query(gis_info, conn_info)
    meta = ds.meta.copy()
    meta.update({'dtype': gis_info.dtype, 'nodata': gis_info.nodata})
    with rasterio.open(out_file, 'w', **meta) as dst:
      dst.write(out, 1)
    show(out)
  
if __name__ == '__main__':
  generate()
