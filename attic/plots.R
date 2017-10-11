#!/usr/bin/env Rscript

library(argparser, quietly=TRUE)
library(broom)
library(ggplot2)
library(gridExtra)


doit <- function(argv) {
   if (is.na(argv$refdir) || is.na(argv$newdir)) {
      print(p)
      stop()
   }

   ref.model <- readRDS(paste(argv$refdir, 'ab-model.rds', sep='/'))
   ref.data <- readRDS(paste(argv$refdir, 'ab-model-data.rds', sep='/'))

   new.model <- readRDS(paste(argv$newdir, 'ab-model.rds', sep='/'))
   new.data <- readRDS(paste(argv$newdir, 'ab-model-data.rds', sep='/'))
   
   ref <- augment(ref.model, ref.data)
   new <- augment(new.model, new.data)

   if (is.na(argv$ref_title)) {
      ref.title <- 'Reference Model'
   } else {
      ref.title <- argv$ref_title
   }
   if (is.na(argv$new_title)) {
      new.title <- 'New Model'
   } else {
      new.title <- argv$new_title
   }
   dpi <- 300
   if (is.na(argv$dpi)) {
      dpi <- argv$dpi
   }

   ##xform <- function(x) { return exp(x) }
   ##if (argv$l) {
   ##    xform <- function(x) return exp(x)
   ##} else {
   ##    xform <- function(x) return x
   ##}

   p1 <- ggplot(ref, aes(logHPD.rs, LogAbund,
                         color=UseIntensity, fill=UseIntensity)) +
      geom_point() + facet_grid(. ~ LandUse) +  ggtitle(ref.title) +
      ylab('LogAbund')
   p3 <- ggplot(ref, aes(logHPD.rs, exp(.fixed),
                         color=UseIntensity, fill=UseIntensity)) +
      geom_point() + facet_grid(. ~ LandUse) +
      ylab('Abund') + theme(legend.position="none")
   p5 <- ggplot(ref, aes(logHPD.rs, .resid,
                         color=UseIntensity, fill=UseIntensity)) +
      geom_point() + facet_grid(. ~ LandUse) +
      ylab('Residuals') + theme(legend.position="none")

   p2 <- ggplot(new, aes(logHPD.rs, LogAbund,
                         color=UseIntensity, fill=UseIntensity)) +
      geom_point() + facet_grid(. ~ LandUse) + ggtitle(new.title) +
      ylab('LogAbund')
   p4 <- ggplot(new, aes(logHPD.rs, exp(.fixed),
                         color=UseIntensity, fill=UseIntensity)) +
      geom_point() + facet_grid(. ~ LandUse) +
      ylab('Abund') + theme(legend.position="none")
   p6 <- ggplot(new, aes(logHPD.rs, .resid,
                         color=UseIntensity, fill=UseIntensity)) +
      geom_point() + facet_grid(. ~ LandUse) +
      ylab('Residuals') + theme(legend.position="none")

   if (!is.na(argv$pdf)) {
      pdf(argv$pdf, res = dpi, width = 6 * dpi, height = 4 * dpi)
   } else if (!is.na(argv$png)) {
      png(argv$png, res = dpi, width = 6 * dpi, height = 4 * dpi)
   } else {
      X11()
   }
   grid.arrange(p1, p2, p3, p4, p5, p6, nrow=3)
                                        #readline(prompt="Press [enter] to continue")
                                        #invisible(readLines("stdin", n=1))
   if (!interactive() && is.na(argv$png) && is.na(argv$pdf)) {
      while (!is.null(dev.list())) Sys.sleep(1)
   }
}

if (!interactive()) {
   p <- arg_parser("Plot human population density response curves")
   p <- add_argument(p, "--png", help="Generate png output")
   p <- add_argument(p, "--pdf", help="Generate pdf output")
   p <- add_argument(p, "--refdir", help="Reference output directory")
   p <- add_argument(p, "--newdir", help="New output directory")
   p <- add_argument(p, "--ref-title", help="Title for reference model panel")
   p <- add_argument(p, "--new-title", help="Title for new model panel")
   p <- add_argument(p, "--l", help="Data is log transformed", flag=TRUE)
   p <- add_argument(p, "--dpi", help="Resolution of rasters in dots per inch", default=300)
   argv <- parse_args(p)
   doit(argv)
}
