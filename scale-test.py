#!/usr/bin/env python

import rasterio
import fiona
import numpy as np
import time

import matplotlib.pyplot as plt
from rasterio.plot import show, show_hist

from projections.atlas import atlas
from rasterset import RasterSet, Raster, SimpleExpr

import projections.predicts as predicts
import projections.rds as rds

# Import standard PREDICTS rasters
rasters = predicts.rasterset("rcp", "aim", 2020, "medium")
rs = RasterSet(rasters)
rs["logHPD_rs2"] = SimpleExpr("logHPD_rs", "scale(log(hpd + 1), 0.0, 1.0)")

data1 = rs.eval("logHPD_rs")
data2 = rs.eval("logHPD_rs2")
data3 = np.where(np.isclose(data1, data2, equal_nan=True), 1, 0)
diff = np.fabs(data1 - data2)
print("max diff %f" % diff.max())

print("max in hpd_ref: %f" % rs["hpd_ref"].data.values.max())
print("max in hpd: %f" % rs["hpd"].data.dropna().values.max())

fig, ((ax1, ax2, ax3), (hx1, hx2, hx3)) = plt.subplots(2, 3, figsize=(21, 7))
show(data1, ax=ax1, cmap="Greens", title="Global max/min")
show(data2, ax=ax2, cmap="Greens", title="Computed max/min")
show(diff, ax=ax3, cmap="viridis", title="Difference", vmin=0, vmax=1.0)
show_hist(data1, ax=hx1, histtype="stepfilled")
show_hist(data2, ax=hx2, histtype="stepfilled")
show_hist(diff, ax=hx3, histtype="stepfilled")
plt.show()
