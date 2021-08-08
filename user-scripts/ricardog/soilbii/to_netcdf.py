#!/usr/bin/env python3

import datetime
from pathlib import Path

import h5netcdf
import numpy as np
import pandas as pd
import rasterio

from projutils.utils import outfn


def s2b(ss):
    return np.asarray(ss, dtype="bytes")


def year2days(year):
    return (datetime.date(year, 1, 1) - datetime.date(1970, 1, 1)).days


def list_files(path):
    #import pdb; pdb.set_trace()
    data = [pp.stem.split("-") + [str(pp)]
            for pp in path.glob("historical-*-*.tif")]
    df = pd.DataFrame(data, columns=["Scenario", "Indicator", "Year",
                                     "Path"])
    return df.groupby(["Scenario", "Indicator"])\
             .apply(lambda s: s.sort_values(by="Year"))


def get_lat_lon(src):
    lat = np.arange(src.height, dtype='float32') * \
        src.transform.e + src.transform.f
    lon = np.arange(src.width, dtype='float32') * \
        src.transform.a + src.transform.c
    return lat, lon


def get_days(df):
    years = df.Year.unique().astype(int).tolist()
    return np.array([year2days(yy) for yy in years], dtype="i4"), years


def create_dims(handle, dims, attrs):
    handle.dimensions = dict([(name, len(values))
                              for name, values in dims.items()])
    for name, values in dims.items():
        v = handle.create_variable(name, (name,), dtype=values.dtype,
                                   data=values)
        if name in attrs:
            for attr, val in attrs[name].items():
                v.attrs[attr] = val
    return handle


def create_vars(handle, crs, xform):
    lat_lon = handle.create_variable("latitude_longitude", (), "|S1")
    lat_lon.attrs["grid_mapping_name"] = "latitude_longitude"
    lat_lon.attrs["spatial_ref"] = crs.to_wkt()
    lat_lon.attrs["GeoTransform"] = " ".join(map(str, xform.to_gdal()))

    handle.attrs["Conventions"] = s2b("CF-1.6")
    handle.attrs["history"] = f"Created on {datetime.datetime.today()}"
    return


def write_data(handle, row, years):
    scenario, indicator, year, path = row.tolist()
    idx = years.index(int(year))
    with rasterio.open(path) as src:
        if scenario not in handle:
            handle.create_group(scenario)
        group = handle[scenario]
        if indicator not in group:
            v = group.create_variable(indicator, ("time", "lat", "lon"),
                                      dtype=src.dtypes[0],
                                      chunks=(1, src.height, src.width))
            v.attrs["_FillValue"] = src.nodata
            v.attrs["grid_mapping"] = "latitude_longitude"
            v.attrs["cell_methods"] = "time: point"
        v = group[indicator]
        v[idx, :, :] = src.read(1)
    return


def from_output():
    data_dir = Path(outfn("luh2", "soilbii"))
    files = list_files(data_dir)
    with rasterio.open(files.iloc[0].Path) as src:
        lats, lons = get_lat_lon(src)
        days, years = get_days(files)
        crs = src.crs
        xform = src.transform
    dims = {'time': days, 'lon': lons, 'lat': lats}
    ref_dt = datetime.date(1970, 1, 1).isoformat()
    attrs = {
        "time": {
            "units": f"days since {ref_dt}",
            "calendar": "standard",
            "standard_name": "time",
            "axis": "T",
        },
        "lon": {
            "units": "degrees_east",
            "long_name": "longitude",
            "standard_name": "longitude",
            "axis": "X",
        },
        "lat": {
            "units": "degrees_north",
            "long_name": "latitude",
            "standard_name": "latitude",
            "axis": "Y",
        }
    }

    with h5netcdf.File(data_dir / "soilbii.nc", "w",
                       decode_vlen_strings=False) as nc:
        create_dims(nc, dims, attrs)
        create_vars(nc, crs, xform)
        for idx, row in files.iterrows():
            write_data(nc, row, years)
    print("done")
    return


if __name__ == '__main__':
    from_output()

