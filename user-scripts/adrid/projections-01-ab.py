#!/usr/bin/env python

import time
import fiona
import multiprocessing
from rasterio.plot import show
import math
import os
import click
#import matlibplot.pyplot as plt
import numpy as np
import numpy.ma as ma
import rasterio
from rasterio.plot import show, show_hist
import pandas

from projections.rasterset import RasterSet, Raster
from projections.simpleexpr import SimpleExpr
import projections.predicts as predicts
import projections.r2py.modelr as modelr
import projections.utils as utils

# specify the model version
fldr = ['v1', 'v2', 'v3']

# Open the mask shape file
shp_file = 'c:/data/from-adriana/tropicalforests.shp'
shapes = fiona.open(shp_file)

# for each model version
for version in fldr:

    # get the model name
    mod_name = 'simplifiedAbundanceModel_' + version + '.rds'

    # Read in the model
    mod = modelr.load('C:/data/from-adriana/ModelsForProjections/' + mod_name)
    predicts.predictify(mod)

    # pull out the reference value for this model
    df = pandas.read_csv('C:/data/from-adriana/ValuesForProjections/abData.csv')
    value_name = 'reference_' + version
    ref = float(df[df['Value'] == value_name]['zeroValue'])

    # for each year
    for year in range(2001, 2013):
        
        # Import standard PREDICTS rasters
        rasters = predicts.rasterset('1km', 'version3.3', year, 'medium')

        # update the land-use classes that we need for the model
        rasters['cropland_lightintense'] = SimpleExpr('cropland_lightintense',
                                                    'cropland_light + cropland_intense')
        rasters['pasture_lightintense'] = SimpleExpr('pasture_lightintense',
                                                'pasture_light + pasture_intense')
        # read in the interpolated HPD
        rasters['hpd'] = Raster('hpd', 'C:/data/from-adriana/DataForProjections/HPD/yr%d/hdr.adf' % year)
        # extract the maximum value
        max_hpd = float(df[df['Value'] == 'LogHPDPlus1']['max'])
        # clip to the maximum value
        rasters['clip_hpd'] = SimpleExpr('clip_hpd', 'clip(hpd, 0, %f)' % max_hpd)
        # center and scale HPD (subtract mean and divide by sd)
        # we don't need to log(x+1) hpd because the data are already in this format
        mean_hpd = float(df[df['Value'] == 'LogHPDPlus1']['mean'])
        sd_hpd = float(df[df['Value'] == 'LogHPDPlus1']['sd'])
        rasters['LogHPDPlus1_cs'] = SimpleExpr('LogHPDPlus1_cs',
                                               '(clip_hpd - %f) / %f' % (mean_hpd, sd_hpd))
    
        # set studyMeanHPD as a control variable to 0 (in the transformed space, that is ~ -2)
        zero_studyHPD = float(df[df['Value'] == 'studyMeanHPD']['zeroValue'])
        rasters['studyMeanHPD_cs'] = SimpleExpr('studyMeanHPD_cs', '%f' % zero_studyHPD)
        
        # read in Road density layers
        rasters['RdDens_50km'] = Raster('RdDens_50km',
                                        'C:/data/from-adriana/DataForProjections/RdDn50km.tif')
        # cube root the layer
        rasters['Croot_RdDens_50km'] = SimpleExpr('Croot_RdDens_50km',
                                                  'pow(RdDens_50km, 1/3.)')
        # extract the maximum value
        max_rd = float(df[df['Value'] == 'CRootRdDens_50km']['max'])
        # clip to the maximum value
        rasters['clip_rd'] = SimpleExpr('clip_rd',
                                        'clip(Croot_RdDens_50km, 0, %f)' % max_rd)
        # scale and center
        mean_rd = float(df[df['Value'] == 'CRootRdDens_50km']['mean'])
        sd_rd = float(df[df['Value'] == 'CRootRdDens_50km']['sd'])
        rasters['CRootRdDens_50km_cs'] = SimpleExpr('CRootRdDens_50km_cs',
                                                    '(clip_rd - %f) / %f' % (mean_rd, sd_rd))

        # set up the rasterset, cropping by tropical forests
        # set all_touched = False as there are some boundary issues with very small countries on the edge
        # like Macao
        rs = RasterSet(rasters, shapes = shapes, crop = True, all_touched = False)
    
        # evaluate the model
        # model is square root abundance so square it

        # note that the intercept value has been calculated for the baseline land use when all other variables are held at 0
        rs[mod.output] = mod        
        rs['output'] = SimpleExpr('output', '(pow(%s, 2) / pow(%f, 2))' % (mod.output, ref))
        rs.write('output', utils.outfn('temporal-bii/' + version, 'bii-ab-%d.tif' % year))

        # if you're on the final version 1 (i.e. the last time you're going round)
        # write out the pressure data
        if version == 'v3':
            rs.write('primary', utils.outfn('temporal-bii/primary', 'primary-%d.tif' % year))
            rs.write('secondary', utils.outfn('temporal-bii/secondary', 'secondary-%d.tif' % year))
            rs.write('pasture', utils.outfn('temporal-bii/pasture', 'pasture-%d.tif' % year))
            rs.write('cropland', utils.outfn('temporal-bii/cropland', 'cropland-%d.tif' % year))
            rs.write('urban', utils.outfn('temporal-bii/urban', 'urban-%d.tif' % year))
            rs.write('clip_hpd', utils.outfn('temporal-bii/hpd', 'hpd-%d.tif' % year))



        
    





