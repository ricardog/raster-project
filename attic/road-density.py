#!/usr/bin/env python

import cProfile

import click
from geopy.distance import distance
import rasterio
import fiona
import numpy as np
import numpy.ma as ma
import os
import rtree
import shapely
import shapely.geometry

import pdb


def window_shape(win):
    return (win[0][1] - win[0][0], win[1][1] - win[1][0])


def explode(coords):
    """Explode a GeoJSON geometry's coordinates object and yield coordinate
      tuples.  As long as the input is conforming, the type of the
      geometry doesn't matter.

    Source:
      https://gis.stackexchange.com/questions/90553/fiona-get-each-feature-extent-bounds
    """
    for e in coords:
        if isinstance(e, (float, int, long)):
            yield coords
            break
        else:
            for f in explode(e):
                yield f


def bbox(f):
    x, y = zip(*list(explode(f["geometry"]["coordinates"])))
    return (min(x), min(y), max(x), max(y))


def generator(layer):
    for idx, feat in enumerate(layer):
        if idx % 1000 == 0:
            print(idx)
        fid = int(feat["id"])
        shape = shapely.geometry.shape(feat["geometry"])
        # geom = shape(feat['geometry'])
        # yield(fid, geom.bounds, fid)
        yield (fid, bbox(feat), shape.to_wkb())


def gen_index(layer):
    if os.path.isfile("roads.db.idx") and os.path.isfile("roads.db.dat"):
        click.echo("using exiting index")
        return rtree.index.Index("roads.db")
    click.echo("computing index")
    index = rtree.index.Index("roads.db", generator(layer))
    click.echo("done")
    return index


def line_length(line):
    """Length of a line in meters, given in geographic coordinates

    Args:
      line: a shapely LineString object with WGS-84 coordinates

    Returns:
      Length of line in meters
    """

    return sum(distance(a, b).meters for (a, b) in pairs(line.coords))


def pairs(lst):
    """Iterate over a list in overlapping pairs without wrap-around.

    Args:
      lst: an iterable/list

    Returns:
      Yields a pair of consecutive elements (lst[k], lst[k+1]) of lst. Last
      call yields the last two elements.

    Example:
      lst = [4, 7, 11, 2]
      pairs(lst) yields (4, 7), (7, 11), (11, 2)

    Source:
        https://stackoverflow.com/questions/1257413/1257446#1257446
    """
    i = iter(lst)
    prev = i.next()
    for item in i:
        yield prev, item
        prev = item


def do_intersect(bbox, obj):
    cell = shapely.geometry.box(*bbox)
    lines = shapely.geometry.base.geom_from_wkb(obj)
    xxx = cell.intersection(lines)
    if xxx.is_empty:
        return 0
    if isinstance(xxx, shapely.geometry.multilinestring.MultiLineString):
        return sum(map(line_length, xxx))
    return line_length(xxx)


def do_block(win, mask, index):
    pdb.set_trace()
    xres, yres = mask.res
    affine = mask.window_transform(win)
    mask_data = mask.read(1, masked=True, window=win)
    out = ma.empty(mask_data.shape, dtype=np.float32)
    out.mask = mask_data.mask.copy()
    height, width = out.shape
    startx, starty = affine * (win[1][0] - xres / 2.0, win[0][0] - yres / 2.0)
    endx, endy = affine * (win[1][1] - xres / 2.0, win[0][1] - yres / 2.0)
    click.echo("block %d:%d" % (win[0][0], win[0][1]))
    lats = np.linspace(starty, endy, height)
    lons = np.linspace(startx, endx, width)
    for y in range(height):
        if y > 10:
            break
        click.echo("block %d" % (y + win[0][0]))
        lat = lats[y]
        lat_min = lat - yres / 2.0
        lat_max = lat + yres / 2.0
        for lon in lons[ma.where(mask_data.mask[y, :] != True)]:
            bbox = (lon - xres / 2.0, lat_min, lon + xres / 2.0, lat_max)
            length = 0
            for obj in index.intersection(bbox, objects="raw"):
                length += do_intersect(bbox, obj)
            # end x for loop
            # out[y, x] = length
    return out


def doit(index, mask, layer):
    bounds = layer.bounds
    mask_win = mask.window(*bounds)
    height, width = window_shape(mask_win)
    xres, yres = mask.res
    out_meta = mask.meta.copy()
    out_meta.update(
        {
            "driver": "GTiff",
            "compress": "lzw",
            "predictor": 2,
            "width": width,
            "height": height,
        }
    )
    num_rows = 100

    click.echo("processing %d:%d" % (mask_win[0][0], mask_win[0][1]))
    with rasterio.open("roads-density.tif", "w", **out_meta) as dst:
        for j in range(mask_win[0][0], mask_win[0][1], num_rows):
            win = ((j, j + num_rows), (0, width))
            out = do_block(win, mask, index)
            dst.write(out.filled(), window=win, indexes=1)
            break
    return


@click.command()
@click.argument("mask", type=click.Path())
@click.argument("shapes", type=click.Path())
def densify(mask, shapes):
    if mask is None:
        mask = "zip:%s!ICE_1km_2005.bil" % os.path.join(
            utils.data_root(), "1km", "ICE.zip"
        )
    if shapes is None:
        shapes = os.path.join(
            utils.data_root(), "groads1.0/groads-v1-global-gdb/gROADS_v1.gdb"
        )
    with fiona.open(shapes) as layer:
        with rasterio.open(mask) as mask_ds:
            index = gen_index(layer)
            wrap = lambda: doit(index, mask_ds, layer)
            cProfile.runctx(
                "wrap()", filename="restats", locals={"wrap": wrap}, globals=globals()
            )
            # doit(index, mask_ds, layer)


if __name__ == "__main__":
    densify()
