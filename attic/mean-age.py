#!/usr/bin/env python

from copy import copy
import matplotlib
import netCDF4
import numpy

matplotlib.use("Agg")
import matplotlib.animation as animation
import matplotlib.colors as colors
import matplotlib.pyplot as plt

FFMpegWriter = animation.writers['ffmpeg']
metadata = dict(title='Secondary Mean Age', artist='LUH2 v2h',
                comment='LUH2 v2h (historical)')
palette = copy(plt.cm.viridis)
palette.set_over('r', 1.0)
palette.set_under('g', 1.0)
palette.set_bad('k', 1.0)

fname = '../../data/luh2_v2/historical/states.nc'
vname = 'secma'
nc_ds = netCDF4.Dataset(fname)
years = nc_ds.variables['time'][:]
if years[0] < 850:
  years = [y + 850 for y in years]
#pdb.set_trace()
writer = FFMpegWriter(fps=10, metadata=metadata)
fig = plt.figure(figsize=(8, 4))
ax1 = plt.axes(frameon=False)
ax1.axes.get_yaxis().set_visible(False)
ax1.axes.get_xaxis().set_visible(False)
plt.tight_layout()
plt.subplots_adjust(left=0.0, right=1.0, top=1.0, bottom=0.0)
for spine in ax1.spines.itervalues():
  spine.set_visible(False)
img = plt.imshow(nc_ds.variables[vname][0], cmap=palette,
                 norm=colors.Normalize(vmin=0.0, vmax=600))
text = plt.text(0.5, 0.1, '', ha = 'center', va = 'center',
                color='y', fontsize=24, transform = ax1.transAxes)
with writer.saving(fig, "writer_test.mp4", 180):
  for i in xrange(len(years)):
    print years[i]
    data = nc_ds.variables[vname][i]
    img.set_array(data)
    text.set_text(str(int(years[i])))
    writer.grab_frame()
