#!/usr/bin/env python3

import click
from netCDF4 import Dataset
import os
import rasterio

import projections.hpd as hpd
import projections.lui as lui
import projections.r2py.modelr as modelr
from projections.rasterset import RasterSet, Raster
from projections.simpleexpr import SimpleExpr
from projections.utils import data_file, outfn

import pdb

class YearRangeParamType(click.ParamType):
  name = 'year range'

  def convert(self, value, param, ctx):
    try:
      try:
        return [int(value)]
      except ValueError:
        values = value.split(':')
        if len(values) == 3:
          low, high, inc = values
        elif len(values) == 2:
          low, high = values
          inc = '1'
        else:
          raise ValueError
        return range(int(low), int(high), int(inc))
    except ValueError:
      self.fail('%s is not a valid year range' % value, param, ctx)

YEAR_RANGE = YearRangeParamType()

def get_model(what, forested, model_dir):
    if what == 'bii':
        return None
    if forested:
        if what == 'ab':
            mname = 'full_ab_f.rds'
        elif what == 'cs-ab':
            mname = 'full_cs_f.rds'
        else:
            assert False, f'unknown what {what}'
    else:
        if what == 'ab':
            mname = 'ab_nf.rds'
        elif what == 'cs-ab':
            mname = 'cs_nf.rds'
        else:
            assert False, f'unknown what {what}'
    return modelr.load(os.path.join(model_dir, mname))
    

def vivid_layer(layer):
    return ':'.join(('netcdf', data_file('vivid', 'spatial_files',
                                         'cell.land_0.5.nc'),
                     layer))

def vivid_crop_layer(layer):
    return ':'.join(('netcdf', data_file('vivid', 'spatial_files',
                                         'cell.croparea_0.5_share.nc'),
                     layer))

