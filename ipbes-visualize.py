#!/usr/bin/env python3

from math import pi
import io
import re

from bokeh.io import output_file, show, save
from bokeh.layouts import gridplot
from bokeh.models import Range1d, ColumnDataSource, HoverTool, CrosshairTool
from bokeh.models import Legend, LegendItem
from bokeh.palettes import Category20, Spectral6, brewer, viridis
from bokeh.plotting import figure
from bokeh.transform import factor_cmap

import click
import joblib
import numpy as np
import pandas as pd
import requests

import pdb

def csv2df(url, stype, syear, eyear):
    m = re.match(r'file://(.*)', url)
    if m:
        path = m.group(1)
        fd = open(path % (stype, int(syear), int(eyear)), 'r')
    else:
        addr = url % (stype, int(syear), int(eyear))
        req = requests.get(addr)
        if req.status_code != 200:
            raise RuntimeError('Request for %s failed' % addr)
        s = req.text
        fd = io.StringIO(s)
    df = pd.read_csv(fd)
    df = df[df.Name != 'Excluded']
    subset = df.loc[:, syear:eyear].T.reset_index()
    subset.columns = ['Year'] + df['Name'].values.tolist()
    return subset

def pline(p, df, column, color='black', line_width=6):
    src = ColumnDataSource(data={
        'year': df.index.values,
        'data': df[column],
        'name': [column for n in range(len(df))]
    })
    p.line('year', 'data', source=src, line_width=line_width,
           color=color)

def  stacked(df):
    '''Convert a Pandas df to a stacked structure suitable for plotting.'''
    df_top = df.cumsum(axis=1)
    df_bottom = df_top.shift(axis=1).fillna(0)[::-1]
    df_stack = pd.concat([df_bottom, df_top], ignore_index=True)
    return df_stack

@click.group(invoke_without_command=True)
@click.pass_context
def cli(ctx):
    if ctx.invoked_subcommand is None:
        click.echo('I was invoked without subcommand')
        indicators()

@cli.command()
@click.option('-m', '--merged', is_flag=True, default=False)
@click.option('-l', '--local', is_flag=True, default=False)
@click.option('--out', type=click.Path(dir_okay=False))
def indicators(merged, local, out):
    scenarios = ('historical',
                 'ssp1_rcp2.6_image',
                 'ssp2_rcp4.5_message-globiom',
                 'ssp3_rcp7.0_aim',
                 'ssp4_rcp3.4_gcam',
                 'ssp4_rcp6.0_gcam',
                 'ssp5_rcp8.5_remind-magpie')
    plots = []

    base_url = "http://ipbes.s3.amazonaws.com/weighted/" + \
               "%s-%s-%s-%%s-%%04d-%%04d.csv"
    if local:
        print('Using local summary files')
        base_url = "file://ipbes-upload/%s-%s-%s-%%s-%%04d-%%04d.csv"

    hsubset = {}
    hglob = {}
    for scenario in scenarios:
        print(scenario)
        row = []
        for indicator in ('BIIAb', 'BIISR'):
        #for indicator in ('CompSimAb',):
            title = 'historical'
            syear = '900'
            eyear = '2014'
            weight = 'npp' if indicator == 'BIIAb' else 'vsr'
            url = base_url % (scenario, indicator, weight)
            if scenario != 'historical':
                ssp, rcp, model = scenario.upper().split('_')
                title = '%s -- %s / %s' % (indicator, ssp, rcp)
                syear = '2015'
                eyear = '2100'
            subset = csv2df(url, 'subreg', syear, eyear)
            glob = csv2df(url, 'global', syear, eyear)
            if merged:
                if scenario == 'historical':
                    hsubset[indicator] = subset
                    hglob[indicator] = glob
                else:
                    subset = pd.concat([hsubset[indicator], subset],
                                                ignore_index=True)
                    glob = pd.concat([hglob[indicator], glob],
                                     ignore_index=True)
            p = figure(title=title)
            p.y_range = Range1d(0.45, 1)
            mypalette=Category20[len(subset.columns)]

            for idx, col in enumerate(subset.columns):
                if col in ('Year', 'Excluded'):
                    continue
                pline(p, subset, col, mypalette[idx], 4)
            pline(p, glob, 'Global', 'black')
            p.add_tools(HoverTool(tooltips=[('Year', '@year'),
                                            (indicator, '@data'),
                                            ('Region', '@name')]))
            row.append(p)
        plots.append(row)
    grid = gridplot(plots, sizing_mode='scale_width')
    if out:
        output_file(out)
    save(grid)
    show(grid)

