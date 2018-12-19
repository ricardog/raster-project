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
        
        # This line imports standard PREDICTS rasters
        #rasters = predicts.rasterset('1km', 'version3.3', year, 'medium')
        # we don't need this anymore as we're importing our own data

        # so set up an empty rasters object
        rasters = dict()

        # update the land-use classes that we need for the model
        rasters['cropland_minimal'] = Raster('cropland_minimal',
                                             'C:/ds/adrid/cropland_minimal-%d.tif' % year)
        rasters['cropland_light'] = Raster('cropland_light',
                                           'C:/ds/adrid/cropland_light-%d.tif' % year)
        rasters['cropland_intense'] = Raster('cropland_intense',
                                             'C:/ds/adrid/cropland_intense-%d.tif' % year)
        rasters['cropland'] = SimpleExpr('cropland',
                                         'cropland_minimal + cropland_light + cropland_intense')


        rasters['pasture_minimal'] = Raster('pasture_minimal',
                                            'C:/ds/adrid/pasture_minimal-%d.tif' % year)
        rasters['pasture_light'] = Raster('pasture_light',
                                          'C:/ds/adrid/pasture_light-%d.tif' % year)
        rasters['pasture_intense'] = Raster('pasture_intense',
                                            'C:/ds/adrid/pasture_intense-%d.tif' % year)
        rasters['pasture'] = SimpleExpr('pasture',
                                        'pasture_minimal + pasture_light + pasture_intense')
        

        rasters['primary_minimal'] = Raster('primary_minimal',
                                            'C:/ds/adrid/primary_minimal-%d.tif' % year)
        rasters['primary_light'] = Raster('primary_light',
                                          'C:/ds/adrid/primary_light-%d.tif' % year)
        rasters['primary_intense'] = Raster('primary_intense',
                                            'C:/ds/adrid/primary_intense-%d.tif' % year)
        rasters['primary'] = SimpleExpr('primary',
                                        'primary_minimal + primary_light + primary_intense')
        

        rasters['secondary_minimal'] = Raster('secondary_minimal',
                                              'C:/ds/adrid/secondary_minimal-%d.tif' % year)
        rasters['secondary_light'] = Raster('secondary_light',
                                            'C:/ds/adrid/secondary_light-%d.tif' % year)
        rasters['secondary_intense'] = Raster('secondary_intense',
                                              'C:/ds/adrid/secondary_intense-%d.tif' % year)
        rasters['secondary'] = SimpleExpr('secondary',
                                          'secondary_minimal + secondary_light + secondary_intense')
                

        rasters['urban_minimal'] = Raster('urban_minimal',
                                          'C:/ds/adrid/urban_minimal-%d.tif' % year)
        rasters['urban_light'] = Raster('urban_light',
                                        'C:/ds/adrid/urban_light-%d.tif' % year)
        rasters['urban_intense'] = Raster('urban_intense',
                                          'C:/ds/adrid/urban_intense-%d.tif' % year)
        rasters['urban'] = SimpleExpr('urban',
                                      'urban_minimal + urban_light + urban_intense')



        rasters['cropland_lightintense'] = SimpleExpr('cropland_lightintense',
                                                    'cropland_light + cropland_intense')
        rasters['pasture_lightintense'] = SimpleExpr('pasture_lightintense',
                                                'pasture_light + pasture_intense')

        # plantation_pri is what the code takes to be plantation forest
        # we have no layers for this so make it 0
        rasters['plantation_pri'] = SimpleExpr('plantation_pri', 0)

        
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

        # if you're on the final version (i.e. the last time you're going round)
        # write out the pressure data
        if version == 'v3':
            rs.write('primary', utils.outfn('temporal-bii/primary', 'primary-%d.tif' % year))
            rs.write('secondary', utils.outfn('temporal-bii/secondary', 'secondary-%d.tif' % year))
            rs.write('pasture', utils.outfn('temporal-bii/pasture', 'pasture-%d.tif' % year))
            rs.write('cropland', utils.outfn('temporal-bii/cropland', 'cropland-%d.tif' % year))
            rs.write('urban', utils.outfn('temporal-bii/urban', 'urban-%d.tif' % year))
            rs.write('clip_hpd', utils.outfn('temporal-bii/hpd', 'hpd-%d.tif' % year))



        
    





