#!/usr/bin/env python3

from rasterset import RasterSet
import projections.predicts as predicts
import r2py.modelr as modelr
from projutils.hpd import hyde

scenarios = ['historical',
             'ssp1_rcp2.6_image',
             'ssp5_rcp8.5_remind-magpie',
             'ssp2_rcp4.5_message-globiom',
             'ssp3_rcp7.0_aim',
             'ssp4_rcp3.4_gcam',
             'ssp4_rcp6.0_gcam']


models = ['compositionalsimilarity_model.rds', 'abundance_model_simple.rds']

ablayers = {
    'land_use_cropland_light_intense': 'cropland_light + cropland_intense',
    'land_use_cropland_minimal': 'cropland_minimal',
    'land_use_intermediate_secondary_vegetation_light_intense': 'intermediate_secondary_light + intermediate_secondary_intense',
    'land_use_intermediate_secondary_vegetation_minimal': 'intermediate_secondary_minimal',
    'land_use_mature_secondary_vegetation_light_intense': 'mature_secondary_light + mature_secondary_intense',
    'land_use_mature_secondary_vegetation_minimal': 'mature_secondary_minimal',
    'land_use_pasture_light_intense': 'pasture_light + pasture_intense',
    'land_use_pasture_minimal': 'pasture_minimal',
    'land_use_plantation_forest_light_intense': 'plantation_pri_intense + plantation_pri_light',
    'land_use_plantation_forest_minimal': 'plantation_pri_minimal',
    'land_use_primary_light_intense': 'primary_light + primary_intense',
    'land_use_urban_light_intense': 'urban_light + urban_intense',
    'land_use_urban_minimal': 'urban_minimal',
    'land_use_young_secondary_vegetation_light_intense': 'young_secondary_intense + young_secondary_light',
    'land_use_young_secondary_vegetation_minimal': 'young_secondary_minimal',
    'loghpd' : 'log(hpd + 1)'
}


for k, v in ablayers.items():
    ablayers[k] = v

cslayers = {
    'contrast_primary_minimal_cropland' : 'cropland',
    'contrast_primary_minimal_intermediate_secondary_vegetation' : 'intermediate_secondary',
    'contrast_primary_minimal_mature_secondary_vegetation' : 'mature_secondary',
    'contrast_primary_minimal_pasture' : 'pasture',
    'contrast_primary_minimal_plantation_forest' : 'plantation_pri',
    'contrast_primary_minimal_primary_vegetation' : 'primary_light + primary_intense',
    'contrast_primary_minimal_urban' : 'urban',
    'contrast_primary_minimal_young_secondary_vegetation' : 'young_secondary',
    'contrast_primary_minimal_intermediate_secondary_vegetation_light_intense': 'intermediate_secondary_light + intermediate_secondary_intense',
    'contrast_primary_minimal_intermediate_secondary_vegetation_minimal': 'intermediate_secondary_minimal',
    'contrast_primary_minimal_pasture_light_intense': 'pasture_light + pasture_intense',
    'contrast_primary_minimal_pasture_minimal': 'pasture_minimal',
    'contrast_primary_minimal_plantation_forest_light_intense': 'plantation_pri_intense + plantation_pri_light',
    'contrast_primary_minimal_plantation_forest_minimal': 'plantation_pri_minimal',
    'contrast_primary_minimal_primary_light_intense': 'primary_light + primary_intense',
    'contrast_primary_minimal_young_secondary_vegetation_light_intense': 'young_secondary_intense + young_secondary_light',
    'contrast_primary_minimal_young_secondary_vegetation_minimal': 'young_secondary_minimal',
    'log10geo' : 0,
    'gower_env_dist' : 0
}

for k, v in cslayers.items():
    cslayers[k] = v

for model in models:

    if model == 'abundance_model_simple.rds':
        what = "abundance"
    else:
        what = "comp_sim"

    # Read in the model
    mod = modelr.load(model)

    for scenario in scenarios:

        if scenario == 'historical':
            years = filter(lambda x: x >= 1970 and x < 2015, hyde.years())
        else:
            years = range(2015, 2100)

        for year in years:
            print(f'{scenario}: {year}')
            rasters = predicts.helen(scenario, year, wpp=False)

            if model == 'abundance_model_simple.rds':
                rasters.update(ablayers)
            else:
                rasters.update(cslayers)

            rs = RasterSet(rasters)

            # back transform
            rs[mod.output] = mod

            if model == 'abundance_model_simple.rds':
                rs['output'] = 'clip((pow(%s, 2) / pow(%f, 2)), 0, 1e20)' % (mod.output, mod.intercept)

            else:
                rs['output'] = 'clip((inv_logit(%s) - 0.01) / (inv_logit(%f) - 0.01), 0, 1e20)' % (mod.output, mod.intercept)

            #rs.write('output', './simple_projections/'+ what + '-' + scenario + '-' + '%d.tif' % year)
            
            data, meta = rs.eval("output", quiet=True)
            from rasterio.plot import show
            show(data)
            xxx
        
