#!/usr/bin/env python3

# Insert country polygons to a POstGIS database.

from geoalchemy2 import Geography, WKTElement
import geopandas as gpd
import pandas as pd
from sqlalchemy import create_engine
import shapely
from shapely.geometry.multipolygon import MultiPolygon

# From https://github.com/geoalchemy/geoalchemy2/issues/61
from geoalchemy2.elements import _SpatialElement
from sqlalchemy.sql import expression


class GeographyElement(WKTElement):
    """
    Instances of this class wrap a WKT value.

    Usage examples::

    wkt_element = GeographyElement('POINT(4.1 52.0)') # long, lat in degrees

    """

    def __init__(self, *args, **kwargs):
        kwargs["srid"] = 4326
        _SpatialElement.__init__(self, *args, **kwargs)
        expression.Function.__init__(self, "ST_GeographyFromText", self.data)


def from_text(text, srid):
    """Convert a shape as text into a WKT.

    With the caveat that a POLYGON get converted to MULTIPOLYGON so all
    the geometries are the same type.
    """

    as_wkt = shapely.wkt.loads(text)
    if text[0:7] == "POLYGON":
        as_wkt = [as_wkt]
    # shp = geoshape.from_shape(MultiPolygon(as_wkt))
    return GeographyElement(MultiPolygon(as_wkt).wkt)


def main():
    # I don't know how to get the SRID (without using a hack) from the CRS
    # of the shapefile.
    srid = 4326
    ne_file = (
        "/data/natural-earth/ne_10m_admin_0_countries/" "ne_10m_admin_0_countries.shp"
    )
    cn_file = "/data/ssp-data/country-names.csv"
    ne = gpd.read_file(ne_file)
    cn = pd.read_csv(cn_file)
    xx = ne.merge(cn, left_on="ISO_A3", right_on="iso3c")
    xx = xx.assign(pd_area=xx.area).rename(
        columns=lambda s: s.lower() if isinstance(s, str) and s.isupper() else s
    )
    wba = pd.read_csv("/data/area/API_AG.LND.TOTL.K2_DS2_en_csv_v2_10181480.csv")
    wba = wba.loc[:, ["Country Code", "2017"]].rename(
        columns={"Country Code": "wb_api3c", "2017": "wb_area"}
    )
    xx = xx.merge(wba, on="wb_api3c", how="left")
    yy = xx.assign(geom=xx.geometry.apply(lambda x: from_text(x.wkt, srid=4326))).drop(
        "geometry", axis=1
    )

    engine = create_engine("postgresql://postgis:postgis@192.168.0.46:5432/groads")
    yy.to_sql(
        "countries",
        engine,
        if_exists="replace",
        index=False,
        dtype={"geom": Geography("MULTIPOLYGON", srid=srid)},
    )


if __name__ == "__main__":
    main()
