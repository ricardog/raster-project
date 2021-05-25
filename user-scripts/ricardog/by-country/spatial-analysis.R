#!/usr/bin/env Rscript

library(argparser, quietly=True)
library(broom, quietly=TRUE)
library(dplyr, quietly=TRUE)
library(ggplot2, quietly=TRUE)
library(gridExtra, quietly=TRUE)
library(lme4, quietly=TRUE)
library(rgdal, quietly=TRUE)
library(sjPlot, quietly=TRUE)
library(spdep, quietly=TRUE)
library(spatial, quietly=TRUE)
library(tibble, quietly=TRUE)

fit.model <- function(formula, data) {
    cat(paste("  Formula            : ", formula, "\n", sep=""))
    mod <- lm(formula, data=data, na.action=na.omit)
    terms <- attr(mod$terms, "term.labels")
    mdata <- data[complete.cases(data[, terms]), c(terms, "fips")]
    cat(paste("  Number of countries: ", nrow(mdata), "\n", sep=""))
    return(list(formula=formula, mod=mod, mdata=mdata))
}

print_mc <- function(name, data) {
    cat(paste("  ", name, ":\n", sep=""))
    cat(paste("    Statistic  : ", data$statistic, "\n", sep=""))
    cat(paste("    p value    : ", data$p.value, "\n", sep=""))
    cat(paste("    Alternative: ", data$alternative, "\n", sep=""))
}

do.moran <- function(x, nb, style, labels, name) {
    lw <- nb2listw(nb, zero.policy=TRUE, style=style)
    xx <- moran.mc(x, lw, nsim=99, zero.policy=TRUE)
    print_mc(name, xx)
    moran.plot(x, lw, zero.policy=TRUE, labels=labels, main=name, spChk=TRUE)
    tbl <- as.tibble(xx[c('statistic', 'p.value', 'alternative')])
    tbl <- add_column(tbl, name=name, .before=1)
    return(tbl)
}

ggplotRegression <- function (fit, pred) {
    if (missing(pred)) {
        pred <- 2
    }
    p1 = ggplot(fit$model, aes_string(x=names(fit$model)[pred],
                                      y=names(fit$model)[1])) + 
        geom_point() +
        stat_smooth(method = "lm", col = "red") +
        labs(title = paste("Adj R2 = ",signif(summary(fit)$adj.r.squared, 5),
                           "Intercept =",signif(fit$coef[[1]],5 ),
                           " Slope =",signif(fit$coef[[2]], 5),
                           " P =",signif(summary(fit)$coef[2,4], 5)))
    return(p1)
}

ggplotRegression.lmer <- function (fit, pred) {
    if (missing(pred)) {
        pred <- 2
    }
    face <- names(fit@flist)[[1]]
    p1 = ggplot(fit@frame, aes_string(x=names(fit@frame)[pred],
                                      y=names(fit@frame)[1])) + 
        geom_point() +
        stat_smooth(method = "lm", col = "red") +
        facet_grid(. ~ ar5)
    return(p1)
}

mydiag <- function(mod) {
    ps = lapply(2:ncol(mod$model), function(arg) ggplotRegression(mod, arg))
    do.call(grid.arrange, append(list(ncol=3),
                                 append(ps, plot_model(mod, type="diag"))))
}

p <- arg_parser("Fit soci-economic models to BII data")
p <- add_argument(p, "--year", help="Year for which the data was generated.")
argv <- parse_args(p)
if (is.na(argv$year)) {
    print(p)
    stop("Please speficy the year.")
}
#if (is.na(year)) {
    year  <- argv$year
#s}

countries.file <- '/Users/ricardog/src/eec/data/natural-earth/ne_10m_admin_0_countries/ne_10m_admin_0_countries.shp'
style <- "W"
#formula <- "ratio ~ prim_ratio + ec_pc + WJP.Rule.of.Law.Index..Overall.Score"
formula <- "ratio ~ prim_ratio + ec_pc"
formulas <- list("BIIAb_ratio ~ npp_ratio",
                 "BIIAb_ratio ~ npp_ratio + RoL",
                 paste("BIIAb_ratio ~ npp_ratio + RoL + ECI_", year, sep='')
                 #paste("BIIAb_ratio ~ npp_ratio + RoL + ECI_", year,
                 #      " + BTU_PC_", year, sep=''),
                 )
