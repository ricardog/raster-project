#!/usr/bin/env Rscript

library(yarg)
args <- commandArgs(trailingOnly = TRUE)
dbfile <- args[1]
diversity <- readRDS(dbfile)
sites.div<-SiteMetrics(diversity=diversity,
                       extra.cols=c("SSB","SSBS","Biome","Sampling_method",
                                    "Study_common_taxon","Sampling_effort",
                                    "Sampling_effort_unit","Realm"),
                       sites.are.unique=TRUE,
                       srEstimators=FALSE)

sites <- unique(sites.div[,c('SSS','Longitude','Latitude')])
write.csv(sites,row.names=FALSE, file = args[2])

