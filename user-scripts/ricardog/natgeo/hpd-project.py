#!/usr/bin/env python3

import os

import click
import numpy as np
import numpy.ma as ma

import rasterio
import projections.predicts as predicts
from projections.rasterset import RasterSet
from projections.simpleexpr import SimpleExpr
import projections.r2py.modelr as modelr
import projections.utils as utils


@click.group()
def cli():
    pass

@cli.command()
def luh2():
    print('Running luh2 projection')
    rset = predicts.rasterset('luh2', 'historical', 2014, 'wpp')
    rs = RasterSet(rset)
    data, meta = rs.eval('hpd')
    data = ma.masked_where(np.isnan(data), data)
    with rasterio.open(utils.outfn('luh2', 'hpd-%d.tif' % 2014),
                       'w', **meta) as dst:
        dst.write(data.filled(), indexes=1)

@cli.command()
@click.argument('what', type=click.Choice(['abundance', 'annual_minimal',
                                           'hpd']))
@click.argument('year', type=int)                
@click.option('--model-dir', '-m', type=click.Path(dir_okay=True),
              default='/out/models')
@click.option('--model', '-M', type=str,
              default='michelle/2019-12-05/Mod_GLB1sqrt.rds')
def glb_lu(what, year, model_dir, model):
    if year != 2015:
        print('Year must be 2015')
        return
    print('Initialzing GLB_LU rasterset')
    rset = predicts.rasterset('glb_lu', None, year, 'wpp')
    rs = RasterSet(rset)

    model = os.path.join(model_dir, model)
    print('Loading model %s' % model)
    mod = modelr.load(model)
    predicts.predictify(mod)
    rs[mod.output] = mod
    expr = '(%s / %f)'
    rs['abundance'] = SimpleExpr('abundance',
                                 expr % (mod.output, mod.intercept))

    print('Generating %s raster' % what)
    rs.write(what, utils.outfn('glb-lu', '%s-%d.tif' % (what, 2015)))

if __name__ == '__main__':
    cli()
