#!/usr/bin/env python

import numpy as np
import numpy.ma as ma
import os
import rasterio
import rasterio.warp as rwarp
import subprocess
import pdb

import projections.poly as poly
from projections.rasterset import Raster, RasterSet
import projections.reproject as reproj
from projections.simpleexpr import SimpleExpr
import projections.utils as utils

def luh2_states(ssp):
  if ssp != 'historical':
    dname = utils.luh2_prefix() + ssp.upper()
  else:
    dname = ssp
  return 'netcdf:' + os.path.join(utils.luh2_dir(), dname, 'states.nc')

def luh2_secd(ssp):
  return 'netcdf:' + os.path.join('ds/luh2', 'secd-%s.nc' % ssp)

def luh2_secd_types():
  return [x % fnf
          for fnf in ('f', 'n')
          for x in ('secd%s%%s' % n for n in ('y', 'i', 'm'))]

def luh2_types(ssp, year):
  res = {}
  assert ssp in utils.luh2_scenarios()
  path = luh2_states(ssp)
  if ssp == 'historical':
    assert year >= 850 and year < 2015
    bidx = year - 849
  else:
    assert year >= 2015
    bidx = year - 2014
  for lu in ['primf', 'primn', 'secdf', 'secdn', 'pastr', 'range',
             'urban', 'c3ann', 'c3per', 'c4ann', 'c4per', 'c3nfx']:
    res[lu] = Raster(lu, '%s:%s' % (path, lu), bidx)
  for secd in luh2_secd_types():
    res[secd] = Raster(secd, '%s:%s' % (luh2_secd(ssp), secd), bidx)
  return res

def rset_add(rasters, name, expr):
  rasters[name] = SimpleExpr(name, expr)

def luh2_rasterset(scenario, year):
  rset = luh2_types('historical', 1999)
  rset_add(rset, 'perennial', 'c3per + c4per')
  rset_add(rset, 'annual', 'c3ann + c4ann')
  rset_add(rset, 'nitrogen', 'c3nfx')
  rset_add(rset, 'rangelands', 'range')
  rset_add(rset, 'secondaryf', 'secdyf + secdif + secdmf')
  rset_add(rset, 'secondaryn', 'secdyn + secdin + secdmn')
  rset_add(rset, 'secondary',
           'secdyf + secdif + secdmf + secdyn + secdin + secdmn')
  return RasterSet(rset)

def process_lu(rcp_lu, comps, luh2, mask=None):
  rcp_lui_ds = rasterio.open('ds/lui/%s.tif' % rcp_lu)
  rcp_lui_data = rcp_lui_ds.read(masked=True)
  rcp_lu_ds = rasterio.open('ds/lu/rcp/hyde/%s_1999.tif' % rcp_lu)
  rcp_lu_data = rcp_lu_ds.read(masked=True)
  rcp_lui_data /= rcp_lu_data
  meta, data = reproj.reproject2(rcp_lui_ds, rcp_lui_data, (0.25, 0.25),
                                 rwarp.Resampling.mode)
  lu_meta = meta.copy()
  lu_meta.update({'count': 1})
  
  count = meta['count']
  if mask is not None:
    for idx in range(count):
      np.logical_or(data[idx].mask, mask, data[idx].mask)

  arrays = (luh2.eval(what)[0] for what in comps)
  shares = ma.array(tuple(arrays), fill_value=-9999)
  total = shares.sum(axis=0)
  #fract = shares / total
  fract = ma.empty_like(shares)
  for idx in xrange(shares.shape[0]):
    fract[idx] = ma.where(total == 0, 0, shares[idx] / total)

  for idx, lu in enumerate(comps):
    with rasterio.open('ds/luh2/%s.tif' % lu, 'w', **meta) as dst:
      xxx = data * fract[idx] * shares[idx]
      dst.write(xxx.filled(meta['nodata']), indexes=range(1, count + 1))
    with rasterio.open('ds/luh2/lu-%s.tif' % lu, 'w', **lu_meta) as dst:
      dst.write(shares[idx].filled(meta['nodata']), indexes=1)

    cmd = [os.path.join(os.getcwd(), 'lu-recalibrate.R'),
           '-m', utils.outdir(),
           '--hpd', 'ds/luh2/gluds00ag-full.tif',
           '-u', 'ds/luh2/un_subregions-full.tif',
           '--mask',
           'netcdf:%s/staticData_quarterdeg.nc:icwtr' % utils.luh2_dir(),
           '--lu', 'ds/luh2/lu-%s.tif' % lu,
           '--lui', 'ds/luh2/%s.tif' % lu,
           '-o', 'ds/luh2/%s-recal.tif' % lu,
           '-t', rcp_lu]
    subprocess.check_output(cmd, shell=False)

def main(scenario='historical', year=1999):
  static = os.path.join(utils.data_root(), 'luh2_v2',
                        'staticData_quarterdeg.nc')
  icewtr = rasterio.open('netcdf:%s:icwtr' % static)
  icewtr_mask = ma.where(icewtr.read(1) == 1.0, True, False)
  
  # How to allocate current land use types
  rcp = {'cropland': ['perennial', 'annual', 'nitrogen'],
         'pasture': ['pastr', 'range'],
         'primary': ['primf', 'primn'],
         'secondary': ['secdyf', 'secdif', 'secdmf',
                       'secdyn', 'secdin', 'secdmn'],
         'urban': ['urban']}

  luh2 = luh2_rasterset(scenario, year)

  for rcp_lu in rcp:
    process_lu(rcp_lu, rcp[rcp_lu], luh2, mask=icewtr_mask)

if __name__ == '__main__':
  main('historical', 1999)