@cli.command()
def landuse():
    storage = joblib.load('overtime.dat')
    historical = storage['historical']

    rows = []
    row = []
    for scenario in filter(lambda s: s != 'historical', storage.keys()):
        ssp, rcp, model = scenario.upper().split('_')
        title = '%s / %s' % (ssp, rcp)
        arr = np.hstack((historical, storage[scenario])).T
        df = pd.DataFrame(arr[:, 1:6])
        df.index = arr[:, 0]
        df.columns = ['Cropland', 'Pasture', 'Primary', 'Secondary', 'Urban']

        areas = stacked(df)
        colors = viridis(areas.shape[1])
        x2 = np.hstack((df.index[::-1], df.index))

        source = ColumnDataSource(data={
            'year' : [x2] * areas.shape[1],
            'data' : [areas[c].values for c in areas],
            'color': Category20[areas.shape[1]],
            'label': areas.columns
        })
        p = figure(x_range=(df.index[0], df.index[-1]), y_range=(0, 100),
                   title=title)
        p.grid.minor_grid_line_color = '#eeeeee'

        p.patches( xs='year', ys='data', color='color', legend='label',
                   source=source)
        #p.patches([x2] * areas.shape[1], [areas[c].values for c in areas],
        #    color=colors, alpha=0.8, line_color=None)
        #p.line(df.index, arr[:, 6], legend='Human NPP', line_width=6,
        #       color='black')
        p.add_tools(HoverTool(tooltips=[('Year', '$x{0}'),
                                        ('Percent', '$y'),
                                        ('Land use', '@label')]))
        row.append(p)
        if len(row) == 2:
            rows.append(row)
            row = []
    grid = gridplot(rows)
    show(grid)
    out = False
    if out:
        output_file(out)
    save(grid)

@cli.command()
@click.option('-l', '--local', is_flag=True, default=False)
@click.option('--out', type=click.Path(dir_okay=False))
@click.option('-s', '--subregions', is_flag=True, default=False)
def deltas(local, out, subregions):
    scenarios = ('ssp1_rcp2.6_image',
                 'ssp2_rcp4.5_message-globiom',
                 'ssp3_rcp7.0_aim',
                 'ssp4_rcp3.4_gcam',
                 'ssp4_rcp6.0_gcam',
                 'ssp5_rcp8.5_remind-magpie')
    names = []
    for s in scenarios:
        ssp, rcp = s.split('_')[0:2]
        name = '%s / %s' % (ssp, rcp)
        names.append(name)

    base_url = "http://ipbes.s3.amazonaws.com/weighted/" + \
               "%s-%s-%s-%%s-%%04d-%%04d.csv"
    if local:
        print('Using local summary files')
        if subregions:
            base_url = "file://ipbes-sub-weighted/%s-%s-%s-%%s-%%04d-%%04d.csv"
        else:
            base_url = "file://ipbes-weighted/%s-%s-%s-%%s-%%04d-%%04d.csv"

    data = None
    delta = None
    plots = []
    row = []
    syear = '2015'
    eyear = '2100'
    for indicator in ('BIIAb', 'BIISR'):
        title = 'Change in %s per IPBES %sregion' % (indicator,
                                                     'sub' if subregions
                                                     else '')
        weight = 'npp' if indicator == 'BIIAb' else 'vsr'
        for name, scenario in zip(names, scenarios):
            print(scenario, name)
            url = base_url % (scenario, indicator, weight)
            subset = csv2df(url, 'subreg', syear, eyear)
            glob = csv2df(url, 'global', syear, eyear)
            if delta is None:
                cols = ['Global'] + subset.columns[1:].values.tolist()
                delta = pd.DataFrame(columns=cols, index=names)
            delta.loc[name, cols[1]:] = \
                subset.loc[85, cols[1]:] - \
                subset.loc[0, cols[1]:]
            delta.loc[name, 'Global'] = glob.loc[85, 'Global'] - \
                                            glob.loc[0, 'Global']
            
        df2 = delta.transpose().stack().reset_index()
        df2.columns=['Subregion', 'Scenario', 'value']
        df2['Indicator']= indicator
        if data is None:
            data = df2
        else:
            data = pd.concat([data, df2])

        dlow = delta.loc[:, delta.min() < 0.0]
        dhigh = delta.loc[:, delta.max() > 0.0]
        barsl = ColumnDataSource(data=dict(regions=dlow.columns,
                                           bottom=dlow.min(),
                                           top=dlow.max().clip(upper=0.0)))
        barsh = ColumnDataSource(data=dict(regions=dhigh.columns,
                                           bottom=dhigh.min().clip(lower=0.0),
                                           top=dhigh.max()))
        points = ColumnDataSource(df2)
        plt = figure(title=None, x_range=cols, toolbar_location="above")
        plt.y_range = Range1d(delta.min().min() * 1.1,
                              delta.max().max() * 1.1)
        plt.xaxis.major_label_orientation = pi/4

        r1 = plt.vbar(x='regions', width=0.9, source=barsl, top='top',
                      bottom='bottom', fill_color="#D5E1DD",
                      line_color="black")
        r2 = plt.vbar(x='regions', width=0.9, source=barsh, top='top',
                      bottom='bottom', fill_color="#ccebc5",
                      line_color="black")
        r3 = plt.circle(x='Subregion', y='value', source=points,
                        legend='Scenario',
                        size=8,
                        fill_color=factor_cmap('Scenario',
                                               palette=Spectral6,
                                               factors=names))
        plt.add_tools(HoverTool(renderers=[r3],
                                tooltips=[('Subregion', '@Subregion'),
                                          ('BII delta', '$y'),
                                          ('Scenario', '@Scenario')]))
        plt.legend.location = 'bottom_right'
        #plt.title.text_font_size = '18pt'
        plt.xaxis.axis_label_text_font_size = '14pt'
        plt.xaxis.major_label_text_font_size = '12pt'
        plt.yaxis.axis_label_text_font_size = '14pt'
        plt.yaxis.major_label_text_font_size = '12pt'
        plt.yaxis.axis_label = 'Change in mean BII'
        plt.legend.label_text_font_size = '14pt'
        row.append(plt)

    data.to_csv('data.csv', index=False)
    grid = gridplot([row], sizing_mode='scale_width')
    show(grid)
    if out:
        output_file(out)
    save(grid)

