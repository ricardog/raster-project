#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import fiona
import pdb

def doit():
  name = 'ne_10m_admin_0_countries'
  with fiona.open('%s_orig/%s.shp' % (name, name), encoding='utf-8') as src:
    with fiona.open('%s/%s.shp' % (name, name), 'w', encoding='utf-8',
         driver=src.driver, crs=src.crs, schema=src.schema) as dst:
      for shp in src:
        if shp['properties']['NAME'] == 'Norway':
          print('1')
          shp['properties']['UN_A3'] = '578'
          shp['properties']['FIPS_10_'] = 'NO'
          shp['properties']['ISO_A3'] = 'NOR'
        if shp['properties']['NAME'] == 'France':
          print('2')
          shp['properties']['ISO_A3'] = 'FRA'
        if shp['properties']['NAME'] == 'S. Sudan':
          print('3')
          shp['properties']['FIPS_10_'] = 'OD'
        if shp['properties']['NAME'] == 'Åland':
          print('4')
          shp['properties']['FIPS_10_'] = 'AX'
        if shp['properties']['NAME'] == 'Israel':
          print('5')
          shp['properties']['FIPS_10_'] = 'IS'
        if shp['properties']['NAME'] == 'Palestine':
          print('6')
          shp['properties']['FIPS_10_'] = 'WE'
        dst.write(shp)

    
if __name__ == '__main__':
  os.chdir('/Users/ricardog/src/eec/data/natural-earth')
  doit()
