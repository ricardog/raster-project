#!/usr/bin/env python3

import os
import re

import matplotlib.pyplot as plt
import pandas as pd
import projections.utils as utils
import seaborn as sns
from wid_data import get_bii_data

import pdb

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

  if not isinstance(name, (str)):
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

def iso3_to_fips(iso3, df):
  def cleanup(index):
    row = df[index]['fips']
    if len(row) > 1:
      return row.values
    return row.values[0]

  if not isinstance(iso3, (str)):
    return None
  rows = df[df.iso3c == iso3.upper()]
  if rows.empty:
    return None
  return rows[fips].values[0]

def cleanup_p4v(fname, avg=True):
  bins = [-100, -10, -6, 6, 10]
  labels = ['Other', 'Autocracy', 'Anocracy', 'Democracy']
  cnames_fname = utils.data_file('ssp-data', 'country-names.csv')
  ccodes = pd.read_csv(cnames_fname)
  p4 = pd.read_excel(fname)
  p4s = p4.loc[:, ['scode', 'country', 'year', 'polity', 'polity2']]
  # Select countries we find a name match for
  cfips = map(lambda cc: cname_to_fips(cc, ccodes), p4s.country.tolist())
  csel = map(lambda cc: cc if (isinstance(cc, str) and
                               len(cc) == 2) else False, cfips)
  p4s2 = p4s.assign(fips=tuple(csel))
  p4s3 = p4s2[p4s2.fips != False]
  if avg:
    df = p4s3.loc[:, ['fips', 'polity', 'polity2']].groupby('fips').\
      rolling(window=5, fill_method='bfill').mean().reset_index()
    p4s3['polity'] = df.polity.values
    p4s3['polity2'] = df.polity2.values
  p4s3 = p4s3.assign(government=pd.cut(p4s3.polity2, right=True,
                                       bins=bins, labels=labels))
  return p4s3

def cleanup_language():
  lang = pd.read_csv(utils.data_file('policy', 'language-distance.csv'),
                     index_col=0)
  lang.drop(['USSR', 'Gran Colombia', 'Montenegro'], axis=0, inplace=True)
  lang.drop(['USSR', 'Gran Colombia', 'Montenegro'], axis=1, inplace=True)
  ccodes = pd.read_csv(utils.data_file('ssp-data', 'country-names.csv'))
  cfips = map(lambda cc: cname_to_fips(cc, ccodes), lang.index.tolist())
  csel = map(lambda cc: cc if (isinstance(cc, str) and
                               len(cc) == 2) else False, cfips)
  fips=tuple(csel)
  lang.columns = fips
  lang = lang.assign(fips=fips)
  lang.index = fips
  lang = lang.loc[lang.fips != False, lang.columns != False]
  del lang['fips']
  return lang
                   
def cleanup_wb_area(fname):
  wb_area = pd.read_csv(fname)
  wb_area = wb_area.loc[:, ['Country Name', 'Country Code', '2017']]
  wb_area['2017'] /= 1000
  wb_area.columns = ['Country Name', 'Country Code', 'WB Area']
  wb_area = wb_area.assign(area_q=pd.qcut(wb_area['WB Area'], q=5,
                                          labels=['V. Small',
                                                  'Small', 'Medium', 'Large',
                                                  'V. Large']))
  return wb_area.dropna()

def read_data():
  area = cleanup_wb_area(utils.data_file('area',
                                         'API_AG.LND.TOTL.K2_DS2_en_csv_v2_10181480.csv'))
  language = cleanup_language()
  p4v = cleanup_p4v(utils.data_file('policy', 'p4v2017.xls'), False)
  return language, p4v, area

def swarm_plot(data, labels):
  g = sns.FacetGrid(data, col='ar5', col_wrap=3, hue='area_q')
  g = g.map(sns.swarmplot, 'government', 'BIIAb_diff',
            order=labels)
  g.map(plt.axhline, y=1.0, lw=2).add_legend()
  plt.show()

if __name__ == '__main__':
  language, p4v, area = read_data()
  language.to_csv('summary-data/language-distance.csv', index=False)
  p4v.to_csv('summary-data/polityv4.csv', index=False)
  area.to_csv('summary-data/wb-area.csv', index=False)

