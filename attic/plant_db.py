#!/usr/bin/env python3

import click
import concurrent.futures
import numpy as np
import numpy.ma as ma
import os
import psycopg2
import psycopg2.pool
import rasterio
from rasterio.warp import calculate_default_transform
import re
import shapely.wkb
import sys
import time

import pdb

#
# To create the DB:
# CREATE DATABASE trees WITH ENCODING='UTF8' LC_CTYPE='en_US.UTF-8' LC_COLLATE='en_US.UTF-8' OWNER=postgis TEMPLATE=template0 CONNECTION LIMIT=-1;
#
# To insert tree DB data into database
# ogr2ogr -f "PostgreSQL" PG:"host=bonobo.local port=5432 dbname=trees user=postgis password=postgis" plantations_v1_3_dl.gdb aus_plant

#
# To create the index
# CREATE INDEX trees_shape_geom_ids ON trees USING GIST (shape);
#

#
# The planted trees DB has what PostGIS considered illegal shapes and
# generates "tpology errors".  I fixed this by creating a new column and
# assigning it with a "valid" version of the geometry
# ALTER TABLE trees ADD COLUMN geom geometry(MultiPolygon, 4326);
# UPDATE trees SET geom = STMakeValid(geom);
# CREATE INDEX trees_geom_geom_idx ON trees USING GIST (geom);

os.environ['DB_NAME'] = 'trees'
os.environ['DB_HOST'] = '192.168.178.63'
os.environ['DB_USER'] = 'postgis'
os.environ['PASSWORD'] = 'postgis'

class HiddenPassword(object):
  """Class for prompting the user for a password.  If there is a default
(from the environment, for example, hide the default as a collection of
*'s.

  Code from
  https://stackoverflow.com/questions/41268949/python-click-option-with-a-prompt-and-default-hidden

  """
  
  def __init__(self, password=''):
    self.password = password
  def __str__(self):
    return '*' * len(self.password)

class OptionPromptNull(click.Option):
  """Click option processing class that only prompts the user for a value
if there is no default.  Set the value via an environment vairble to
skip the prompt.
  

  Code from:
  https://stackoverflow.com/questions/45868549/creating-a-click-option-with-prompt-that-shows-only-if-default-value-is-empty

  """
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

def get_crs(crs):
  """Get a valid CRS.  If it is undefined or None return a default value."""
  if crs is None or crs == {}:
    return rasterio.crs.CRS(init='epsg:4326')
  return crs

def get_srid(crs):
  """Get the SRID from a raster CRS.  This seems to work but I do not
understand all the possible ways rasterio returns CRS.  Also, on some
systems checking whether CRS is an empty has causes problems.

  Returns the EPSG code as an integer.

  """
  if crs == {} or crs is None:
    return 4326
  m = re.match(r'epsg:(\d+)$', crs['init'])
  if m:
    return int(m.group(1))
  raise RuntimeError("Unknow CRS: %s" % str(crs))

def get_bounds(pg_url, table, clause):
  with psycopg2.connect(pg_url) as conn:
    #conn = conn_pool.getconn()
    cursor = conn.cursor()
    query = "SELECT ST_SetSRID(ST_Extent(geom), 4326) " + \
            "as table_extent FROM %s %s;" % (table, clause)
    try:
      cursor.execute(query)
    except psycopg2.ProgrammingError as exc:
      print(query)
      raise exc
    
    data = cursor.fetchall()
    #conn_pool.putconn(conn)
    shape = shapely.wkb.loads(data[0][0], hex=True)
  return shape.bounds
  
def get_template():
  """Read the PostGIS query template from a file. """
  my_dir = os.path.dirname(__file__)
  fname = os.path.join(my_dir, 'plant-db.psql')
  with open(fname) as f:
    query_sql = f.read()
  return query_sql

def put(array, data):
  """Put the data returned from the PostGIS query into the output array.
The returned data is a list of tuples (row, col, value).

  """
  y = tuple(map(lambda x: x[0] - 1, data))
  x = tuple(map(lambda x: x[1] - 1, data))
  v = tuple(map(lambda x: x[2], data))
  try:
    idx = np.ravel_multi_index((y, x), array.shape)
  except Exception as e:
    pdb.set_trace()
    str(e)
    pass
  np.put(array, idx, v)

