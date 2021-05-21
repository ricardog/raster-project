#!/usr/bin/env python

import argparse

from rasterset import RasterSet, Raster, SimpleExpr
import projections.utils as utils

parser = argparse.ArgumentParser(description="bii.py -- BII projections")
parser.add_argument('--mainland', '-m', dest='mainland', default=False,
                    action='store_true',
                    help='Project using mainland coefficients '
                    '(default: islands)')
parser.add_argument('--clip', '-c', dest='clip', default=False,
                    action='store_true',
                    help='Clip predictor variables to max value seen '
                    'during model fitting')
args = parser.parse_args()

if args.mainland:
  suffix = 'mainland'
  ab_max = 1.655183
  sr_max = 1.636021
else:
  suffix = 'islands'
  ab_max = 1.443549
  sr_max = 1.413479

folder = 'clip' if args.clip else 'no-clip'

# pull in all the rasters for computing bii
bii_rs = RasterSet({'abundance': Raster('abundance',
                                        utils.outfn('katia',
                                                    folder,
                                                    'ab-%s.tif' % suffix)),
                    'comp_sim': Raster('comp_sim',
                                       utils.outfn('katia',
                                                   'ab-cs-%s.tif' % suffix)),
                    'clip_ab': 'clip(abundance, 0, %f)' % ab_max,
                    'bii_ab': 'abundance * comp_sim',
                    'bii_ab2': 'clip_ab * comp_sim'})

# write out bii raster
bii_rs.write('bii_ab' if args.clip else 'bii_ab2',
             utils.outfn('katia', folder,
                         'abundance-based-bii-%s.tif' % suffix))

# do the same for species richness
# pull in all the rasters for computing bii
bii_rs = RasterSet({'sp_rich': Raster('sp_rich',
                                      utils.outfn('katia',
                                                  folder,
                                                  'sr-%s.tif' % suffix)),
                    'comp_sim': Raster('comp_sim',
                                       utils.outfn('katia',
                                                   'sr-cs-%s.tif' % suffix)),
                    'clip_sr': 'clip(sp_rich, 0, %f)' % sr_max,
                    'bii_sr': 'sp_rich * comp_sim',
                    'bii_sr2': 'clip_sr * comp_sim'})

# write out bii raster
bii_rs.write('bii_sr' if args.clip else 'bii_sr2',
             utils.outfn('katia', folder,
                         'speciesrichness-based-bii-%s.tif' % suffix))
