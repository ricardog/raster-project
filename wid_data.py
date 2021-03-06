#!/usr/bin/env python3

import pdb

import pandas as pd
from pylru import lrudecorator
import seaborn as sns

BII_URL = 'http://ipbes.s3.amazonaws.com/weighted/' \
  'historical-BIIAb-npp-country-1880-2014.csv'

@lrudecorator(10)
def get_raw_bii_data():
  return pd.read_csv(BII_URL)

def findt(ss):
  rval = [None] * len(ss)
  rval[0] = True
  for i in range(1, len(ss)):
    rval[i] = not pd.isnull(ss.iloc[i]) and ss.iloc[i] != ss.iloc[i - 1]
  return pd.Series(rval)

def get_bii_data(dropna=True):
  bii = get_raw_bii_data()
  cols = list(filter(lambda nn: nn[0:6] == 'BIIAb_' or nn[0:4] == 'GDP_',
                     bii.columns))
  bii2 = bii.loc[:, ['fips', 'ar5', 'name', 'iso3', 'npp_mean'] + cols]
  if dropna:
    bii2.dropna(inplace=True)
  cols = tuple(filter(lambda col: col[0:6] == 'BIIAb_', bii2.columns))
  for col in bii2.loc[:, cols].columns:
    bii2.insert(5, col.replace('Ab_', 'Ab2_'), bii2[col].div(bii2.npp_mean))
  t7 = pd.wide_to_long(bii2, ['BIIAb', 'BIIAb2', 'GDP'], i=['name'],
                       j='Year', sep='_')
  t7.reset_index(inplace=True)
  t7 = t7.assign(year=t7.Year.astype(int))
  del t7['Year']
  return t7

def get_wid_data():
  url_temp = 'http://ipbes.s3.amazonaws.com/by-country/%s.csv'
  metrics = ('sfiinc992j', 'afiinc992t', 'afiinc992j', 'afiinc992i')
  data = dict()
  for metric in metrics:
    data[metric] = pd.read_csv(url_temp % metric, encoding='utf-8')
  return data

def get_eci_data(dropna=False):
  bii = get_raw_bii_data()
  cols = list(filter(lambda nn:  nn[0:4] == 'ECI_', bii.columns))
  bii2 = bii.loc[:, ['fips', 'ar5', 'name', 'iso3',] + cols]
  if dropna:
    bii2.dropna(inplace=True)
  t7 = pd.wide_to_long(bii2, 'ECI', i=['name'], j='Year', sep='_')
  t7.reset_index(inplace=True)
  t7 = t7.assign(year=t7.Year.astype(int))
  del t7['Year']
  return t7

def get_rol_data(dropna=False):
  bii = get_raw_bii_data()
  cols = {'WJP Rule of Law Index: Overall Score': 'ROLI',
          'Factor 1: Constraints on Government Powers': 'ROLI_1',
          'Factor 2: Absence of Corruption': 'ROLI_2',
          'Factor 3: Open Government ': 'ROLI_3',
          'Factor 4: Fundamental Rights': 'ROLI_4',
          'Factor 5: Order and Security': 'ROLI_5',
          'Factor 6: Regulatory Enforcement': 'ROLI_6',
          'Factor 7: Civil Justice': 'ROLI_7',
          'Factor 8: Criminal Justice': 'ROLI_8'
  }
  bii2 = bii.loc[:, ['fips', 'ar5', 'name', 'iso3'] + list(cols.keys())]
  if dropna:
    bii2.dropna(inplace=True)
  bii2.rename(columns=cols, inplace=True)
  return bii2
  
def get_language_data():
  url = 'http://ipbes.s3.amazonaws.com/by-country/language-distance.csv'
  return pd.read_csv(url, encoding='utf-8')

def get_area_data():
  url = 'http://ipbes.s3.amazonaws.com/by-country/wb-area.csv'
  return pd.read_csv(url, encoding='utf-8')

def area_order():
  return ('V. Small', 'Small', 'Medium', 'Large', 'V. Large')

def get_p4_data(avg=False):
  url = 'http://ipbes.s3.amazonaws.com/by-country/polityv4.csv'
  p4v = pd.read_csv(url, encoding='utf-8')
  if avg:
    df = p4v.loc[:, ['fips', 'polity', 'polity2']].groupby('fips').\
      rolling(window=5, fill_method='bfill').mean().reset_index()
    p4v['polity'] = df.polity.values
    p4v['polity2'] = df.polity2.values
  return p4v

def gov_order():
  return ('Other', 'Autocracy', 'Anocracy', 'Democracy')

def get_hpop_data():
  url = 'http://ipbes.s3.amazonaws.com/by-country/hpop.csv'
  hpop = pd.read_csv(url)
  return hpop[hpop.fips != 'Global']

def get_gdp_data():
  url = 'http://ipbes.s3.amazonaws.com/by-country/gdp-1800.csv'
  gdp= pd.read_csv(url)
  return gdp

def gdp_tresholds(df):
  bins = [0, 500, 1000, 2000, 4000, 8000, 16000, 32000]
  labels = ['0.5k', '1k', '2k', '4k', '8k', '16k', '32k']

  df['GDPq'] = pd.cut(df.GDP, right=False, bins=bins, labels=labels)
  grouped = df.sort_values(['name', 'year']).groupby('name')
  df['threshold'] = grouped['GDPq'].transform(findt)
  return df

def gdp_tresholds_plot():
  bii = gdp_tresholds(get_bii_data(False))
  biit = bii[bii.threshold == True]
  biit = biit.assign(Decade=(biit.Year / 10).astype(int) * 10)
  bii = bii.assign(Decade=(bii.Year / 10).astype(int) * 10)

  hue_order = reversed(sorted(biit.Decade.unique()))
  g = sns.catplot(x='GDPq', y='BIIAb2', data=biit, col='ar5', col_wrap=3,  hue='Decade', hue_order=hue_order,
                  #palette=sns.color_palette(n_colors=15),
                  #palette='tab20c',
                  palette=sns.color_palette("coolwarm", 15),
                  sharey=True, kind='violin', inner='point',
                  dodge=False, scale='count', cut=0)
  g.set_xlabels('Quantixed GDP per capita (log-scale)')
  g.set_ylabels('NPP-weighted Abundance-based BII (fraction)')
  for ax in g.fig.get_axes():
      set_alpha(ax, 0.8)

  hue_order = reversed(sorted(biit.Decade.unique()))
  g = sns.catplot(x='GDPq', y='BIIAb', data=biit, col='ar5', col_wrap=3,  hue='Decade', hue_order=hue_order,
                  #palette=sns.color_palette(n_colors=15),
                  #palette='tab20c',
                  palette=sns.color_palette("coolwarm", 15),
                  sharey=True, kind='violin', inner='point',
                  dodge=False, scale='count', cut=0)
  g.set_xlabels('Quantixed GDP per capita (log-scale)')
  g.set_ylabels('NPP-weighted bundance-based BII')
  for ax in g.fig.get_axes():
      set_alpha(ax, 0.8)

if __name__ == '__main__':
  pass
