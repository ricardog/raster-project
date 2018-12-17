import os
import sys
import arcpy
from arcpy import env
from arcpy.sa import *
import shutil
arcpy.CheckOutExtension("Spatial")

arcpy.env.overwriteOutput = True

inoutdir = "C:/ds/temporal-bii/"


# Project the global shape file
projSystem = "PROJCS['World_Behrmann',GEOGCS['GCS_WGS_1984',DATUM['D_WGS_1984',SPHEROID['WGS_1984',6378137.0,298.257223563]],PRIMEM['Greenwich',0.0],UNIT['Degree',0.0174532925199433]],PROJECTION['Behrmann'],PARAMETER['False_Easting',0.0],PARAMETER['False_Northing',0.0],PARAMETER['Central_Meridian',0.0],UNIT['Meter',1.0]]"
geogSystem = "GEOGCS['GCS_WGS_1984',DATUM['D_WGS_1984',SPHEROID['WGS_1984',6378137.0,298.257223563]],PRIMEM['Greenwich',0.0],UNIT['Degree',0.0174532925199433]]"

print("Projecting shapefile")
arcpy.Project_management(in_dataset = "C:/data/from-adriana/tropicalforestsDis.shp",
                         out_dataset = "C:/data/from-adriana/tropicalforestsDisProj.shp",
                         out_coor_system = projSystem,
                         preserve_shape = "PRESERVE_SHAPE")


print("Working on years")

fldr = ["v1/", "v2/", "v3/", "primary/", "secondary/", "urban/", "pasture/", "cropland/"]


for year in range(2001, 2013):

    for pressure in fldr:
        biiproj = inoutdir + pressure + "proj-" + str(year)
        outDir = inoutdir + pressure

        if pressure == "v2/":
            print("Calculating income group statistics for year:" + str(year))
            ZonalStatisticsAsTable(in_zone_data = "C:/data/from-adriana/CountriesIncome.shp",
                                   zone_field = "IncmGrp",
                                   in_value_raster = biiproj,
                                   out_table = outDir + "IncomeGroup_" + str(year) + ".dbf",
                                   ignore_nodata = "DATA")

            ZonalStatisticsAsTable(in_zone_data = "C:/data/from-adriana/CountriesIncome.shp",
                                   zone_field = "FnlCtgr",
                                   in_value_raster = biiproj,
                                   out_table = outDir + "FinalCategory_" + str(year) + ".dbf",
                                   ignore_nodata = "DATA")

        print("Calculating global statistics for year:" + str(year))
        ZonalStatisticsAsTable(in_zone_data = "C:/data/from-adriana/tropicalforestsDisProj.shp",
                               zone_field = "Id",
                               in_value_raster = biiproj,
                               out_table = outDir + "Global_" + str(year) + ".dbf",
                               ignore_nodata = "DATA")
    
        print("Calculating region statistics for year:" + str(year))
        ZonalStatisticsAsTable(in_zone_data = "C:/Users/adrid/projections/7_ProjectIPBESRegions/IPBESregions.shp",
                               zone_field = "FIRST_IPBE",
                               in_value_raster = biiproj,
                               out_table = outDir + "IPBESregions_" + str(year) + ".dbf",
                               ignore_nodata = "DATA")

        print("Calculating subregion statistics for year:" + str(year))
        ZonalStatisticsAsTable(in_zone_data = "C:/Users/adrid/projections/7_ProjectIPBESRegions/IPBESregions.shp",
                               zone_field = "IPBES_sub",
                               in_value_raster = biiproj,
                               out_table = outDir + "IPBESSubregions_" + str(year) + ".dbf",
                               ignore_nodata = "DATA")

        print("Calculating country statistics for year:" + str(year))
        ZonalStatisticsAsTable(in_zone_data = "C:/Users/adrid/projections/6_ProjectWorldBorders/Countries.shp",
                    zone_field = "ISO3",
                    in_value_raster = biiproj,
                    out_table = outDir + "Countries_" + str(year) + ".dbf",
                    ignore_nodata = "DATA")

        ZonalStatisticsAsTable(in_zone_data = "C:/data/high_res_country_boundaries/equal_area_countries.shp",
                           zone_field = "ISO3",
                           in_value_raster = biiproj,
                           out_table = outDir + "Countries_bip_" + str(year) + ".dbf",
                           ignore_nodata = "DATA")

        print("Calculating biome statistics for year:" + str(year))
        ZonalStatisticsAsTable(in_zone_data = "C:/data/from-adriana/tropicalforestsProj.shp",
                zone_field = "WWF_MHTNAM",
                in_value_raster = biiproj,
                out_table = outDir + "Biomes_" + str(year) + ".dbf",
                ignore_nodata = "DATA")



# Zonal statistics for original BII
pressure = "tim/"
year = 2005
biiproj = inoutdir + pressure + "bii-proj-" + str(year)
outDir = inoutdir + pressure

print("Calculating global statistics for year:" + str(year))
ZonalStatisticsAsTable(in_zone_data = "C:/data/from-adriana/tropicalforestsDisProj.shp",
                       zone_field = "Id",
                       in_value_raster = biiproj,
                       out_table = outDir + "Global_" + str(year) + ".dbf",
                       ignore_nodata = "DATA")

print("Calculating region statistics for year:" + str(year))
ZonalStatisticsAsTable(in_zone_data = "C:/Users/adrid/projections/7_ProjectIPBESRegions/IPBESregions.shp",
                       zone_field = "FIRST_IPBE",
                       in_value_raster = biiproj,
                       out_table = outDir + "IPBESregions_" + str(year) + ".dbf",
                       ignore_nodata = "DATA")

print("Calculating subregion statistics for year:" + str(year))
ZonalStatisticsAsTable(in_zone_data = "C:/Users/adrid/projections/7_ProjectIPBESRegions/IPBESregions.shp",
                       zone_field = "IPBES_sub",
                       in_value_raster = biiproj,
                       out_table = outDir + "IPBESSubregions_" + str(year) + ".dbf",
                       ignore_nodata = "DATA")


print("Calculating country statistics for year:" + str(year))
ZonalStatisticsAsTable(in_zone_data = "C:/Users/adrid/projections/6_ProjectWorldBorders/Countries.shp",
                       zone_field = "ISO3",
                       in_value_raster = biiproj,
                       out_table = outDir + "Countries_" + str(year) + ".dbf",
                       ignore_nodata = "DATA")

ZonalStatisticsAsTable(in_zone_data = "C:/Users/adrid/Downloads/country_boundaries/country_boundaries/equal_area_countries.shp",
                           zone_field = "ISO3",
                           in_value_raster = biiproj,
                           out_table = outDir + "Countries_bip_" + str(year) + ".dbf",
                           ignore_nodata = "DATA")

print("Calculating biome statistics for year:" + str(year))
ZonalStatisticsAsTable(in_zone_data = "C:/data/from-adriana/tropicalforestsProj.shp",
                       zone_field = "WWF_MHTNAM",
                       in_value_raster = biiproj,
                       out_table = outDir + "Biomes_" + str(year) + ".dbf",
                       ignore_nodata = "DATA")