data.file <- paste('/Users/ricardog/tmp/jupyter/country-data-', year, '.csv',
                   sep='')

cat("*** Loading data\n")
shp <- readOGR(countries.file, verbose=FALSE)
levels(shp$FIPS_10_) = c(levels(shp$FIPS_10_), 'IS', 'SS', 'WE')
shp$FIPS_10_[shp$NAME == 'Israel'] = 'IS'
shp$FIPS_10_[shp$NAME == 'S. Sudan'] = 'SS'
shp$FIPS_10_[shp$NAME == 'Palestine'] = 'WE'

data <- read.csv(data.file)
rownames(data) <- data$fips
#for (y in 1980:2015) {
#    data[paste('ec_pc_', y, sep='')] = data[paste('ec_', y, sep='')] /
#        data[paste('pop_', y, sep='')] / 1e-5
#}
cat(paste("  Data file          : ", data.file, "\n", sep=""))
cat(paste("  Number of countries: ", nrow(data), "\n", sep=""))

cat("*** Fitting models\n")
#xx <- fit.model(formula, data)
#mod <- xx$mod
#mdata <- xx$mdata
#cnames <- mdata$name

mods <- lapply(formulas, function(f) fit.model(f, data=data))
summ.table <- do.call(rbind, lapply(mods, function(m) broom::glance(m$mod)))
summ.table
moran.summ <- list()

cat("*** Generating neighbors lists\n")
tmp.shp = shp[match(data$fips, shp$FIPS_10_), ]
xy <- coordinates(tmp.shp)
wr <- poly2nb(tmp.shp, row.names=tmp.shp$FIPS_10_, queen=FALSE)
wq <- poly2nb(tmp.shp, row.names=tmp.shp$FIPS_10_, queen=TRUE)
k3 <- knn2nb(knearneigh(xy, k=3, RANN=FALSE), row.names=tmp.shp$FIPS_10_)
k6 <- knn2nb(knearneigh(xy, k=6, RANN=FALSE), row.names=tmp.shp$FIPS_10_)

for (xxx in mods) {
    form <- xxx[[1]]
    mod <- xxx[[2]]
    mdata <- xxx[[3]]
    cnames <- mdata$name
    res <- residuals(mod)
    cat(paste("== Formula: ", form, "\n", sep=""))

    dev.new()
    cat("*** Diagnostics\n")
    mydiag(mod)

    cat("*** Moran checks\n")
    dev.new()
    par(mfrow=c(2,2))
    moran.summ <- append(moran.summ,
                         list(do.call(bind_rows, mapply(
                                                function(nb, name) {
                                                    do.moran(res, nb, style,
                                                             cnames, name)
                                                },
                                                nb=list(wr, wq, k3, k6),
                                                name=list('Rook', 'Queen', 'K3', 'K6'),
                                                SIMPLIFY=FALSE
                                            ))))
}
morans <- bind_rows(moran.summ)
print(morans)
stop("Done")

moran.plot(res, wrl, zero.policy=TRUE, labels=cnames, main='rook',
           spChk=TRUE)
moran.plot(res, wql, zero.policy=TRUE, labels=cnames, main='queen',
           spChk=TRUE)
moran.plot(res, k3l, zero.policy=TRUE, labels=cnames, main='k3',
           spChk=TRUE)
moran.plot(res, k6l, zero.policy=TRUE, labels=cnames, main='k6',
           spChk=TRUE)
     
cat("*** Moran\n")
xx <- moran.mc(res, wrl, nsim=99, zero.policy=TRUE)
print_mc('Rook', xx)
xx <- moran.mc(res, wql, nsim=99, zero.policy=TRUE)
print_mc('Queen', xx)
xx <- moran.mc(res, k3l, nsim=99, zero.policy=TRUE)
print_mc('k3', xx)
xx <- moran.mc(res, k6l, nsim=99, zero.policy=TRUE)
print_mc('K6', xx)

cat("*** Map\n")
dev.new()
#par(mfrow=c(2,2))
plot(tmp.shp, border="gray")
plot(wr, xy, col="red", add=TRUE)
#plot(tmp.shp, border="gray")
plot(wq, xy, col="green", add=TRUE)
#plot(tmp.shp, border="gray")
plot(k3, xy, col="blue", add=TRUE)
#plot(tmp.shp, border="gray")
plot(k6, xy, col="yellow", add=TRUE)
