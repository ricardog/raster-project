import os
import sys
import arcpy
from arcpy import env
from arcpy.sa import *
import shutil
arcpy.CheckOutExtension("Spatial")

arcpy.env.overwriteOutput = True

lbiiDir =  "C:/ds/temporal-bii/"

projSystem = "PROJCS['World_Behrmann',GEOGCS['GCS_WGS_1984',DATUM['D_WGS_1984',SPHEROID['WGS_1984',6378137.0,298.257223563]],PRIMEM['Greenwich',0.0],UNIT['Degree',0.0174532925199433]],PROJECTION['Behrmann'],PARAMETER['False_Easting',0.0],PARAMETER['False_Northing',0.0],PARAMETER['Central_Meridian',0.0],UNIT['Meter',1.0]]"
geogSystem = "GEOGCS['GCS_WGS_1984',DATUM['D_WGS_1984',SPHEROID['WGS_1984',6378137.0,298.257223563]],PRIMEM['Greenwich',0.0],UNIT['Degree',0.0174532925199433]]"

print("Projecting main LBII results")

#fldr = ["v1", "v2", "v3", "hpd", "primary", "secondary", "urban", "pasture", "cropland"]
fldr = ["v1", "v2", "v3", "primary", "secondary", "urban", "pasture", "cropland"]

for year in range(2001, 2013):
    print("Working on year " + str(year))
    for pressure in fldr:
        print("Working on " + pressure)

        if pressure == "v1":
            filename = "bii"
        elif pressure == "v2":
            filename = "bii"
        elif pressure == "v3":
            filename = "bii"
        else:
            filename = pressure
            
        biifile = lbiiDir + pressure + "/" + filename + "-" + str(year) + ".tif"
        print(biifile)
        bii = Raster(biifile)
        outras = lbiiDir + pressure + "/proj-" + str(year)

        #arcpy.DefineProjection_management(bii,
        #                                  geogSystem)
        arcpy.ProjectRaster_management(in_raster = bii,
                                       out_raster = outras,
                                       out_coor_system = projSystem,
                                       resampling_type = "BILINEAR",
                                       in_coor_system = geogSystem)


# project original BII
#outDir = "C:/ds/temporal-bii/tim/"
#bii = "C:/Users/adrid/projections/tim-bii/lbii.asc"
#year = 2005

#arcpy.DefineProjection_management(bii,
#                                  geogSystem)
#arcpy.ProjectRaster_management(in_raster = bii,
#                               out_raster = outDir + "bii-proj-" + str(year),
#                               out_coor_system = projSystem,
#                               resampling_type = "BILINEAR",
#                               in_coor_system = geogSystem)    

# Execute Clip
#arcpy.Clip_analysis("C:/Users/adrid/projections/7_ProjectIPBESRegions/IPBESregions.shp",
#                    "C:/data/from-adriana/tropicalforestsDisProj.shp",
#                    "C:/ds/temporal-bii/clip-polygons/IPBESregion_clip.shp")

#arcpy.Clip_analysis("C:/Users/adrid/projections/6_ProjectWorldBorders/Countries.shp",
#                    "C:/data/from-adriana/tropicalforestsDisProj.shp",
#                    "C:/ds/temporal-bii/clip-polygons/Countries_clip.shp")
