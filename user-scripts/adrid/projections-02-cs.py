#!/usr/bin/env python

import time
import fiona
import multiprocessing
from rasterio.plot import show
import math
import os
import pandas
import click
#import matlibplot.pyplot as plt
import numpy as np
import numpy.ma as ma
import rasterio
from rasterio.plot import show, show_hist

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
    mod_name = 'simplifiedCompositionalSimilaritymodel_' + version + '.rds'
    
    # Read in the model
    mod = modelr.load('C:/data/from-adriana/ModelsForProjections/' + mod_name)
    predicts.predictify(mod)

    # pull out the reference value for this model
    df = pandas.read_csv('C:/data/from-adriana/ValuesForProjections/csData.csv')
    value_name = 'reference_' + version
    ref = float(df[df['Value'] == value_name]['zeroValue'])

    # for each year
    for year in range(2001, 2013):
        
        # Import standard PREDICTS rasters
        rasters = predicts.rasterset('1km', 'version3.3', year, 'medium')

        # read in the interpolated HPD
        # we don't need to log(x+1) hpd because the data are already in this format
        rasters['hpd'] = Raster('hpd', 'C:/data/from-adriana/DataForProjections/HPD/yr%d/hdr.adf' % year)
        # get the maximum value
        max_hpd = float(df[df['Value'] == 'LogHPDPlus1_s2']['max'])
        # clip to the maximum value
        rasters['clip_hpd'] = SimpleExpr('clip_hpd', 'clip(hpd, 0, %f)' % max_hpd)
        # center and scale HPD (subtract mean and divide by sd)
        mean_hpd = float(df[df['Value'] == 'LogHPDPlus1_s2']['mean'])
        sd_hpd = float(df[df['Value'] == 'LogHPDPlus1_s2']['sd'])
        rasters['LogHPDPlus1_s2_cs'] = SimpleExpr('LogHPDPlus1_s2_cs',
                                                  '(clip_hpd - %f) / %f' % (mean_hpd, sd_hpd))

        # get the difference
        # diff = log(s1+1) - log(s2+1)
        # we want log(s1+1) = 0
        # so the difference is 0 - hpd
        # then center and scale (subtract mean and divide by sd)
        mean_hpddiff = float(df[df['Value'] == 'LogHPDPlus1_diff']['mean'])
        sd_hpddiff = float(df[df['Value'] == 'LogHPDPlus1_diff']['sd'])
        rasters['LogHPDPlus1_diff_cs'] = SimpleExpr('LogHPDPlus1_diff_cs',
                                                    '((0-clip_hpd) - %f)/ %f' % (mean_hpddiff, sd_hpddiff))

        # set control variables to 0 (in the transformed scale)
        zero_studymean = float(df[df['Value'] == 'LogHPDPlus1_studyMean']['zeroValue'])
        rasters['LogHPDPlus1_studyMean_cs'] = SimpleExpr('LogHPDPlus1_studyMean_cs', '%f' % zero_studymean)

        zero_dist = float(df[df['Value'] == 'distScale']['zeroValue'])
        rasters['distScale_cs'] = SimpleExpr('distScale_cs', '%f' % zero_dist)

        zero_envdist = float(df[df['Value'] == 'envdistsCRoot']['zeroValue'])
        rasters['envdistsCRoot_cs'] = SimpleExpr('envdistsCRoot_cs', '%f' % zero_envdist)

        # read in road density layers
        rasters['Rd_50km'] = Raster('RdDens_50km', 'C:/data/from-adriana/DataForProjections/RdDn50km.tif')
        rasters['Rd_1km'] = Raster('RdDens_1km', 'C:/data/from-adriana/DataForProjections/RdDn1km.tif')
        # Cube Root road density layers
        rasters['CRootDens_50km'] = SimpleExpr('CRootDens_50km', 'pow(Rd_50km, 1/3.)')
        rasters['CRootDens_1km'] = SimpleExpr('CRootDens_1km', 'pow(Rd_1km, 1/3.)')
        # find the maximum values
        max_rd50 = float(df[df['Value'] == 'CRootDens_50km_s2']['max'])
        max_rd1 = float(df[df['Value'] == 'CRootDens_1km_s2']['max'])
        # clip to the maximum value
        rasters['clip_rd50'] = SimpleExpr('clip_rd50', 'clip(CRootDens_50km, 0, %f)' % max_rd50)
        rasters['clip_rd1'] = SimpleExpr('clip_rd1', 'clip(CRootDens_1km, 0, %f)' % max_rd1)
        # Center and scale road density layers
        mean_rd50 = float(df[df['Value'] == 'CRootDens_50km_s2']['mean'])
        mean_rd1 = float(df[df['Value'] == 'CRootDens_1km_s2']['mean'])
        sd_rd50 = float(df[df['Value'] == 'CRootDens_50km_s2']['sd'])
        sd_rd1 = float(df[df['Value'] == 'CRootDens_1km_s2']['sd'])
        rasters['CRootDens_50km_s2_cs'] = SimpleExpr('CRootDens_50km_s2_cs',
                                                     '(clip_rd50 - %f) / %f' % (mean_rd50, sd_rd50))
        rasters['CRootDens_1km_s2_cs'] = SimpleExpr('CRootDens_1km_s2_cs',
                                                    '(clip_rd1 - %f) / %f' % (mean_rd1, sd_rd1))

        # get the differences
        # diff = cuberoot(s1) - cuberoot(s2)
        # we want cuberoot(s1+1) = 0
        # so the difference is 0 - cuberoot(s2)
        # then center and scale (subtract mean and divide by sd)
        mean_rd50_diff = float(df[df['Value'] == 'CRootDens_50km_diff']['mean'])
        mean_rd1_diff = float(df[df['Value'] == 'CRootDens_1km_diff']['mean'])
        sd_rd50_diff = float(df[df['Value'] == 'CRootDens_50km_diff']['sd'])
        sd_rd1_diff = float(df[df['Value'] == 'CRootDens_1km_diff']['sd'])
        rasters['CRootDens_50km_diff_cs'] = SimpleExpr('CRootDens_50km_diff_cs',
                                                       '((0 - clip_rd50) - %f) / %f' % (mean_rd50_diff, sd_rd50_diff))
        rasters['CRootDens_1km_diff_cs'] = SimpleExpr('CRootDens_1km_diff_cs',
                                                      '((0 - clip_rd1) - %f) / %f' % (mean_rd1_diff, sd_rd1_diff))

        # set up the rasterset, cropping by tropical forests
        rs = RasterSet(rasters, shapes = shapes, crop = True, all_touched = False)

        # evaluate the model
        # model is logit transformed with an adjustment, so back-transformation
        rs[mod.output] = mod
        rs['output'] = SimpleExpr('output', '(inv_logit(%s) - 0.01) / (inv_logit(%f) - 0.01)' % (mod.output, ref))
        rs.write('output', utils.outfn('temporal-bii/' + version, 'bii-cs-%d.tif' % year))



