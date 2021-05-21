#!/usr/bin/env python3

import click
import fiona
import pdb


@click.command()
@click.argument("in_file", type=str)
@click.argument("out_file", type=click.Path(dir_okay=False))
@click.option("--vfs", type=str)
def doit(in_file, out_file, vfs):
    if vfs:
        input = fiona.open(in_file, vfs=vfs)
    else:
        input = fiona.open(in_file)
    # The output has the same schema
    output_schema = input.schema.copy()
    # write a new shapefile
    with fiona.open(
        out_file, "w", "ESRI Shapefile", output_schema, crs=input.crs
    ) as output:
        for elem in filter(
            lambda feat: feat["properties"].get("type") == "Land", input
        ):
            print("processing %d" % elem["properties"].get("OBJECTID"))
            output.write(elem)


if __name__ == "__main__":
    doit()