def rasters(ssp, year):
    rasters = {}
    rasters['icew'] = Raster('icew', outfn('rcp', 'icew.tif'))
    rasters['land'] = SimpleExpr('land', '1 - icew')
    rasters['hpd_ref'] = Raster('hpd_ref', outfn('rcp', 'gluds00ag.tif'))
    rasters['unSub'] = Raster('unSub', outfn('rcp', 'un_subregions-full.tif'))
    rasters['un_code'] = Raster('un_codes', outfn('rcp', 'un_codes-full.tif'))
    if year < 2015:
        raise IndexError(f'year must be greater than 2014 ({year})')
    else:
        hpd_dict = hpd.sps.raster(ssp, year, 'rcp')
    rasters['pop'] = hpd_dict['hpd']
    rasters['hpd'] = SimpleExpr('hpd', '(pop / carea_m2) * 1e6')
    rasters['loghpd'] = SimpleExpr('loghpd', 'log(hpd + 1)')
    rasters['hpd_diff'] = SimpleExpr('hpd_diff', '0 - loghpd')
    rasters['carea_m2'] = Raster('carea_m2', outfn('rcp', 'carea.tif'))
    rasters['carea'] = SimpleExpr('carea', 'land * (carea_m2 / 1e10)')

    rasters['tropical_mask'] = Raster('tropical_mask',
                                      outfn('rcp', 'tropical.tif'))
    rasters['temperate_mask'] = Raster('temperate_mask', 
                                       outfn('rcp', 'temperate.tif'))
    rasters['log_dist'] = 0
    rasters['log_study_max_hpd'] = 0
    rasters['log_study_mean_hpd'] = 0

    with Dataset(data_file('vivid', 'spatial_files',
                           'cell.land_0.5.nc')) as ds:
        years_avail = ds.variables['time'][:].astype(int).tolist()
        if year not in years_avail:
            raise IndexError(f'Year {year} not available in Vivid datset')
        index = years_avail.index(year)
        for layer in ds.variables:
            if len(ds.variables[layer].shape) != 3:
                continue
            rasters[f'{layer}_area'] = Raster(f'{layer}_area',
                                              vivid_layer(layer),
                                              band=index + 1)
            rasters[layer] = SimpleExpr(layer, f'{layer}_area / carea')

    # FIXME: these should come from Vivid
    rasters['age8'] = 0
    rasters['age15'] = 0
    rasters['age28'] = 0

    with Dataset(data_file('vivid', 'spatial_files',
                           'cell.croparea_0.5_share.nc')) as ds:
        years_avail = ds.variables['time'][:].astype(int).tolist()
        if year not in years_avail:
            raise IndexError(f'Year {year} not available in Vivid datset')
        index = years_avail.index(year)
        for layer in ('begr', 'betr', 'oilpalm'):
            rasters[f'{layer}_rainfed'] = Raster(f'{layer}_rainfed',
                                                 vivid_crop_layer(layer +
                                                                  '.rainfed'),
                                                 band=index + 1)
            rasters[f'{layer}_irrigated'] = Raster(f'{layer}_rainfed',
                                                   vivid_crop_layer(layer +
                                                                    '.irrigated'),
                                                   band=index + 1)
            rasters[f'{layer}'] = SimpleExpr(layer, f'{layer}_rainfed + {layer}_irrigated')
        rasters['annual_share'] = SimpleExpr(layer, 'begr + betr + oilpalm')

    # FIXME: How to compute other_notprimary
    rasters['other_primary'] = 0.00
    rasters['other_notprimary'] = SimpleExpr('other_notprimary',
                                             'other * (1 - other_primary)') 
    rasters['pasture'] = 'past'
    rasters['primary'] = SimpleExpr('primary',
                                    'other * other_primary + primforest')
    rasters['annual'] = SimpleExpr('annual', 'crop * annual_share')
    rasters['perennial'] = SimpleExpr('annual', 'crop * (1 - annual_share)')

    for lu in ('pasture', 'primary'):
        ref_path = outfn('rcp', '%s-recal.tif' % lu)
        for band, intensity in enumerate(lui.intensities()):
            n = lu + '_' + intensity
            rasters[n] = lui.RCP(lu, intensity)
            n2 = n + '_ref'
            rasters[n2] = Raster(n2, ref_path, band + 1)

    base = 'magpie_baseline_pas'
    rasters[f'{base}_urban'] = 'urban'
    rasters[f'{base}_annual'] = 'annual'
    rasters[f'{base}_perennial'] = 'perennial'
    rasters[f'{base}_secondary_forest'] = 'secdforest'
    rasters[f'{base}_primary_minimal'] = 'primary_minimal'
    rasters[f'{base}_managed_forest'] = 'forestry'
    rasters[f'{base}_other_not_primary'] = 'other_notprimary'
    rasters[f'{base}_age8'] = 'age8'
    rasters[f'{base}_age15'] = 'age15'
    rasters[f'{base}_age28'] = 'age28'

    rasters[f'{base}_primary_light_intense'] = \
        SimpleExpr('primary_light_intense',
                   'primary_light + primary_intense')
    rasters[f'{base}_pasture_minimal'] = 'pasture_minimal'
    rasters[f'{base}_pasture_light_intense'] = \
        SimpleExpr('pasture_light_intense',
                   'pasture_light + primary_intense')

    #
    # CompSim-only parameters
    #
    pre = 'magpie_pas_contrast_primary_minimal'
    rasters[f'{pre}_cropland'] = 'crop'
    rasters[f'{pre}_managed_forest'] = 'forestry'
    rasters[f'{pre}_other_not_primary'] = 'other_notprimary'
    rasters[f'{pre}_pasture_light_intense'] = f'{base}_primary_light_intense'
    rasters[f'{pre}_pasture_minimal'] = 'pasture_minimal'
    rasters[f'{pre}_primary_light_intense'] = f'{base}_pasture_light_intense'
    rasters[f'{pre}_secondary_forest'] = 'secdforest'
    rasters[f'{pre}_urban'] = 'urban'
    rasters[f'{pre}_age8'] = 'age8'
    rasters[f'{pre}_age15'] = 'age15'
    rasters[f'{pre}_age28'] = 'age28'
    
    rasters['gower_env_dist'] = 0
    rasters['s2_loghpd'] = 'loghpd'
    
    return rasters

