#!/usr/bin/env Rscript

library(rgdal)
source('get_rcp_grid.R')
maps <- get_rcp_grid("../data/rcp1.1/", scenario = "minicam", years = 2017)
dump_maps(maps, years = 2017)
