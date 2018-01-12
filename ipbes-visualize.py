#!/usr/bin/env python3

import io

from bokeh.io import output_file, show
from bokeh.layouts import gridplot
from bokeh.models import Range1d, ColumnDataSource, HoverTool, CrosshairTool
from bokeh.palettes import Category20
from bokeh.plotting import figure
import pandas as pd
import requests

import pdb

def csv2df(url, stype, syear, eyear):
    s = requests.get(url % (stype, int(syear), int(eyear))).content
    df = pd.read_csv(io.StringIO(s.decode('utf-8')))
    subset = df.loc[:, syear:eyear].T.reset_index()
    subset.columns = ['Year'] + df['Name'].values.tolist()
    return subset

def pline(p, df, column, color='black', line_width=6):
    src = ColumnDataSource(data={
        'year': df.Year,
        'data': df[column],
        'name': [column for n in range(len(df))]
    })
    p.line('year', 'data', source=src, line_width=line_width,
           color=color)
    
scenarios = ('historical',
             'ssp1_rcp2.6_image',
             'ssp3_rcp7.0_aim',
             'ssp4_rcp3.4_gcam',
             'ssp4_rcp6.0_gcam',
             'ssp5_rcp8.5_remind-magpie')
plots = []

for scenario in scenarios:
    print(scenario)
    row = []
    for indicator in ('BIIAb', 'BIISR'):
        title = 'historical'
        syear = '900'
        eyear = '2014'
        base_url = "http://ipbes.s3.amazonaws.com/summary/" + \
                   "%s-%s-%%s-%%4d-%%4d.csv" % (scenario, indicator)
        if scenario != 'historical':
            ssp, rcp, model = scenario.upper().split('_')
            title = '%s -- %s / %s' % (indicator, ssp, rcp)
            syear = '2015'
            eyear = '2100'
        p = figure(title=title)
        p.y_range = Range1d(0.45, 1)
        subset = csv2df(base_url, 'subreg', syear, eyear)
        mypalette=Category20[len(subset.columns)]

        for idx, col in enumerate(subset.columns):
            if col in ('Year', 'Excluded'):
                continue
            pline(p, subset, col, mypalette[idx], 4)

        glob = csv2df(base_url, 'global', syear, eyear)
        pline(p, glob, 'Global', 'black')

        p.add_tools(HoverTool(tooltips=[('Year', '@year'),
                                        (indicator, '@data'),
                                        ('Region', '@name')]))
        row.append(p)
    plots.append(row)
grid = gridplot(plots, sizing_mode='scale_width')
show(grid)
