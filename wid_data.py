#!/usr/bin/env python3

import glob
import os
import pdb

import fiona
from netCDF4 import Dataset
import numpy as np
import numpy.ma as ma
import pandas as pd
from pylru import lrudecorator
import projections.utils as utils
import rasterio
import seaborn as sns

BII_URL = 'http://ipbes.s3.amazonaws.com/weighted/' \
  'historical-BIIAb-npp-country-1880-2014.csv'
HPD_URL = 'http://ipbes.s3.amazonaws.com/econ/hpd.csv'

@lrudecorator(10)
def get_raw_bii_data():
  return pd.read_csv(BII_URL)

def get_ipbes_regions():
  with fiona.open(utils.outfn('vector', 'ipbes_land_shape',
                              'ipbes_land.shp')) as shapes:
    props = tuple(filter(lambda x: x.get('type') == 'Land',
                         (s['properties'] for s in shapes)))
    return pd.DataFrame({'ID': tuple(int(s.get('OBJECTID')) for s in props),
                         'Name': tuple(s.get('IPBES_sub') for s in props)})

def sum_by(regions, data):
  mask = np.logical_or(data.mask, regions.mask)
  #regions.mask = ma.getmask(data)
  #regions_idx = regions.compressed().astype(int)
  mask_idx = np.where(mask == False)
  regions_idx = regions[mask_idx]
  summ = np.bincount(regions_idx, data[mask_idx])
  ncells = np.bincount(regions_idx)
  idx = np.where(ncells > 0)
  return idx[0], summ[idx]

@lrudecorator(10)
def cnames_df():
  cnames = pd.read_csv(os.path.join(utils.data_root(), 'ssp-data',
                                    'country-names.csv'))
  return cnames

def cid_to_x(cid, x):
  if cid == 736:
    cid = 729
  df = cnames_df()
  row = df[df.un == cid]
  if not row.empty:
    return row[x].values[0]
  return str(int(cid))

def cid_to_fips(cid):
  return cid_to_x(cid, 'fips')

def cid_to_iso3(cid):
  return cid_to_x(cid, 'iso3c')

def iso2_to_cid(iso2):
  df = cnames_df()
  row = df.un[df.iso2c == iso2.upper()]
  if row.empty or np.isnan(row).any():
    return -1
  return int(row.values[0])

def fips_to_cid(fips):
  df = cnames_df()
  row = df.un[df.fips == fips.upper()]
  if row.empty or np.isnan(row).any():
    return -1
  return int(row.values[0])

def fips_to_iso3(fips):
  return cid_to_iso3(fips_to_cid(fips))

def cid_to_name(cid):
  return cid_to_x(cid, 'country.name.en')

def iso2_to_fips(iso2):
  return cid_to_x(iso2_to_cid(iso2), 'fips')

def findt(ss):
  rval = [None] * len(ss)
  rval[0] = True
  for i in range(1, len(ss)):
    rval[i] = not pd.isnull(ss.iloc[i]) and ss.iloc[i] != ss.iloc[i - 1]
  return pd.Series(rval)

def read_hpd_rasters(years, regions=None):
  df = get_ipbes_regions()
  if regions:
    with rasterio.open(regions) as regions_ds:
      # Adjust read area so raster is the full 1440x720 resolution
      regions = regions_ds.read(1, masked=True,
                                window=regions_ds.window(*(-180, -90,
                                                           180, 90)),
                                boundless=True)
      regions = ma.masked_equal(regions, -99)
      regions = ma.masked_equal(regions, regions_ds.nodata)
  with Dataset(utils.luh2_static()) as static:
    carea = static.variables['carea'][:]
  #hpop = np.zeros((len(years), len(np.unique(regions.compressed())) + 1))
  hpop = np.zeros((len(years), 196))
  for idx, year in enumerate(years):
    with rasterio.open(utils.outfn('luh2',
                                   'historical-hpd-%d.tif' % year)) as ds:
      hpd = ds.read(1, masked=True, boundless=True,
                    window=ds.window(*(-180, -90, 180, 90)))
      hp = carea * hpd
      hpop[idx, 0] = hp.sum()
      cids, hpop[idx, 1:] = sum_by(regions, hp)
  fips = list(map(cid_to_fips, cids))
  return pd.DataFrame(hpop, index=years, columns=['Global'] + fips)

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
  url_temp = 'http://ipbes.s3.amazonaws.com/econ/%s.csv'
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
  url = 'http://ipbes.s3.amazonaws.com/econ/language-distance.csv'
  return pd.read_csv(url, encoding='utf-8')

def get_area_data():
  url = 'http://ipbes.s3.amazonaws.com/econ/wb-area.csv'
  return pd.read_csv(url, encoding='utf-8')

