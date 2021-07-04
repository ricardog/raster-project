#!/usr/bin/env python3

import click
import geopandas as gpd
import numpy as np
import numpy.ma as ma
import pandas as pd
from pathlib import Path
import rasterio
import rasterio.mask
import rasterio.features

from projutils.utils import data_file, outfn


def get_data_file(name):
    return Path(data_file("restore", "brazil", name))


def get_shapes(shapefile):
    raw_shapes = gpd.read_file(get_data_file(shapefile))
    raw_shapes[["Column", "Row"]] = raw_shapes.GRD30.str.split(" - ", expand=True)
    raw_shapes.Column = raw_shapes.Column.astype(int)
    raw_shapes.Row = raw_shapes.Row.astype(int)
    return raw_shapes


def get_urban_data(shapefile, urbanf):
    raw_shapes = get_shapes(shapefile)
    biomas = pd.read_csv(get_data_file(urbanf))
    biomas[['Fraction']] = biomas.groupby('Colrow')\
                                 .apply(lambda x: x['sum'] / x['sum'].sum())\
                                 .reset_index()['sum']
    urban = biomas[biomas.MapBiomas_description == 'Urban Infrastructure']
    shapes = raw_shapes.merge(urban[['Colrow', 'Fraction']], on='Colrow',
                              how='left')
    shapes.Fraction = shapes.Fraction.fillna(0.0)
    return shapes


def read_data(shapefile, areaf, landusef):
    raw_shapes = get_shapes(shapefile)
    area = pd.read_csv(get_data_file(areaf), header=None)
    area.columns = ["Country", "Cell", "TotalArea"]
    shapes = raw_shapes.merge(area, right_on="Cell", left_on="Colrow")
    landuse = pd.read_csv(get_data_file(landusef), header=None)
    landuse.columns = ["Country", "Cell", "LandUse", "Year", "Area"]
    return shapes, landuse


def get_fname(scenario, lu):
    fname = outfn("luh2", "restore", "brazil", scenario, f"{lu}.tif")
    parent = Path(fname).parent
    if not parent.exists():
        parent.mkdir()
    return fname


def get_xform(shapes, reference):
    import pdb; pdb.set_trace()
    raw = [geo for geo in shapes.geometry]
    with rasterio.open(outfn("luh2", reference)) as ref:
        img, xform = rasterio.mask.mask(ref, raw, crop=True)
    return (img.shape[1:], xform)


def write(fname, data, xform, crs, years):
    meta = {
        "driver": "GTiff",
        "dtype": "float32",
        "height": data.shape[1],
        "width": data.shape[2],
        "count": len(years),
        "transform": xform,
        "crs": crs,
        "compress": "lzw",
        "predictor": 3,
        "nodata": data.fill_value,
    }
    with rasterio.open(fname, "w", **meta) as out_ds:
        out_ds.write(data, indexes=range(1, len(years) + 1))
    return


def to_array(scenario, landuse, shapes, lu, shape, xform):
    crs = rasterio.crs.CRS.from_epsg(shapes.crs.to_epsg())
    height = shapes.Row.max() - shapes.Row.min() + 1
    width = shapes.Column.max() - shapes.Column.min() + 1
    rmin = shapes.Row.min()
    cmin = shapes.Column.min()
    nodata = -9999.0
    years = sorted(landuse.Year.unique())
    count = len(years)
    out = np.full([count, height, width], nodata, dtype="float32")
    row = shapes.Row.array - rmin
    col = shapes.Column.array - cmin
    out[:, row, col] = 0
    for idx, year in enumerate(years):
        rows = landuse[(landuse.Year == year) & (landuse.LandUse == lu)]
        if len(rows) > 0:
            row = rows.Row.array - rmin
            col = rows.Column.array - cmin
            value = rows.Fraction.array
            out[idx, row, col] = value
    ma_out = ma.masked_equal(out, nodata)
    write(get_fname(scenario, lu), ma_out, xform, crs, years)
    return


def to_array2(shapes, shape, xform):
    crs = rasterio.crs.CRS.from_epsg(shapes.crs.to_epsg())
    height = shapes.Row.max() - shapes.Row.min() + 1
    width = shapes.Column.max() - shapes.Column.min() + 1
    rmin = shapes.Row.min()
    cmin = shapes.Column.min()
    nodata = -9999.0
    out = np.full([1, height, width], nodata, dtype="float32")
    row = shapes.Row.array - rmin
    col = shapes.Column.array - cmin
    out[0, row, col] = shapes.Fraction.array
    ma_out = ma.masked_equal(out, nodata)
    fname = outfn("luh2", "restore", "brazil", "urban.tif")
    write(fname, ma_out, xform, crs, (1,))
    return


@click.group()
def cli():
    return


@cli.command()
@click.argument("shapefile", type=str)
@click.argument("area", type=str)
@click.argument("landuse", type=str)
@click.argument("reference", type=click.Path(dir_okay=False))
def rasterize(shapefile, area, landuse, reference):
    scenario = Path(landuse).stem
    cells, land_use = read_data(shapefile, area, landuse)
    shape, xform = get_xform(cells, reference)
    land_use = land_use.merge(cells[["Cell", "TotalArea", "Column", "Row"]], on="Cell")
    land_use["Fraction"] = land_use.Area / land_use.TotalArea
    for lu in land_use.LandUse.unique():
        print(f"Processing {lu}")
        to_array(scenario, land_use, cells, lu, shape, xform)
    return


@cli.command()
@click.argument("landuse", nargs=-1, type=click.Path(dir_okay=False))
def check(landuse):
    import matplotlib.pyplot as plt

    if not landuse:
        return
    srcs = [rasterio.open(xx) for xx in landuse]
    count = [xx.count for xx in srcs]
    assert len(set(count)) == 1
    bands = count[0]
    for idx in range(bands):
        data = ma.stack([xx.read(idx + 1, masked=True) for xx in srcs])
        total = data.sum(axis=0)
        plt.imshow(total)
        plt.show()
        print(
            "%d: %6.4f | %6.4f -- %6d"
            % (idx, total.min(), total.max(), np.isclose(total, 1.0, atol=1e-1).sum())
        )
    return


@cli.command()
@click.argument("shapefile", type=str)
@click.argument("biomas", type=str)
@click.argument("reference", type=click.Path(dir_okay=False))
def urbanize(shapefile, biomas, reference):
    cells = get_urban_data(shapefile, biomas)
    shape, xform = get_xform(cells, reference)
    to_array2(cells, shape, xform)
    return


if __name__ == "__main__":
    cli()
