#!/usr/bin/env python3

import click
from netCDF4 import Dataset
import numpy.ma as ma
import rasterio
import rasterio.warp as rwarp

from projections.utils import luh2_scenarios, luh2_states

def get_crs(src):
    if src.crs is None or src.crs == '':
        return rasterio.crs.CRS.from_string('epsg:4326')
    return src.crs

def calc_xform(src, res):
    crs = get_crs(src)
    xform, width, height =  rwarp.calculate_default_transform(crs,
                                                              crs,
                                                              src.width,
                                                              src.height,
                                                              *src.bounds,
                                                              resolution=res)
    return rwarp.aligned_target(xform, width, height, res)

def downsample(src):
    summed = src.reshape(360, 2, 720, 2).sum(3).sum(1)
    out = (summed / 4).astype('float32')
    return out

@click.command()
@click.argument('scenario', type=click.Choice(luh2_scenarios()))
@click.argument('year', type=int)
@click.argument('datafile', type=click.Path(dir_okay=False))
@click.argument('outfile', type=click.Path(dir_okay=False))
@click.option('--algo', '-a', type=click.Choice(('ratio', 'minus')),
              default='ratio')
def do_it(scenario, year, datafile, outfile, algo):
    print(scenario)
    states = luh2_states(scenario)
    primf = rasterio.open(f'netcdf:{states}:primf')
    primn = rasterio.open(f'netcdf:{states}:primn')
    secdf = rasterio.open(f'netcdf:{states}:secdf')
    secdn = rasterio.open(f'netcdf:{states}:secdn')
    rland = rasterio.open(f'netcdf:{states}:range')

    with rasterio.open(f'netcdf:{datafile}:LC_area_share') as src:
        xform, width, height = calc_xform(primf, src.res)
    nodata = -9999.0
    meta = primf.meta.copy()
    crs = get_crs(primf)

    with Dataset(datafile) as ds:
        years = [year for year in ds.variables['time'][:].astype(int).tolist()
                 if year > 2014]
        meta.update({'driver': 'GTiff', 'compression': 'lzw', 'predictor': 3,
                     'count': len(years), 'transform': xform, 'crs': crs,
                     'width': width, 'height': height, 'nodata': nodata})
        with rasterio.open(outfile, 'w', **meta) as dst:
            with rasterio.open('grassland.tif', 'w', **meta) as dst2:
                for idx, year in enumerate(years):
                    print(year)
                    other = ds.variables['LC_area_share'][idx, 3, :, :]
                    rangeland = downsample(rland.read(year - 2014, masked=True))
                    if algo == 'ratio':
                        prim = (downsample(primf.read(year - 2014, masked=True)) +
                                downsample(primn.read(year - 2014, masked=True)) +
                                downsample(secdf.read(year - 2014, masked=True)) +
                                downsample(secdn.read(year - 2014, masked=True)))
                        ratio = prim / (prim + rangeland)
                        other = other * ratio
                    else:
                        other = other - rangeland
                        other = ma.clip(other, 0.0, 1.0)
                    other.fill_value = nodata
                    dst.write(other.filled().astype('float32'), indexes=idx + 1)

                    grass = ds.variables['LC_area_share'][idx, 3, :, :] - other
                    grass.fill_value = nodata
                    dst2.write(grass.filled().astype('float32'), indexes=idx + 1)
    return

if __name__ == '__main__':
    do_it()
