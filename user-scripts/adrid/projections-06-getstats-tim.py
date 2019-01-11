import os
import sys
import arcpy
from arcpy import env
from arcpy.sa import *
import shutil
arcpy.CheckOutExtension("Spatial")

arcpy.env.overwriteOutput = True
# Zonal statistics for original BII

inoutdir = "C:/ds/temporal-bii/"
pressure = "tim/"
year = 2005
biiproj = inoutdir + pressure + "bii-proj-" + str(year)
outDir = inoutdir + pressure

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
