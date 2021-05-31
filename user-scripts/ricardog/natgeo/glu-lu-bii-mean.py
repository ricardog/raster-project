#!/usr/bin/env python3

import click
import numpy as np
import numpy.ma as ma
import pandas as pd
import rasterio

R_MAJOR = 6_378_137.0000
R_MINOR = 6_356_752.3142


class YearRangeParamType(click.ParamType):
    name = "year range"

    def convert(self, value, param, ctx):
        try:
            try:
                return [int(value)]
            except ValueError:
                values = value.split(":")
                if len(values) == 3:
                    low, high, inc = values
                elif len(values) == 2:
                    low, high = values
                    inc = "1"
                else:
                    raise ValueError
                return range(int(low), int(high), int(inc))
        except ValueError:
            self.fail("%s is not a valid year range" % value, param, ctx)


YEAR_RANGE = YearRangeParamType()


def band_area(lats):
    rlats = np.radians(lats)
    e = np.sqrt(1 - (R_MINOR / R_MAJOR) ** 2)
    zm = 1 - e * np.sin(rlats)
    zp = 1 + e * np.sin(rlats)
    c = 2 * np.arctanh(e * np.sin(rlats))
    area = np.pi * R_MINOR ** 2 * (c / (2 * e) + np.sin(rlats) / (zp * zm))
    return area


def cell_area(lats, x_res):
    slices = band_area(lats)
    return slices * (x_res / 360.0)


def raster_cell_area(ds):
    x_res, y_res = ds.res
    x_max, y_max = (0, 0) * ds.transform
    x_min, y_min = (ds.width, ds.height) * ds.transform
    if y_min * y_max > 0:
        raise RuntimeError("Not implemented")
    else:
        # FIXME: Check there is a grid at 0.0
        _, zero_y = (0, 0) * ~ds.transform
        # print(zero_y)
        cords = ((0, y) * ds.transform for y in reversed(range(0, int(zero_y))))
        lats = np.abs(np.array(tuple((cc[1] for cc in cords))))
        area = cell_area(lats, x_res)
        p_area = np.diff(area, 1, prepend=0)[::-1]

        cords = ((0, y) * ds.transform for y in range(int(zero_y) + 1, ds.height + 1))
        lats = np.abs(np.array(tuple((cc[1] for cc in cords))))
        area = np.abs(cell_area(lats, x_res))
        m_area = np.diff(area, 1, prepend=0)

        areas = (
            np.concatenate(
                (p_area.reshape(p_area.shape[0], 1), m_area.reshape(m_area.shape[0], 1))
            )
            / 1e6
        )
    assert areas.shape[0] == ds.height
    return areas


@click.command()
@click.argument("years", type=YEAR_RANGE)
@click.argument("template", type=str)
@click.option("--npp", type=click.Path(dir_okay=False))
def main(years, template, npp):
    df = pd.DataFrame({"Year": [], "Intact": [], "Actual": [], "BII": []})
    with rasterio.open(npp) as npp_ds:
        for idx, year in enumerate(years):
            fname = template % year
            with rasterio.open(fname) as ds:
                areas = raster_cell_area(ds)
                data = ds.read(1, masked=True)
                npp_data = npp_ds.read(1, masked=True, window=npp_ds.window(*ds.bounds))
                data *= npp_data
                data = ma.masked_where(np.isnan(data), data)
                mask = np.where(data.mask, 0.0, npp_data)
                intact = (mask * areas).sum()
                actual = (data * areas).sum()
                bii = actual / intact
                print("%4d\t%9.3f\t%9.3f\t%5.3f" % (year, actual, intact, bii))
                df.loc[idx] = [year, actual, intact, bii]
    return df


if __name__ == "__main__":
    df = main()
    print(df)
    df.to_csv("summary.csv", index=False)
