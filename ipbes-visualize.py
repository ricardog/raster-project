#!/usr/bin/env python3

import io

from bokeh.io import output_file, show
from bokeh.layouts import gridplot
from bokeh.models import Range1d, ColumnDataSource, HoverTool, CrosshairTool
from bokeh.palettes import Category20
from bokeh.plotting import figure
import numpy as np
import pandas as pd
import requests

import projections.utils as utils

output_file('ipbes.html')

scenarios = utils.luh2_scenarios()
plots = []
for scenario in utils.luh2_scenarios():
    print(scenario)
    row = []
    for indicator in ('BIIAb', 'BIISR'):
        title = 'historical'
        base_url = "http://ipbes.s3.amazonaws.com/summary/%s-%s-%s- 900-2014.csv"
        syear = '900'
        eyear = '2014'
        if scenario != 'historical':
            ssp, rcp, model = scenario.upper().split('_')
            title = '%s -- %s / %s' % (indicator, ssp, rcp)
            base_url = "http://ipbes.s3.amazonaws.com/summary/%s-%s-%s-2015-2100.csv"
            syear = '2015'
            eyear = '2100'
        p = figure(title=title)
        p.y_range = Range1d(0.45, 1)
        s = requests.get(base_url % (scenario, indicator, 'subreg')).content
        df = pd.read_csv(io.StringIO(s.decode('utf-8')))
        #df = pd.read_csv('ipbes-upload/%s-%s-subreg-2015-2100.csv' % (scenario, indicator))
        subset = df.loc[:, syear:eyear].T
        subset.columns = df['Name']
        subset.reset_index(inplace=True)
        subset = subset.rename(columns={'index': 'Year'})
        mypalette=Category20[len(subset.columns)]

        for idx, col in enumerate(subset.columns):
            if col in ('Year', 'Excluded'):
                continue
            src = ColumnDataSource(data={
                'year': subset.Year,
                'data': subset[col],
                'name': [col for n in range(len(subset))]
            })
            p.line('year', 'data', source=src, line_width=4, color=mypalette[idx])
            
        s = requests.get(base_url % (scenario, indicator, 'global')).content
        df = pd.read_csv(io.StringIO(s.decode('utf-8')))
        glob = df.loc[:, syear:eyear].T.reset_index()
        src = ColumnDataSource(data={
            'year': glob['index'],
            'data': glob[0],
            'name': ['Global' for n in range(len(glob))]
        })
        p.line('year', 'data', source=src, line_width=8, color='black')
        p.add_tools(HoverTool(tooltips=[('Year', '@year'), (indicator, '@data'), ('Region', '@name')]))
        row.append(p)
    plots.append(row)
grid = gridplot(plots, sizing_mode='scale_width')
show(grid)
