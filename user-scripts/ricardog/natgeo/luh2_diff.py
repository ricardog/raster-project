#!/usr/bin/env python3

import click
import numpy as np
import rasterio
import time

from projections.utils import data_file, outfn, luh2_states
from rasterset import RasterSet, SimpleExpr

from rasterset import Raster

def __infile(lu, year, path):
    return data_file(path, f'LUH2_{lu}_{year}_1KM.tif')

def __outfile(lu, path):
    return outfn(path, 'LUH2_%s_delta_1KM.tif' % lu)

def inpath(res):
    if res == 'qd':
        return 'luh2'
    elif res == '1km':
        return 'luh2_1km'
    else:
        raise ValueError("Unsupported resolution '%s'" % res)

def out_path(res, name):
    if res == 'qd':
        return outfn('luh2', f'{name}.tif')
    elif res == '1km':
        return outfn('glb-lu', f'LUH2_{name}_1KM.tif')
    else:
        raise ValueError("Unsupported resolution '%s'" % res)

def sdpt_raster(res):
    path = data_file('sdpt_' + res, 'sum-full.tif')
    return Raster('sdpt', path)
    
def in_raster(res, lu, year):
    if res == '1km':
        path = data_file('luh2_1km', f'LUH2_{lu}_{year}_1KM.tif')
        band = 1
    else:
        path = 'netcdf:' + luh2_states('historical') + ':' + lu
        band = year - 849
    return Raster(lu, path, band)

def out_raster(res, name):
    if res == '1km':
        path = outfn('glb-lu', name)
    else:
        path = outfn('luh2', name)
    return Raster(name, path)

@click.command()
@click.argument('resolution', type=click.Choice(['qd', '1km']))
def rasters(resolution):
    ystart = 2000
    yend = 2014
    layers = ('primf', 'primn', 'secdf', 'secdn')
    for lu in layers:
        oname = lu + '_delta'
        sraster = in_raster(resolution, lu, ystart)
        eraster = in_raster(resolution, lu, yend)
        oraster = SimpleExpr(oname, 'clip((start - end), 0, 1)')
        rset = RasterSet({'start': sraster,
                          'end': eraster,
                          oname: oraster })
        stime = time.time()
        rset.write(oname, out_path(resolution, oname))
        etime = time.time()
        print("executed in %6.2fs" % (etime - stime))
    oname = 'sum_delta'
    rasters = dict(((name, Raster(name, out_path(resolution, name)))
                    for name in (_ + '_delta' for _ in layers)))
    sum_delta = SimpleExpr(oname, ' + '.join(_ + '_delta' for _ in layers))
    rasters.update({oname: sum_delta})
    rset = RasterSet(rasters)
    stime = time.time()
    rset.write(oname, out_path(resolution, oname))
    etime = time.time()
    print("executed in %6.2fs" % (etime - stime))
    
    print('done')

    
@click.command()
@click.argument('resolution', type=click.Choice(['qd', '1km']))
def main(resolution):
    year_start = 2000
    year_end = 2014
    for lu in ('primf', 'primn', 'secdf', 'secdn'):
        print('start: ', infile(lu, year_start))
        print('end  : ', infile(lu, year_end))
        print('delta : ', outfile(lu))
        with rasterio.open(infile(lu, year_start)) as start_ds:
            with rasterio.open(infile(lu, year_end)) as end_ds:
                meta = start_ds.meta.copy()
                meta.update({'driver': 'GTiff', 'compress': 'lzw',
                             'predictpr': 2})
                with rasterio.open(outfile(lu), 'w', **meta) as delta_ds:
                    start = start_ds.read(1, masked=True)
                    end = end_ds.read(1, masked=True)
                    delta = np.clip(end - start, -2, 0)
                    delta_ds.write(delta.filled(), indexes=1)

if __name__ == '__main__':
    rasters()
