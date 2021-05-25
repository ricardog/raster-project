#!/usr/bin/env python
# -*- coding: utf-8 -*-

import click
from collections import OrderedDict
import fiona
import json
import os
import pandas as pd
import re
import shapely.geometry
import shapely.ops

import projections.utils as utils


def cname_to_fips(name, df):
    def rematch(regexp, name):
        if isinstance(regexp, str):
            return re.search(regexp, name, re.I) is not None
        return False

    def cleanup(index):
        row = df[index]["fips"]
        assert len(row) == 1
        return row.values[0]

    if not isinstance(name, (str)):
        return None
    index = df["cow.name"] == name
    if index.any():
        return cleanup(index)
    index = df["country.name.en.regex"].apply(rematch, args=(name,))
    if index.any():
        return cleanup(index)
    index = df["country.name.de.regex"].apply(rematch, args=(name,))
    if index.any():
        return cleanup(index)
    return name


def merge(src, dst, regions, cnames):
    wrap = lambda cn: cname_to_fips(cn, cnames)                  # noqa E731
    for region in regions:
        click.echo("processing %s" % region)
        fips_names = map(wrap, regions[region])
        features = filter(lambda s: s["properties"]["FIPS"] in fips_names, src)
        shapes = map(shapely.geometry.shape, [f["geometry"] for f in features])
        union = shapely.ops.unary_union(shapes)
        props = OrderedDict({"name": region})
        dst.write(
            {
                "geometry": shapely.geometry.mapping(union),
                "type": features[0]["type"],
                "properties": props,
            }
        )


@click.command()
@click.argument("borders", type=click.Path())
@click.argument(
    "regions",
    type=click.File("r"),
    default=os.path.join(utils.data_root(), "ssp-data", "regions.json"),
)
@click.argument(
    "country-names",
    type=click.Path(),
    default=os.path.join(utils.data_root(), "ssp-data", "country-names.csv"),
)
@click.argument("output", type=click.Path(dir_okay=False, writable=True))
def main(borders, regions, country_names, output):
    cnames = pd.DataFrame.from_csv(country_names)
    region_data = json.load(regions)
    with fiona.open(borders) as src:
        meta = src.meta
        meta["schema"]["properties"] = OrderedDict({"name": "str:8"})
        with fiona.open(output, "w", **meta) as dst:
            merge(src, dst, region_data, cnames)


if __name__ == "__main__":
    main()
