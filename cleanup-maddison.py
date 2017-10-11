#!/usr/bin/env python

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

  if not isinstance(name, (str, unicode)):
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
def main(infile, outfile):
  xls = pd.read_excel(infile)
  cnames = xls.iloc[1, :]
  clist = cnames.tolist()
  ccodes = pd.DataFrame.from_csv('../../data/ssp-data/country-names.csv')
  cfips = map(lambda cc: cname_to_fips(cc, ccodes), clist)
  csel = map(lambda cc: True if (isinstance(cc, str) and len(cc) == 2) else False, cfips)
  cint_name = filter(lambda cc: (isinstance(cc, str) and len(cc) == 2), cfips)
  cinterest = xls.loc[170:230, csel]
  cinterest.columns = cint_name
  cinterest.index = range(1950, 2011)
  cinterest.to_csv(outfile)


if __name__ == '__main__':
  main()
