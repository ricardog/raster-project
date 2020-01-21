
import math
import numpy as np

R_MAJOR = 6378137.0000
R_MINOR = 6356752.3142

def band_area(lats):
  rlats = np.radians(lats)
  a = R_MAJOR #6378137.0000
  b = R_MINOR #6356752.3142
  e = math.sqrt(1 - (b / a)**2)
  zm = 1 - e * np.sin(rlats)
  zp = 1 + e * np.sin(rlats)
  c = 2 * np.arctanh(e * np.sin(rlats))
  area = np.pi * b**2 * (c / (2 * e) + np.sin(rlats) / (zp*zm))
  return area

def slice_area(lats):
  area = band_area(lats)
  return np.abs(np.diff(area, 1))

def cell_area(lats, lons):
  width = lons.shape[0] - 1
  height = lats.shape[0] - 1
  slices = slice_area(lats).reshape(height, 1)
  return (np.diff(lons, 1) / 360.0).reshape(1, width) * slices

def raster_cell_area(src, full=False):
  left, bottom, right, top = src.bounds
  lats = np.linspace(top, bottom, src.height + 1)
  if full:
    lons = np.linspace(left, right, src.width + 1)
  else:
    lons = np.linspace(left, left + src.affine[0], 2)
  return cell_area(lats, lons)

    
                     
