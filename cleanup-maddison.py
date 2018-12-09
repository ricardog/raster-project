#!/usr/bin/env python3

import click
import pandas as pd
import re

def cname_to_fips(name, df):
  def rematch(regexp, name):
    if isinstance(regexp, str):
      return re.search(regexp, name, re.I) != None
    return False

  def cleanup(index):
    row = df[index]['fips']
    if len(row) > 1:
      return row.values
    return row.values[0]

  if not isinstance(name, str):
    return None
  index = df['cow.name'] == name
  if index.any():
    return cleanup(index)
  index = df['country.name.en.regex'].apply(rematch, args=(name, ))
  if index.any():
    return cleanup(index)
  index = df['country.name.de.regex'].apply(rematch, args=(name, ))
  if index.any():
    return cleanup(index)
  return name

@click.command()
@click.argument('infile', type=click.Path(dir_okay=False))
@click.argument('outfile', type=click.Path(dir_okay=False))
@click.option('--start-year', '-s', type=int, default=1950)
def main(infile, outfile, start_year):
  xls = pd.read_excel(infile)
  cnames = xls.iloc[1, :]
  clist = cnames.tolist()
  ccodes = pd.read_csv('/data/ssp-data/country-names.csv')
  cfips = tuple(map(lambda cc: cname_to_fips(cc, ccodes), clist))
  csel = map(lambda cc: True if (isinstance(cc, str) and len(cc) == 2) else False, cfips)
  cint_name = tuple(filter(lambda cc: (isinstance(cc, str) and len(cc) == 2), cfips))
  start_row = xls.loc[xls['GDP per capita'] == start_year, ].index.values[0]
  cinterest = xls.loc[start_row:230, csel]
  cinterest.columns = cint_name
  cinterest.index = range(start_year, 2011)
  cinterest.index.name = 'Year'
  cinterest.to_csv(outfile)


if __name__ == '__main__':
  main()