@cli.command()
@click.option('-l', '--local', is_flag=True, default=False)
@click.option('--out', type=click.Path(dir_okay=False))
def violin(local, out):
    import seaborn as sns
    scenarios = ('ssp1_rcp2.6_image',
                 'ssp2_rcp4.5_message-globiom',
                 'ssp3_rcp7.0_aim',
                 'ssp4_rcp3.4_gcam',
                 'ssp4_rcp6.0_gcam',
                 'ssp5_rcp8.5_remind-magpie')
    names = []
    for s in scenarios:
        ssp, rcp = s.split('_')[0:2]
        name = '%s / %s' % (ssp, rcp)
        names.append(name)

    base_url = "http://ipbes.s3.amazonaws.com/summary/" + \
               "%s-%s-%s-%%s-%%04d-%%04d.csv"
    if local:
        print('Using local summary files')
        base_url = "file://ipbes-weighted/%s-%s-%s-%%s-%%04d-%%04d.csv"

    data = None
    plots = []
    row = []
    syear = '2015'
    eyear = '2100'
    for indicator in ('BIIAb', 'BIISR'):
        title = 'Change in %s per IPBES subregion' % indicator
        weight = 'npp' if indicator == 'BIIAb' else 'vsr'
        delta = None
        for name, scenario in zip(names, scenarios):
            print(scenario, name)
            url = base_url % (scenario, indicator, weight)
            subset = csv2df(url, 'subreg', syear, eyear)
            glob = csv2df(url, 'global', syear, eyear)
            if delta is None:
                cols = ['Global'] + subset.columns[1:].values.tolist()
                delta = pd.DataFrame(columns=cols, index=names)
            delta.loc[name, cols[1]:] = \
                subset.loc[85, cols[1]:] - \
                subset.loc[0, cols[1]:]
            delta.loc[name, 'Global'] = glob.loc[85, 'Global'] - \
                                            glob.loc[0, 'Global']
        delta = delta.T
        delta['Region'] = delta.index
        ldf = pd.melt(delta, value_vars=delta.columns[0:-1],
                      id_vars='Region', value_name='value',
                      var_name='Scenario')
        #ldf = pd.melt(subset, value_vars=subset.columns[1:],
        #              id_vars=subset.columns[0], value_name='value',
        #              var_name='Region')
        #ldf['Scenario'] = scenario
        ldf['Indicator'] = indicator
        if data is None:
            data = ldf
        else:
            data = pd.concat([data, ldf])
    pdb.set_trace()
    g = sns.catplot(x='Region', y='value', hue='Scenario', kind='violin',
                    data=data, col='Indicator', sharey=True,
                    bw=0.2, cut=True, scale='area', inner='point', orient='v')
    if out:
        g.savefig(out)

if __name__ == '__main__':
    cli()

