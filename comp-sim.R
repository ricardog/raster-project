prepCompSimData <- function(data, metric="Sor") {
  ## Take subsets of the data depending on the selected metric (records
  ## of abundance only for abundance-weighted Sorensen, and records
  ## recorded as number of individuals for corrected Sorensen)
  if (metric == "SorAbd" | metric == "JaccAbdAsymm" | metric == "BC"){
    data <- data[data$Diversity_metric_type == "Abundance", ]
  } else if (metric == "SorCorr"){
    data <- data[((data$Diversity_metric == "Abundance") &
                  (data$Diversity_metric_unit == "individuals")), ]
  } else if (metric == "SorWeight"){
    data <- data[(!is.na(data[, weights])), ]
  }

  ## Define LandUse column (this is the mapping that corresponds to the
  ## lu.allsec if in roquefort.CompositionalSimilarityData.
  data$LandUse <- paste(data$Predominant_habitat)
  data$LandUse[which(data$LandUse == "Primary forest")] <- "Primary Vegetation"
  data$LandUse[which(data$LandUse == "Primary non-forest")] <- "Primary Vegetation"
  data$LandUse[which(data$LandUse == "Secondary vegetation (indeterminate age)")] <- "Secondary Vegetation"
  data$LandUse[which(data$LandUse == "Secondary non-forest")] <- "Secondary Vegetation"
  data$LandUse[which(data$LandUse == "Young secondary vegetation")] <- "Secondary Vegetation"
  data$LandUse[which(data$LandUse == "Intermediate secondary vegetation")] <- "Secondary Vegetation"
  data$LandUse[which(data$LandUse == "Mature secondary vegetation")] <- "Secondary Vegetation"
  data$LandUse[which(data$LandUse == "Cannot decide")] <- NA
  data$LandUse <- factor(data$LandUse)
  data$LandUse <- relevel(data$LandUse, ref="Primary Vegetation")

  ## Create list to store counts of sites in different land uses
  count.lus <- as.list(rep(0, length(na.omit(unique(data$LandUse)))))
  names(count.lus) <- na.omit(unique(data$LandUse))

  # Subset the data to just the required columns and remove NAs
  data <- subset(data,select=c("SS", "SSBS", "Measurement",
                               "Taxon_name_entered", "LandUse",
                               "Longitude", "Latitude"))
  data <- na.omit(data)

  # If the selected metric is corrected Sorensen, only use studies where all
  # measurements are integers
  if (metric == "SorCorr"){
    study.all.int.meas <- tapply(data$Measurement, data$SS,
                                 function(m) all(floor(m) == m))
    int.meas <- study.all.int.meas[match(data$SS, names(study.all.int.meas))]
    data <- data[int.meas, ]
  }
  return(droplevels(data))
}

## Prepare a number of variables that are used in compositional
## similarity.
prepVarsForCompSim <- function(nIters=100) {
  ## Get a list of unique land uses
  all.lu <- unique(paste(data$LandUse))

  ## Make matrices to store the final results, temporary sums and counts
  all.results <- matrix(nrow=length(all.lu), ncol=length(all.lu))
  sum.matrix <- matrix(0,nrow=length(all.lu), ncol=length(all.lu))
  count.matrix <- matrix(0,nrow=length(all.lu), ncol=length(all.lu))

  ## Convert the final results matrix to a data frame and name rows and
  ## columns
  all.results <- data.frame(all.results)
  names(all.results) <- all.lu
  row.names(all.results) <- all.lu

  ## Crate integers to count studies and used studies
  all.studies.count <- 0
  used.studies.n <- 0

  ## Create character vector to store list of used studies
  used.studies <- character(0)

  ## Make a list to store all final compositional similarity data in
  all.data <- vector("list", nIters)
  return(list(all.lu, all.results, sum.matrix, count.matrix, all.data))
}