def area_order():
  return ('V. Small', 'Small', 'Medium', 'Large', 'V. Large')

def get_p4_data(avg=False):
  url = 'http://ipbes.s3.amazonaws.com/econ/polityv4.csv'
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
  url = 'http://ipbes.s3.amazonaws.com/econ/hpop.csv'
  hpop = pd.read_csv(url)
  return hpop[hpop.fips != 'Global']

def get_gdp_data():
  url = 'http://ipbes.s3.amazonaws.com/econ/gdp-1800.csv'
  gdp= pd.read_csv(url)
  return gdp

def read_wid_csvs():
  data = dict()
  for fname in glob.glob(os.path.join(utils.data_root(), 'wid', 'Data',
                                      'WID_*_InequalityData.csv')):
    bname = os.path.basename(fname)
    _, iso2, _ = bname.split('_', 3)
    iso2 = iso2.lower()
    df = pd.read_csv(fname, sep=';', encoding='latin1', low_memory=False)
    df.columns = df.iloc[6, :]
    data[iso2] = df
  return data

def get_var(vname, data):
  countries = tuple(filter(lambda cc: vname in data[cc].columns,
                           data.keys()))
  return dict((cc, data[cc]) for cc in countries)
  
def get_data(vname, perc, data, min_len=0):
  rdata = None
  for cc in data.keys():
    cid = iso2_to_cid(cc)
    if cid == '-1':
      continue
    fips = cid_to_fips(cid)
    iso3 = cid_to_iso3(cid)
    df = data[cc].loc[:, ['year', 'perc', vname]][data[cc].perc == perc]
    df.dropna(inplace=True)
    if len(df) > min_len:
      df['fips'] = fips
      df['iso3'] = iso3
      df['country'] = cid_to_name(iso2_to_cid(cc))
      df['variable'] = vname
      df.rename(columns={vname: perc}, inplace=True)
      df[perc] = df[perc].astype(float)
      df.year = df.year.astype(int)
      del df['perc']
      if rdata is None:
        rdata = df
      else:
        rdata = rdata.append(df, ignore_index=True)
  return rdata

def clean_wid_data():
  perc = 'p90p100'
  data = dict()
  raw_data = read_wid_csvs()
  for vname in ['sfiinc992j']:
    data[vname] = get_data(vname, perc, get_var(vname, raw_data))
  for vname in ['afiinc992i', 'afiinc992j', 'afiinc992t']:
    vdata = get_var(vname, raw_data)
    p90 = get_data(vname, perc, vdata)
    p0 = get_data(vname, 'p0p100', vdata)
    del p0['variable']
    del p0['country']
    del p0['iso3']
    vv = p90.merge(p0, how='inner', left_on=['year', 'fips'],
                   right_on=['year', 'fips'])
    vv['ratio'] = vv.p90p100 / vv.p0p100
    data[vname] = vv
  return data

def gdp_tresholds_plot():
  bins = [0, 500, 1000, 2000, 4000, 8000, 16000, 32000]
  labels = ['0.5k', '1k', '2k', '4k', '8k', '16k', '32k']

  bii = get_bii_data(False).dropna()
  bii['GDPq'] = pd.cut(bii.GDP, right=False, bins=bins, labels=labels)
  grouped = bii.sort_values(['name', 'Year']).groupby('name')
  bii['threshold'] = grouped['GDPq'].transform(findt)
  del biit
  #sns.violinplot(x='GDPq', y='BIIAb2', data=bii[bii.threshold == True], cut=0, scale='count')
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



def main():
  hpd = read_hpd_rasters(range(1950, 2011, 10),
                         utils.outfn('luh2', 'un_codes.tif'))
  hpd = hpd.T
  hpd['fips'] = hpd.index
  hpd = hpd.melt(id_vars='fips', value_vars=range(1950, 2011, 10),
                 var_name='Year', value_name='HPD')
  hpd.Year = hpd.Year.astype(int)
  hpd.to_csv('hpd.csv')
  bii = get_bii_data(False)
  merged = bii.merge(hpd, how='inner', on=['fips', 'Year']).pivot
  pdb.set_trace()

  data = clean_wid_data()
  bins = [500, 1000, 2000, 4000, 8000, 16000, 32000]
  labels = ['0.5K', '1k', '2k', '4k', '8k', '16k']

  bii['GDPq'] = pd.cut(bii.GDP, right=False, bins=bins, labels=labels)
  grouped = bii.sort_values(['name', 'Year']).groupby('name')
  bii['threshold'] = grouped['GDPq'].transform(findt)

  for vname in data:
    print(vname)
    pdb.set_trace()
    pass

if __name__ == '__main__':
  main()
