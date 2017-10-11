#!/usr/bin/env Rscript

##
## "Parse" command-line arguments
##
library(argparser, quietly=TRUE)
p <- arg_parser("Generate site data")
p <- add_argument(p, "--diversity", help="diversity rds file")
p <- add_argument(p, "--out", help="output rds file")
p <- add_argument(p, "--hpd", help="human population density map")
p <- add_argument(p, "--roads", help="road distance map")
p <- add_argument(p, "--merge-secondary", flag=TRUE,
                  help="Merge secondary age classes")
argv <- parse_args(p)

if (is.na(argv$diversity) || is.na(argv$hpd) || is.na(argv$roads) ||
    is.na(argv$out)) {
    print(p)
    stop()
}

##
## Load packages
##
cat("****\n* Loading packages\n")
library(yarg, quietly = TRUE)

##
## Load the data
##
cat("****\n* Preparing data\n")
diversity <- readRDS(argv$diversity)
sites.div <- SiteMetrics(diversity=diversity,
                         extra.cols=c("SSB","SSBS","Biome","Sampling_method",
                                      "Study_common_taxon","Sampling_effort",
                                      "Sampling_effort_unit","Realm"),
                         sites.are.unique=TRUE,
                         srEstimators=FALSE)

##
## Load and merge human population density data
##
cat("****\n* Getting human pressure data\n")
cat(paste("HPD data file:", argv$hpd, "\n", sep=" "))
sitesWithHPD <- read.csv(argv$hpd)
sitesWithHPD$gluds00ag[which(sitesWithHPD$gluds00ag == (-9999))] <- NA
sites.div$hpd <- sitesWithHPD$gluds00ag[match(sites.div$SSS, sitesWithHPD$SSS)]
sites.div$logHPD <- log(sites.div$hpd + 1)
sites.div$logHPD.rs <- plotrix::rescale(sites.div$logHPD, newrange = c(0,1))
cat("****\n")

##
## Load and merge road-distance data
##
cat("****\n* Getting road distance data\n")
cat(paste("Road distance data file:", argv$roads, "\n", sep=" "))
sitesWithRdDist <- read.csv(argv$roads)
sitesWithRdDist[which(sitesWithRdDist$GlobalRoa == (-9999))] <- NA
sites.div$rd.dist <- sitesWithRdDist$Global_Roa[match(sites.div$SSS, sitesWithRdDist$SSS)]
sites.div$logDistRd <- log(sites.div$rd.dist)
sites.div$logDistRd.rs <- plotrix::rescale(sites.div$logDistRd, newrange = c(0,1))
cat("****\n")

##
## Random data munging (get everything into sites.div)
##
sites.div$LogAbund <- log(sites.div$Total_abundance + 1)

##
## Re-arrange land-use data
##
sites.div$LandUse <- paste(sites.div$Predominant_habitat)
sites.div$LandUse[which(sites.div$LandUse == "Primary forest")] <- "Primary Vegetation"
sites.div$LandUse[which(sites.div$LandUse == "Primary non-forest")] <- "Primary Vegetation"
if (argv$merge_secondary) {
  sites.div$LandUse[which(sites.div$LandUse == "Secondary vegetation (indeterminate age)")] <- "Secondary Vegetation"
  sites.div$LandUse[which(sites.div$LandUse == "Young secondary vegetation")] <- "Secondary Vegetation"
  sites.div$LandUse[which(sites.div$LandUse == "Intermediate secondary vegetation")] <- "Secondary Vegetation"
  sites.div$LandUse[which(sites.div$LandUse == "Mature secondary vegetation")] <- "Secondary Vegetation"
} else {
  sites.div$LandUse[which(sites.div$LandUse == "Secondary vegetation (indeterminate age)")] <- "Young secondary vegetation"
}
sites.div$LandUse[which(sites.div$LandUse == "Secondary non-forest")] <- "Secondary Vegetation"
sites.div$LandUse[which(sites.div$LandUse == "Cannot decide")] <- NA
sites.div$LandUse <- factor(sites.div$LandUse)
sites.div$LandUse <- relevel(sites.div$LandUse, ref="Primary Vegetation")

##
## Re-arrange land-use intensity data
##
sites.div$UseIntensity <- paste(sites.div$Use_intensity)
sites.div$UseIntensity[which(sites.div$Use_intensity == "Cannot decide")] <- NA
sites.div$UseIntensity <- factor(sites.div$UseIntensity)
sites.div$UseIntensity <- relevel(sites.div$UseIntensity,ref="Minimal use")
# Merge land-use and land-use intensity into UI
sites.div$UI <- paste(sites.div$LandUse, sites.div$UseIntensity)
sites.div$UI[grep("NA", sites.div$UI)] <- NA

## FIXME: This seems odd
sites.div$UI[which(sites.div$UI == "Young secondary vegetation Intense use")] <- "Young secondary vegetation Light use"
sites.div$UI[which(sites.div$UI == "Intermediate secondary vegetation Intense use")] <- "Intermediate secondary vegetation Light use"
sites.div$UI[which(sites.div$UI == "Mature secondary vegetation Intense use")] <- "Mature secondary vegetation Light use"
sites.div$UI[which(sites.div$UI == "Secondary Vegetation Intense use")] <- "Secondary Vegetation Light use"
sites.div$UI[which(sites.div$UI == "Urban Light use")] <- "Urban Minimal use"
# Relevel UI factor
sites.div$UI <- factor(sites.div$UI)
sites.div$UI <- relevel(sites.div$UI, ref="Primary Vegetation Minimal use")

##
## Save all the data into a Rd file
##
saveRDS(sites.div, file = argv$out)
