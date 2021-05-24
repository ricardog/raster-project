#!/usr/bin/env python3

from copy import copy
import os

import click
import matplotlib
import matplotlib.pyplot as plt
from mpl_toolkits.axes_grid1 import make_axes_locatable
import numpy as np
import numpy.ma as ma
import rasterio
from rasterio.plot import show, plotting_extent
from rasterio.warp import Resampling, calculate_default_transform, reproject

# from descartes import PolygonPatch
# from fiona import collection
import cartopy.crs as ccrs

import projections.utils as utils


def read_historical(start, end, bounds, metric):
    path = "/out/luh2/historical-%s-%%d.tif" % metric
    nodata = -9999.0
    data = []
    last_year = None
    for year in range(start, end):
        fname = path % year
        if os.path.isfile(fname):
            with rasterio.open(fname) as src:
                assert src.nodata == nodata
                win = src.window(*bounds)
                d = src.read(1, masked=True, window=win)
            if last_year is not None and (year - last_year != 1):
                # Interpolate between the values
                delta = year - last_year
                f1 = 1.0 / delta
                for yy in range(last_year + 1, year):
                    i = yy - last_year
                    dd = data[-1] * i * f1 + d * (delta - i) * f1
                    data.append(dd)
                pass
            data.append(d)
            last_year = year
    stack = np.stack(data, axis=0)
    stack2 = ma.masked_equal(stack, nodata)
    return stack2


def project(dst_crs, src, src_data, src_bounds):
    src_height, src_width = src_data.shape
    dst_transform, dst_width, dst_height = calculate_default_transform(
        src.crs, dst_crs, src_width, src_height, *src_bounds
    )
    dst_data = ma.zeros((dst_height, dst_width), "int32")
    dst_data.fill_value = src.nodata
    reproject(
        source=src_data.filled().astype("int32"),
        destination=dst_data,
        src_transform=src.affine,
        src_crs=src.crs,
        dst_transform=dst_transform,
        dst_crs=dst_crs,
        src_nodata=src.nodata,
        dst_nodata=src.nodata,
        resampling=Resampling.bilinear,
    )
    return (
        dst_transform,
        dst_width,
        dst_height,
        ma.masked_equal(dst_data.astype(src_data.dtype), -9999),
    )


@click.command()
@click.argument(
    "metric",
    type=click.Choice(["Ab", "SR", "CompSimAb", "CompSimSR", "BIIAb", "BIISR"]),
)
@click.argument("scenario", type=click.Choice(utils.luh2_scenarios()))
@click.option("--start", "-s", type=int, default=1900)
@click.option("--limit", "-l", type=float, default=1.2)
@click.option("--out", "-o", type=click.File(mode="wb"))
@click.option("--dst_crs", "-d", type=str)
def main(metric, scenario, start, limit, out, dst_crs):
    """Generate a raster of how much we can turn back the clock for a SSP
    scenario.

      metric   -- Which metric to use for the calculation.

      scenario -- Which scenario to use.

      start    -- The year at which to start the comparison.

      limit    -- Mask cells where the metric is > limit at both the start
                  and end of the sequence.

      out      -- Name of the output file.  The script save the data as a
                  GeoTIFF (raw) and a rendered PNG.

      dst-crs  -- Use the specified CRS for projecting the rendered raster.

    """
    palette = copy(plt.cm.viridis_r)
    palette.set_under("y", 1.0)
    palette.set_over("r", 1.0)
    palette.set_bad("w", 1.0)

    fname = "/out/luh2/%s-%s-%d.tif" % (scenario, metric, 2100)
    with rasterio.open(fname) as src:
        meta = src.meta
        end = src.read(1, masked=True)
        stack = read_historical(start, 2015, src.bounds, metric)
    inc = ma.where(stack < end, 1, 0)
    years = inc.sum(axis=0)
    years2 = ma.where(
        end > stack[-1], ma.where(end > stack[0], start - 1, 2015 - years), 2016
    )
    mask = ma.where((end > limit) & (stack[-1] > limit), True, False)
    years2.mask = np.logical_or(years2.mask, mask)
    years2.fill_value = src.nodata

    if out:
        meta_out = meta.copy()
        meta_out["dtype"] = "int32"
        with rasterio.open(out.name, "w", **meta_out) as dst:
            dst.write(years2.filled(meta_out["nodata"]).astype(np.int32), indexes=1)
    title = "Year to which BII recovers by 2100"
    vmin = start - 2
    vmax = 2015
    dpi = 100.0
    size = [years2.shape[1] / dpi, years2.shape[0] / dpi]
    size[1] += 70 / dpi
    fig = plt.figure(figsize=size, dpi=dpi)
    if dst_crs:
        with rasterio.open(out.name) as src:
            data = src.read(
                1,
                masked=True,
                window=src.window(*(-180, -90, 180, 90)),  # *src.bounds))
            )
            # crs = ccrs.Robinson()
            crs = ccrs.Mollweide()
            dst_crs = crs.proj4_params
            (dst_transform, dst_width, dst_height, dst_data) = project(
                dst_crs, src, data, (-180, -90, 180, 90)  # src.bounds)
            )
        xmin, ymax = dst_transform * (0, 0)
        xmax, ymin = dst_transform * (dst_width, dst_height)
        # taff = Affine.from_gdal(-18040068.169145808, 25055.6578813187,
        #                        0.0, 9020047.848073646, 0.0, -25055.6578813187)
        # xmin, ymax = taff * (0, 0)
        # xmax, ymin = taff * (1436, 728)
        ax = plt.axes(projection=crs)
        ax.imshow(
            dst_data,
            origin="upper",
            extent=[xmin, xmax, ymin, ymax],
            cmap=palette,
            vmin=vmin,
            vmax=vmax,
        )
        ax.coastlines()
        # ax.set_title(title, fontweight='bold')
        sm = matplotlib.cm.ScalarMappable(cmap=palette, norm=plt.Normalize(1900, 2015))
        sm._A = []
        cb = plt.colorbar(sm, orientation="vertical")
        cb.set_label(title)
    else:
        ax = plt.gca()
        show(
            years2,
            ax=ax,
            cmap=palette,
            title=title,
            vmin=vmin,
            vmax=vmax,
            extent=plotting_extent(src),
        )
        divider = make_axes_locatable(ax)
        cax = divider.append_axes("bottom", size="5%", pad=0.25)
        plt.colorbar(ax.images[0], cax=cax, orientation="horizontal")
    fig.tight_layout()
    # ax.axis('off')
    if out:
        fig.savefig(out.name.replace(".tif", ".png"), transparent=False)
    plt.show()


if __name__ == "__main__":
    main()
