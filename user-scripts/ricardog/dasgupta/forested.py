#!/usr/bin/env python3

from collections import OrderedDict
import fiona
from shapely.geometry import shape, mapping
from shapely.ops import unary_union

TEMPERATE = ("Boreal Forests/Taiga",
              "Temperate Conifer Forests",
              "Temperate Broadleaf & Mixed Forests",
              "Mediterranean Forests, Woodlands & Scrub")

TROPICAL = ("Tropical and Subtropical Coniferous Forests",
            "Tropical and Subtropical Dry Broadleaf Forests",
            "Tropical and Subtropical Moist Broadleaf Forests",
            "Mangroves")

FORESTED = TEMPERATE + TROPICAL

def is_forested(eco):
    return eco['properties']['WWF_MHTNAM'] in FORESTED

def is_tropical(eco):
    return eco['properties']['WWF_MHTNAM'] in TROPICAL
    
def main():
    fname = '/Users/ricardog/src/eec/data/tnc_terr_ecoregions/' \
        'tnc_terr_ecoregions.shp'
    with fiona.open(fname) as src:
        meta = src.meta.copy()
        meta['schema']['properties'].update({'forest': 'bool',
                                             'nonforest': 'bool',
                                             'tropical': 'bool',
                                             'temperate': 'bool'})
        with fiona.open('forested/forested.shp', 'w', **meta) as dst:
            for eco in src:
                props = eco['properties']
                props['forest'] = is_forested(eco)
                props['nonforest'] = not is_forested(eco)
                props['tropical'] = is_tropical(eco)
                props['temperate'] = is_forested(eco) and not is_tropical(eco)
                dst.write({'geometry': eco['geometry'],
                           'properties': props})

    return

if __name__ == '__main__':
    main()

                              
