#!/usr/bin/env python3

import csv
import click
import pandas as pd
import rpy2.robjects as robjects
from rpy2.robjects import default_converter, pandas2ri
from rpy2.rinterface import SexpS4
from rpy2.robjects.conversion import Converter, localconverter


def ri2ro_s4(obj):
    res = obj
    return res


def read_rds(path):
    pandas2ri.activate()
    print("reading...", end="", flush=True)
    my_converter = Converter("lme4-aware converter", template=default_converter)
    my_converter.ri2ro.register(SexpS4, ri2ro_s4)
    with localconverter(my_converter):
        obj = robjects.r("readRDS('%s')" % path)
    df = robjects.conversion.ri2py(obj)
    print("done")
    return df


def write_rds(df, path):
    writer = robjects.r("saveRDS")
    writer(df, path)


@click.group()
def cli():
    pass


@cli.command()
@click.argument("infile", type=click.File(mode="rb"))
@click.argument("outfile", type=click.File(mode="w"))
def rds2csv(infile, outfile):
    # pdb.set_trace()
    df = read_rds(infile.name)
    writer = csv.writer(outfile)
    writer.writerow(df.columns)
    for row in df.itertuples():
        writer.writerow(row)


@cli.command()
@click.argument("infile", type=click.File(mode="r"))
@click.argument("outfile", type=click.File(mode="wb"))
def csv2rds(infile, outfile):
    # pdb.set_trace()
    df = pd.DataFrame.from_csv(infile.name)
    write_rds(df, outfile.name)


if __name__ == "__main__":
    cli()