###
### Compositional Similarity Functions
###
### Set of 8 functions for computing compositional similarity
###
compSorensenSimHACK <- function(data, s1, s2) {
  u <- length(union(s1, s2))
  i <- length(intersect(s1, s2))
  return(2 * i / (2 * i + u - i))
}

compSorensenSim <- function(data, s1, s2, adjust=FALSE) {
  u <- length(union(data$Taxon_name_entered[data$SSBS == s1],
                    data$Taxon_name_entered[data$SSBS == s2]))
  i <- length(intersect(data$Taxon_name_entered[data$SSBS == s1],
                        data$Taxon_name_entered[data$SSBS == s2]))
  sor <- 2 * i / (2 * i + u - i)

  if (!adjust) {
    return(sor)
  }
  div.sub <- droplevels(data[(data$SSBS == s1 | data$SSBS == s2), ])
  sp.rich <- tapply(div.sub$Taxon_name_entered, div.sub$SSBS,
                    function(x) return(length(unique(x))))
  max.spp <- max(sp.rich)
  min.spp <- min(sp.rich)
  spp.ratio <- min.spp / max.spp
  sorMax <- 2 * spp.ratio / (2 * spp.ratio + 1 - spp.ratio)
  return(sor / sorMax)
}

compSorensenWeightedSim <- function(data, s1, s2, weights) {
  a.spp <- intersect(data$Taxon_name_entered[data$SSBS == s1],
                     data$Taxon_name_entered[data$SSBS == s2])
  b.spp <- setdiff(data$Taxon_name_entered[data$SSBS == s1],
                   data$Taxon_name_entered[data$SSBS == s2])
  c.spp <- setdiff(data$Taxon_name_entered[data$SSBS == s2],
                   data$Taxon_name_entered[data$SSBS == s1])

  a <- sum(data[, weights][match(a.spp, data$Taxon_name_entered)])
  b <- sum(data[, weights][match(b.spp, data$Taxon_name_entered)])
  c <- sum(data[, weights][match(c.spp, data$Taxon_name_entered)])
  retrun(2 * a) / (2 * a + b + c)
}

compSorensenAbundanceSim <- function(data, s1, s2) {
  s1.sum <- sum(data$Measurement[(data$SSBS == s1)])
  s2.sum <- sum(data$Measurement[(data$SSBS == s2)])
  inter <- intersect(data$Taxon_name_entered[data$SSBS == s1],
                     data$Taxon_name_entered[data$SSBS == s2])
  u <- sum(data$Measurement[(data$SSBS == s1) &
                            (data$Taxon_name_entered %in% inter)] / s1.sum)
  v <- sum(data$Measurement[(data$SSBS == s2) &
                            (data$Taxon_name_entered %in% inter)] / s2.sum)
  sor <- (2 * u * v) / (u + v)
}

compSimpsonSim <- function(data, s1, s2) {
  a <- length(union(data$Taxon_name_entered[data$SSBS == s1],
                    data$Taxon_name_entered[data$SSBS == s2]))
  b <- length(which(!(data$Taxon_name_entered[data$SSBS == s1] %in%
                      data$Taxon_name_entered[data$SSBS == s2])))
  c <- length(which(!(data$Taxon_name_entered[data$SSBS == s2] %in%
                      data$Taxon_name_entered[data$SSBS == s1])))
  return(min(b, c) / (min(b, c) + a))
}

compBCSim <- function(data, s1, s2) {
  if (!all(data$Taxon_name_entered[(data$SSBS == s1)] ==
           data$Taxon_name_entered[(data$SSBS == s2)])) {
    stop("Taxon names don't match")
  }
  bc <- 1 - ((sum(abs(data$Measurement[(data$SSBS == s1)] -
                       data$Measurement[(data$SSBS == s2)]))) /
              (sum(data$Measurement[(data$SSBS == s1)]) +
               sum(data$Measurement[(data$SSBS == s2)])))
  return(bc)
}

