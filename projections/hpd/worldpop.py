
from pathlib import Path
from pylru import lrudecorator

from ..rasterset import Raster
from ..utils import data_file, outfn


class WorldPop(object):
  def __init__(self, year):
    self._year = year
    return

  @property
  def year(self):
    return self._year

  @property
  def syms(self):
    return ['worldpop', 'carea_m2']

  def eval(self, df):
    return df['worldpop'] / (df['carea_m2'] / 1e6)

@lrudecorator(10)
def years():
  rasters = [p for p in Path(data_file('worldpop')).iterdir()
             if p.match('worldpop-*.tif')]
  return sorted(int(p.stem.rsplit('-')[-1]) for p in rasters)

def raster(year):
  rasters = {}
  if year not in years():
    raise RuntimeError(f'year {year} not available in WorldPop projection')
  rasters['carea_m2'] = Raster('carea_m2', outfn('1km', 'carea_m2.tif'))
  rasters['worldpop'] = Raster('worldpop', data_file('worldpop',
                                                     f'worldpop-{year}.tif'))
  rasters['hpd'] = WorldPop(year)
  return rasters