# Code ideas from 
def do_block(dst, win, conn_pool, template):
  """Do one PostGIS query (for a block window).  Grabs one connection from
the connection pool, does the query, returns the connection to
the pool and stuffs the query data into the output array.

  Example for using threaded connection pool is from 
  https://stackoverflow.com/questions/34815650/python-multithread-and-postgresql

  Returns the data as a new array (shape of array given by block shape).

  """
  width = win.width
  height = win.height
  xoff, yoff = dst.transform * (win.col_off, win.row_off)
  params = {'width': width,
            'height': height,
            'xres': dst.transform[0],
            'yres': dst.transform[4],
            'xoff': xoff,
            'yoff': yoff,
            'srid': get_srid(dst.crs)
            }
  out = np.full((height, width), dst.nodata, dtype=dst.dtypes[0])
  #print(template % params)
  stime = time.time()
  conn = conn_pool.getconn()
  cursor = conn.cursor()
  try:
    cursor.execute(template, params)
    data = cursor.fetchall()
  except Exception as ex:
    print('exception caught in do_block')
    print(ex)
    sys.exit()
  finally:
    conn_pool.putconn(conn)
  etime = time.time()
  print("[%d:%d] executed in %7.2fs" % (win.col_off, win.row_off,
                                        etime - stime))
  if len(data) > 0:
    put(out, data)
  return ma.masked_equal(out, dst.nodata)
  
def do_parallel(src, dst, pg_url, table, clause, num_workers):
  """Generate road length data for an entire raster.  Uses threads and a
connection pool to parallelize queries to the database.

  Takes as input a reference raster that defines the bounds and the
  block shape of the queries.  The code does one query per block window.
  Only the master thread writes to the output file.  Each slave thread
  does a query and returns the result data stuffed into a new array
  (shape set by block shape).

  """
  template = get_template().format(table=table, clause=clause)

  conn_pool = psycopg2.pool.ThreadedConnectionPool(1, num_workers, pg_url)
  
  def compute(win):
    return do_block(dst, win, conn_pool, template)

  stime = time.time()
  with concurrent.futures.ThreadPoolExecutor(max_workers=num_workers) as executor:
    future_to_window = {
      executor.submit(compute, win): win for _, win in dst.block_windows()
    }
    for future in concurrent.futures.as_completed(future_to_window):
      win = future_to_window[future]
      out = future.result()
      dst.write(out, window=win, indexes=1)
  etime = time.time()
  print("executed in %7.2fs" % (etime - stime))
      
@click.command()
@click.argument('table', type=str)
@click.argument('clause', type=str)
@click.argument('ref-raster', type=click.Path(dir_okay=False))
@click.argument('path', type=click.Path(dir_okay=False),
                default='road-length.tif')
@click.option('--num_workers', '-n', type=int, default=10)
@click.option('--db', cls=OptionPromptNull, prompt=True,
              default=lambda: os.environ.get('DB_NAME', ''))
@click.option('--host', cls=OptionPromptNull, prompt=True,
              default=lambda: os.environ.get('DB_HOST', ''))
@click.option('--user', cls=OptionPromptNull, prompt=True,
              default=lambda: os.environ.get('DB_USER', ''))
@click.option('--password',
              default=lambda: HiddenPassword(os.environ.get('PASSWORD', '')),
              hide_input=True)
def generate(table, clause, ref_raster, path, num_workers,
             db, host, user, password):
  """Wrapper around do_parallel() to process command-line options."""
  if isinstance(password, HiddenPassword):
    password = password.password
  pg_url = "postgresql://{user}:{password}@{host}/{db}".format(
    user = user, password = password, host = host, db = db)
  with rasterio.open(ref_raster) as src:
    dtype = 'float32'
    nodata = -9999
    meta = src.meta.copy()
    meta.update({'driver': 'GTiff', 'dtype': dtype, 'nodata': nodata})
    if 'compress' not in meta:
      meta.update({'compress': 'lzw', 'predictpr': 2})

    # Query DB to find bounding box of all features and use the information
    # to set the bounds of the raster.  This saves query time (empty queries
    # are not free) and generates a raster sized to only cover regions of
    # the world with features.
    bounds = get_bounds(pg_url, table, clause)
    print(bounds)
    ll = bounds[0:2]
    ur = bounds[2:]
    xl, yl = ~src.transform * ll
    xh, yh = ~src.transform * ur
    ll = src.transform * (int(xl), int(yl))
    ur = src.transform * (int(xh), int(yh))
    bounds = (ll[0], ll[1], ur[0], ur[1])
    print(bounds)

    transform, width, height = calculate_default_transform(
      get_crs(src.crs), get_crs(src.crs), src.width, src.height,
      *bounds, resolution=src.res)
    meta.update({'driver': 'GTiff', 'transform': transform,
                 'height': height, 'width': width})
    if src.crs is None or src.crs == {}:
      meta.update({'crs': rasterio.crs.CRS(init='epsg:4326')})
    with rasterio.open(path, 'w', **meta) as dst:
      do_parallel(src, dst, pg_url, table, clause, num_workers)
  
if __name__ == '__main__':
  generate()
