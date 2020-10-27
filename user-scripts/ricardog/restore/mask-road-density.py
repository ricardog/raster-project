#!/usr/bin/env python3

import click
import rasterio

@click.command()
@click.argument('source', type=click.Path(dir_okay=False))
@click.argument('ice', type=click.Path(dir_okay=False))
@click.argument('out', type=click.Path(dir_okay=False))
def mask(source, ice, out):
    with rasterio.open(ice) as ice_ds:
        with rasterio.open(source) as src_ds:
            ice_data = ice_ds.read(1, masked=True)
            src_data = src_ds.read(1, masked=True,
                                   window=src_ds.window(*ice_ds.bounds))
            src_data.mask = ice_data.mask.copy()
            src_data.fill_value = ice_ds.nodata
            meta = ice_ds.meta.copy()
            meta.update({'driver': 'GTIFF', 'compress': 'lzw',
                         'predictpr': 3})
            import pdb; pdb.set_trace()
            with rasterio.open(out, 'w', **meta) as out_ds:
                out_ds.write(src_data.filled(), indexes=1)
    return


if __name__ == '__main__':
    mask()
