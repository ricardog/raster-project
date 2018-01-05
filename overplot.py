#!/usr/bin/env python3

import matplotlib.pyplot as plt
import joblib
import numpy as np
import pandas as pd

import pdb

storage = joblib.load('overtime.dat')
historical = storage['historical'].T
del storage['historical']

fig, axes = plt.subplots(2, 3)
all_axes = [ax for sublist in axes for ax in sublist]

add_legend = True
for scene in sorted(storage.keys()):
    arr = np.vstack((historical, storage[scene].T))
    years, crop, past, prim, secd, urbn, human  = tuple(map(lambda v: v.reshape(v.shape[0], ), np.hsplit(arr, arr.shape[1])))
    ax = all_axes.pop(0)
    ax.stackplot(years, (crop, past, prim, secd, urbn),
                 labels=['Cropland', 'Pasture', 'Primary', 'Secondary', 'Urban'])
    ax.plot(years, human, 'k-', linewidth=3, label='Human NPP')
    ax.set_ylabel('Fraction of land surface (%)')
    ax.set_xlabel('Year')
    ax.set_title(scene)
    ax.grid('on')
    if add_legend:
        ax.legend(loc='center left')
        add_legend = False

for ax in all_axes:
    fig.delaxes(ax)
plt.show()
    