def inv_transform(what, output, intercept):
    if what == 'ab':
        oname = 'Abundance'
        expr = SimpleExpr(oname, 'pow(%s, 2) / pow(%f, 2)' %
                          (output, intercept))
    else:
        oname = 'CompSimAb'
        expr = SimpleExpr(oname, '(inv_logit(%s) - 0.01) /'
                          '(inv_logit(%f) - 0.01)' % (output,
                                                      intercept))
    return oname, expr

def do_forested(what, ssp, year, model):
    pname = 'forested_tropic_temperate_tropical_forest'
    rs = RasterSet(rasters(ssp, year))
    rs[model.output] = model
    rs[pname] = 0
    rs['tropic_temperate_tropical_forest'] = 1
    arrays = []
    for kind in ('temperate', 'tropical'):
        if kind == 'tropical':
            intercept = model.partial({pname: 1,
                                       'tropic_temperate_tropical_forest': 1})
            rs[pname] = 1
            rs['tropic_temperate_tropical_forest'] = 1
        else:
            intercept = model.intercept

        print('%s forest intercept: %6.4f' % (kind, intercept))
        oname, expr = inv_transform(what, model.output, intercept)
        rs[oname] = expr
        rs[kind] = SimpleExpr(kind, f'{oname} * {kind}_mask')
        print(rs.tree(kind))
        data, meta = rs.eval(kind)
        arrays.append(data)
    data = arrays[0] + arrays[1]
    with rasterio.open(outfn('rcp', f'dasgupta-{oname}-f-{year}.tif'), 'w',
                       **meta) as dst:
        dst.write(data.filled(), indexes=1)
    pass

def do_non_forested(what, ssp, year, model):
    rs = RasterSet(rasters(ssp, year))
    rs[model.output] = model
    intercept = model.intercept
    print('non-forest intercept: %6.4f' % intercept)
    oname, expr = inv_transform(what, model.output, intercept)
    rs[oname] = expr
    #print(rs.tree(oname))
    data, meta = rs.eval(oname)
    with rasterio.open(outfn('rcp', f'dasgupta-{oname}-nf-{year}.tif'), 'w',
                       **meta) as dst:
        dst.write(data.filled(), indexes=1)
    return

def do_bii(year):
    pass

def do_other(vname, ssp, year):
    rs = RasterSet(rasters(ssp, year))
    pdb.set_trace()
    data, meta = rs.eval(vname)
    with rasterio.open(outfn('rcp', f'dasgupta-{vname}-{year}.tif'), 'w',
                       **meta) as dst:
        dst.write(data.filled(), indexes=1)
    return


@click.command()
@click.argument('what', type=click.Choice(('ab', 'cs-ab', 'bii', 'other')))
@click.argument('years', type=YEAR_RANGE)
@click.option('-f', '--forested', is_flag=True, default=False,
              help='Use forested models for projection')
@click.option('-m', '--model-dir', type=click.Path(file_okay=False),
              default=os.path.abspath('.'),
              help='Directory where to find the models ' +
              '(default: ./models)')
@click.option('-v', '--vname', type=str, default=None,
              help='Variable to project when specifying other.')
def project(what, years, forested, model_dir, vname):
    ssp = 'ssp2'
    if what == 'other':
        if vname is None:
            raise ValueError('Please specify a variable name')
    print(what, years, forested)

    for year in years:
        if what == 'bii':
            do_bii(year)
        elif what == 'other':
            do_other(vname, ssp, year)
        else:
            model = get_model(what, forested, model_dir)
            if not forested:
                do_non_forested(what, ssp, year, model)
            else:
                do_forested(what, ssp, year, model)
    return

if __name__ == '__main__':
    project()

