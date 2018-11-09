
library(arm)
hpd.resp <- function(dirname, link.fun='e', seMultiplier=1.96) {
  aModel <- readRDS(paste(dirname, 'ab-model.rds', sep='/'))
  model.data <- readRDS(paste(dirname, 'ab-model-data.rds', sep='/'))
  aug <- augment(aModel, model.data)
  mm <- model.matrix(terms(aModel), model.data)
  pvar1 <- diag(mm %*% base::tcrossprod(as.matrix(vcov(aModel)), mm))
  aug$se <- sqrt(pvar1)
  ##aug$se <- mm %*% se.fixef(aModel)
  err <- seMultiplier * aug$se
  
  if (link.fun == "e") {
    aug$ymax <- exp(aug$.fixed + err)
    aug$ymin <- exp(aug$.fixed - err)
    aug$y <- exp(aug$.fixed)
  } else if (link.fun == "10") {
    aug$ymax <- 10 ^ (aug$.fixed + err)
    aug$ymin <- 10 ^ (aug$.fixed - err)
    aug$y <- 10 ^ aug$.fitted
  } else if (link.fun == "n") {
    aug$ymax <- aug$.fixed + err
    aug$ymin <- aug$.fixed - err
    aug$y <-aug$.fixed
  } else if (link.fun == "b") {
    aug$ymax <- 1 / (1 + exp(0 - (aug$.fixed + err)))
    aug$ymin <- 1 / (1 + exp(0 - (aug$.fixed - err)))
    aug$y <- 1 / (1 + exp(0 - aug$.fixed))
  } else {
    stop(paste("Error: unknow link function:", link.fun))
  }

  land.use <- levels(aug$LandUse)
  land.use <- gsub(' [Vv]egetation', '', land.use)
  land.use <- gsub(' secondary', ' S', land.use)
  land.use <- gsub('Intermediate', 'Interm', land.use)
  land.use <- gsub(' forest', '', land.use)
  aug$land.use <- factor(aug$LandUse, labels = land.use)

  p1 <- ggplot(aug, aes(logHPD.rs, y)) +
    geom_point(aes(color=UseIntensity, fill=UseIntensity), shape=10) +
    geom_ribbon(aes(ymin=ymin, ymax=ymax, fill=UseIntensity), alpha=0.2) +
    facet_grid(. ~ land.use) + ylab("log(abundance)") +
    scale_x_continuous(name="Human Population Density (log)",
                       limits=c(0, 1), breaks=c(0.0, 0.5, 1.0))
  return(p1)
}

hpd.resp2 <- function(mod, data, link.fun='e', seMultiplier=1.96) {
  aModel <- mod
  model.data <- data
  aug <- augment(aModel, model.data)
  mm <- model.matrix(terms(aModel), model.data)
  pvar1 <- diag(mm %*% base::tcrossprod(as.matrix(vcov(aModel)), mm))
  aug$se <- sqrt(pvar1)
  ##aug$se <- mm %*% se.fixef(aModel)
  err <- seMultiplier * aug$se
  
  if (link.fun == "e") {
    aug$ymax <- exp(aug$.fixed + err)
    aug$ymin <- exp(aug$.fixed - err)
    aug$y <- exp(aug$.fixed)
  } else if (link.fun == "10") {
    aug$ymax <- 10 ^ (aug$.fixed + err)
    aug$ymin <- 10 ^ (aug$.fixed - err)
    aug$y <- 10 ^ aug$.fitted
  } else if (link.fun == "n") {
    aug$ymax <- aug$.fixed + err
    aug$ymin <- aug$.fixed - err
    aug$y <-aug$.fixed
  } else if (link.fun == "b") {
    aug$ymax <- 1 / (1 + exp(0 - (aug$.fixed + err)))
    aug$ymin <- 1 / (1 + exp(0 - (aug$.fixed - err)))
    aug$y <- 1 / (1 + exp(0 - aug$.fixed))
  } else {
    stop(paste("Error: unknow link function:", link.fun))
  }

  land.use <- levels(aug$LandUse)
  land.use <- gsub(' [Vv]egetation', '', land.use)
  land.use <- gsub(' secondary', ' S', land.use)
  land.use <- gsub('Intermediate', 'Interm', land.use)
  land.use <- gsub(' forest', '', land.use)
  use.intensity <- aug$UI
  use.intensity <- gsub('Primary vegetation ', '', use.intensity)
  use.intensity <- gsub('^.* secondary vegetation ', '', use.intensity)
  use.intensity <- gsub('Rangelands ', '', use.intensity)
  use.intensity <- gsub('Perennial ', '', use.intensity)
  use.intensity <- gsub('Annual ', '', use.intensity)
  use.intensity <- gsub('Managed pasture ', '', use.intensity)
  use.intensity <- gsub('Nitrogen ', '', use.intensity)
  use.intensity <- gsub('Urban ', '', use.intensity)
  use.intensity <- gsub('Timber ', '', use.intensity)
  aug$land.use <- factor(aug$LandUse, labels = land.use)
  aug$UseIntensity <- use.intensity

  p1 <- ggplot(aug, aes(logHPD.rs, y)) +
    geom_point(aes(color=UseIntensity, fill=UseIntensity), shape=10) +
    geom_smooth(formula="y ~ poly(x, 2)") +
    geom_ribbon(aes(ymin=ymin, ymax=ymax, fill=UseIntensity), alpha=0.2) +
    facet_grid(. ~ land.use) + ylab("log(abundance)") +
    scale_x_continuous(name="Human Population Density (log)",
                       limits=c(0, 1), breaks=c(0.0, 0.5, 1.0))
  return(p1)
}