compSorensenCoefSim <- function(data, s1, s2) {
  n <- sum(data$Measurement[data$SSBS == s1])
  m <- sum(data$Measurement[data$SSBS == s2])
  if (!(n > 0 & m > 0)) {
    return(0)
  }
  uni <- union(data$Taxon_name_entered[data$SSBS == s1],
               data$Taxon_name_entered[data$SSBS == s2])
  xsel <- match(uni, data$Taxon_name_entered[data$SSBS == s1])
  ysel <- match(uni, data$Taxon_name_entered[data$SSBS == s2])

  xi <- data$Measurement[data$SSBS == s1][(xsel)]
  yi <- data$Measurement[data$SSBS == s2][(ysel)]

  xi[is.na(xi)] <- 0
  yi[is.na(yi)] <- 0

  fq1 <- length(which((xi == 1) & (yi > 0)))
  fq2 <- max(1, length(which((xi == 2) & (yi > 0))))
  fp1 <- length(which((xi > 0) & (yi == 1)))
  fp2 <- max(1, length(which((xi > 0) & (yi == 2))))

  p1 <- sum(xi[yi > 0] / n)
  p2 <- ((m - 1) / m) * (fp1 / (2 * fp2))
  p3 <- sum(xi[yi == 1] / n)

  u <- min(1, p1 + p2 * p3)

  q1 <- sum(yi[xi > 0] / m)
  q2 <- ((n - 1) / n) * (fq1 / (2 * fq2))
  q3 <- sum(yi[xi == 1] / m)

  v <- min(1, q1 + q2 * q3)

  if (!(u > 0 & v > 0)) {
    return(0)
  }
  return(2 * u * v / (u + v))
}

compJaccardSim <- function(data, s1, s2) {
  s1.sum <- sum(data$Measurement[(data$SSBS == s1)])
  s2.sum <- sum(data$Measurement[(data$SSBS == s2)])
  inter <- intersect(data$Taxon_name_entered[data$SSBS == s1],
                     data$Taxon_name_entered[data$SSBS == s2])
  u <- sum(data$Measurement[(data$SSBS == s1) &
                            (data$Taxon_name_entered %in% inter)] / s1.sum)
  v <- sum(data$Measurement[(data$SSBS == s2) &
                            (data$Taxon_name_entered %in% inter)] / s2.sum)
  return((u * v) / u)
}

compSimStudy <- function(data, ss, f=compSorensenSimHACK, parallel=-1, nump=4) {
  compute <- function(start, end, nsites, sites, data, taxons) {
    res <- matrix(nrow=end - start + 1, ncol=nsites)
    for (i in start:end) {
      rindex <- i - start + 1
      for (j in (i + 1):nsites) {
        res[rindex, j] <- f(data, taxons[[paste(sites[i])]],
                            taxons[[paste(sites[j])]])
      }
    }
    return(res)
  }
  
  sites <- unique(data$SSBS)
  nsites <- length(sites)
  if (nsites < 2) {
    cat("not enough sites in the study")
    return(NULL)
  }
  taxons = new.env()
  for (site in sites) {
    taxons[[site]] <- data$Taxon_name_entered[data$SSBS == site]
  }
  cat(paste(ss, ": ", nsites, "x", nsites, "\n", sep=""))
  if (parallel > 0 & nsites > parallel) {
    incr <- floor(nsites / nump)
    starts <- seq(1, nsites - 1, incr)
    all <- foreach (start = starts, .combine=rbind) %dopar% {
      end <- min(start + incr - 1, nsites - 1)
      cat(paste("worker ", start, ":", end, "\n", paste=""))
      compute(start, end, nsites, sites, data, taxons)
    }
  } else {
    all <- compute(1, nsites - 1, nsites, sites, data, taxons)
  }
  return(all)
}

library(foreach)
library(doParallel)
registerDoParallel()

compSim <- function(data, f=compSorensenSimHACK) {
  studies <- unique(data$SS)
  res <- foreach (study = studies[1:10]) %dopar% {
    compSimStudy(data[data$SS == study, ], study, f)
  }
  return(res)
}
