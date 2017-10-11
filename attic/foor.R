
library(raster)

my.corr <- function(dirname) {
  hpd.1950 <- raster('hpd-1950.tif')
  hpd.2010 <- raster('hpd-2010.tif')
  logabund.1950 <- raster(paste(dirname, 'historical-LogAbund-1950.tif',
                                sep='/'))
  logabund.2010 <- raster(paste(dirname, 'historical-LogAbund-2010.tif',
                                sep='/'))
  primary.1950 <- crop(raster('ds/luh5/historical-primary-1950.tif'),
                       logabund.1950)
  primary.2010 <- crop(raster('ds/luh5/historical-primary-2010.tif'),
                       logabund.1950)
  secondary.1950 <- crop(raster('ds/luh5/historical-secondary-1950.tif'),
                       logabund.1950)
  secondary.2010 <- crop(raster('ds/luh5/historical-secondary-2010.tif'),
                       logabund.1950)
  all <- na.omit(as.data.frame(stack(hpd.1950, hpd.2010,
                                     logabund.1950, logabund.2010,
                                     primary.1950, primary.2010,
                                     secondary.1950, secondary.2010)))
  all$abund.1950 <- exp(all$historical.LogAbund.1950)
  all$abund.2010 <- exp(all$historical.LogAbund.2010)
  all$abund.diff <- all$abund.2010 - all$abund.1950
  all$prim.diff <- all$historical.primary.2010 - all$historical.primary.1950
  all$secd.diff <- all$historical.secondary.2010 - all$historical.secondary.1950
  return(all)
}
