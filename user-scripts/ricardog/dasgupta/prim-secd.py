#!/usr/bin/env python3

from netCDF4 import Dataset
import numpy as np
import rasterio
import rasterio.warp as rwarp
from rasterio.plot import show

from projections.utils import data_file, luh2_states
from attic.cell_area import raster_cell_area

import pdb

def calc_crs(src):
    if src.crs is None or src.crs == '':
        return rasterio.crs.CRS.from_string('epsg:4326')
    return src.crs


def calc_xform(src):
    crs = calc_crs(src)
    xform, width, height =  rwarp.calculate_default_transform(crs,
                                                              crs,
                                                              src.width,
                                                              src.height,
                                                              *src.bounds,
                                                              resolution=2)
    return rwarp.aligned_target(xform, width, height, 2)


def downsample(in1, src, dst):
    src_carea = raster_cell_area(src) / 1e6
    dst_carea = raster_cell_area(dst) / 1e6
    area = in1 * src_carea
    summed = area.reshape(90, 4, 180, 4).sum(3).sum(1)
    out = (summed / dst_carea).astype('float32')
    return out


def calc_data(in0, in1, src, dst):
    src_carea = raster_cell_area(src) / 1e6
    dst_carea = raster_cell_area(dst) / 1e6
    area = in0 * src_carea + in1 * src_carea
    summed = area.reshape(90, 8, 180, 8).sum(3).sum(1)
    out = (summed / dst_carea).astype('float32')
    return out


def vivid_years(scenario):
    vivid_file = data_file('vivid', scenario, 'spatial_files',
                           'cell.land_0.5.nc')
    with Dataset(vivid_file) as ds:
        years = [int(yy) for yy in ds.variables['time'][:].tolist()]
    return years
    

def luh2(scenario):
    print(scenario)
    states = luh2_states(scenario)
    primf = rasterio.open(f'netcdf:{states}:primf')
    primn = rasterio.open(f'netcdf:{states}:primn')
    secdf = rasterio.open(f'netcdf:{states}:secdf')
    secdn = rasterio.open(f'netcdf:{states}:secdn')

    if scenario == 'historical':
        years = tuple(range(850, 2016, 5))
        start_year = 849
    else:
        years = tuple(filter(lambda yy: yy >= 2015, vivid_years('sample')))
        start_year = 2014
    print(years)
    xform, width, height = calc_xform(primf)
    nodata = -9999.0
    meta = primf.meta.copy()
    crs = calc_crs(primf)

    meta.update({'driver': 'GTiff', 'compression': 'lzw', 'predictor': 3,
                 'count': len(years), 'transform': xform, 'crs': crs,
                 'width': width, 'height': height, 'nodata': nodata})
    print(meta)
    with rasterio.open(f'andy-data/{scenario}-primary.tif', 'w',
                       **meta) as prim:
        with rasterio.open(f'andy-data/{scenario}-secondary.tif', 'w',
                           **meta) as secd:
            for idx, year in enumerate(years):
                bidx = year - start_year
                print(year, bidx)
                data = calc_data(primf.read(bidx, masked=True),
                                 primn.read(bidx, masked=True),
                                 primf, prim)
                data.set_fill_value(nodata)
                prim.write(data.filled(), indexes=idx + 1)
                data = calc_data(secdf.read(bidx, masked=True),
                                 secdn.read(bidx, masked=True),
                                 secdf, secd)
                data.set_fill_value(nodata)
                secd.write(data.filled(), indexes=idx + 1)
    return


def vivid(scenario):
    prim_hist = rasterio.open(f'andy-data/historical-primary.tif')
    prim_ssp = rasterio.open(f'andy-data/{scenario}-primary.tif')
    secd_hist = rasterio.open(f'andy-data/historical-secondary.tif')
    secd_ssp = rasterio.open(f'andy-data/{scenario}-secondary.tif')
    vivid_file = data_file('vivid', 'sample', 'spatial_files',
                           'cell.land_0.5.nc')
    other = rasterio.open(f'netcdf:{vivid_file}:other')
    secdf = rasterio.open(f'netcdf:{vivid_file}:secdforest')
    primf = rasterio.open(f'netcdf:{vivid_file}:primforest')

    carea = raster_cell_area(other) / 1e10
    
    nodata = -9999.0
    years = vivid_years('sample')
    print(years)
    meta = prim_hist.meta.copy()
    meta.update({'driver': 'GTiff', 'compression': 'lzw', 'predictor': 3,
                 'count': len(years), 'nodata': nodata})
    print(meta)
    with rasterio.open(f'andy-data/vivid-primary.tif', 'w',
                       **meta) as prim:
        with rasterio.open(f'andy-data/vivid-secondary.tif', 'w',
                           **meta) as secd:
            for idx, year in enumerate(years):
                print(year, idx)
                if year < 2015:
                    my_idx = tuple(range(850, 2016, 5)).index(year)
                    p1 = prim_hist.read(my_idx + 1, masked=True)
                    s1 = secd_hist.read(my_idx + 1, masked=True)
                else:
                    p1 = prim_ssp.read(idx - 4, masked=True)
                    s1 = secd_ssp.read(idx - 4, masked=True)
                odata = downsample(other.read(idx + 1, masked=True) / carea,
                                   other, prim)
                pdata = downsample(primf.read(idx + 1, masked=True) / carea,
                                   primf, prim)
                sdata = downsample(secdf.read(idx + 1, masked=True) / carea,
                                   secdf, prim)
                #import pdb; pdb.set_trace()
                #other_prim = np.clip((p1 - pdata) / odata, 0, 1)
                other_prim = p1 / (p1 + s1)
                data = pdata + odata * other_prim
                data.set_fill_value(nodata)
                prim.write(data.filled(), indexes=idx + 1)
                data = sdata + odata * (1 - other_prim)
                data.set_fill_value(nodata)
                secd.write(data.filled(), indexes=idx + 1)
    return


if __name__ == '__main__':
    #luh2('historical')
    luh2('ssp2_rcp4.5_message-globiom')

    vivid('ssp2_rcp4.5_message-globiom')

