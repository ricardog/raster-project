#!/usr/bin/env python3

import geopandas as gpd
import pandas as pd
from sqlalchemy import create_engine


def read_sites(fname):
    df = pd.read_csv(fname, dtype={'Longitude': float, "Latitude": float},
                     index_col=0)
    gdf = gpd.GeoDataFrame(df, geometry=gpd.points_from_xy(df.Longitude,
                                                           df.Latitude))
    del gdf["Longitude"]
    del gdf["Latitude"]
    gdf.columns = ["sample_midpoint", "land_use","predominant_land_use",
                   "geometry"]
    return gdf


def insert():
    fname = "sites.csv"
    engine = create_engine("postgresql://postgis:postgis@192.168.178.21:5432/grip4")
    df = read_sites(fname)
    df.to_postgis("sites", engine, if_exists="replace", index=True,
              index_label="id")
    return


if __name__ == '__main__':
    insert()

