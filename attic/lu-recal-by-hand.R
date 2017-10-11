library(rgdal)
library(raster)
library(dovedale)

lu.band <- 1
model <- readRDS(paste('/vagrant/playground/out/_d5ed9724c6cb2c78b59707f69b3044e6', '/', 'primary', '.rds', sep=''))
hpd.baseline <- readGDAL('ds/luh2/gluds00ag-full.tif')
lu.baseline <- readGDAL('ds/luh2/lu-primn.tif', band=lu.band)
lui <- readGDAL('ds/luh2/primn.tif')
un.subregion <- readGDAL('ds/luh2/un_subregions-full.tif')

out <- calibrate_lu_intensity('primary', model, hpd.baseline, lu.baseline, lui, un.subregion)
out$band1[out$band1 == "Nan"] <- NA
out$band2[out$band2 == "Nan"] <- NA
out$band3[out$band3 == "Nan"] <- NA

out$band1[lu.baseline$band1 == 0] <- 0
out$band2[lu.baseline$band1 == 0] <- 0
out$band3[lu.baseline$band1 == 0] <- 0

icew <- raster('netcdf:/data/luh2_v2/staticData_quarterdeg.nc:icwtr')
srs <- projection(hpd.baseline)
projection(out) <- srs
masked <- raster::mask(stack(out), icew, maskvalue=1.0)
writeRaster(masked, 'ds/luh2/primn-recal.tif', format='GTiff', NAflag=-9999,
            overwrite=TRUE, datatype = 'FLT4S')
