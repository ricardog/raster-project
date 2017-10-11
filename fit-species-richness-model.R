#!/usr/bin/env Rscript

##
## "Parse" command-line arguments
##
library(argparser, quietly=TRUE)
p <- arg_parser("Run PREDICTS species richness model")
p <- add_argument(p, "--site-data", help="diversity rds file")
p <- add_argument(p, "--out", help="filename prefix for output files",
                  default='sr-model')
argv <- parse_args(p)

if (is.na(argv$site_data) || is.na(argv$out)) {
    print(p)
    stop()
}

##
## Load packages
##
cat("****\n* Loading packages\n")
library(roquefort, quietly = TRUE)

##
## Read stored site data
##
sites.div <- readRDS(argv$site_data)

##
## Run the model
##
cat("****\n* Running species richness model\n")
model.data <- sites.div[,c('Species_richness', 'UI', 'logHPD.rs', 'logDistRd.rs',
                           'LandUse', 'UseIntensity', 'SS', 'SSB', 'SSBS')]
model.data <- na.omit(model.data)
saveRDS(model.data, file = paste(argv$out, '-data.rds', sep=''))
model.data <- model.data[1:floor(nrow(model.data) / 4), ]
sModel <- glmer(Species_richness ~ UI +
                    poly(logHPD.rs, 2) +
                    poly(logDistRd.rs, 2) +
                    LandUse:poly(logHPD.rs, 2) +
                    LandUse:poly(logDistRd.rs, 2) +
                    (1 + LandUse | SS) +
                    (1 | SSB) +
                    (1 | SSBS),
                family="poisson",data=model.data,
                control=glmerControl(optimizer="bobyqa",optCtrl=list(maxfun=100000)))
stopifnot(sModel$converged)
save(sModel, file = paste(argv$out, '.rds', sep=''))

##
## Plot species richness graphs (uses functions in roquefort package)
##
cat("****\n* Plotting species richness results\n")
png("species-richness-response-plot.png",
    width=8.5, height=15, units="cm", res=1200)
par(mfrow=c(3,1))

PlotErrBar(model=sModel, data=sModel@frame, responseVar="Richness",
           logLink="e", catEffects="UI", forPaper=TRUE)
mtext("A", side=3, line=-1, adj=-0.15)

PlotContEffects(model=sModel, data=model.data, effects="logHPD.rs",
                otherContEffects="logDistRd.rs",
                otherFactors=list(UI="Primary Vegetation Minimal use"),
                xlab="Human population density",
                ylab="Species richness",
                byFactor="LandUse",
                seMultiplier=0.5,
                logLink="e")
mtext("B", side=3, line=-0.1, adj=-0.19)

PlotContEffects(model=sModel, data=model.data, effects="logDistRd.rs",
                otherContEffects="logHPD.rs",
                otherFactors=list(LandUse="Primary Vegetation",
                                  UI="Primary Vegetation Minimal use"),
                xlab="Distance to nearest road",
                ylab="Species richness",
                byFactor="LandUse",
                seMultiplier=0.5,
                logLink="e")
mtext("C", side=3, line=-0.1, adj=-0.19)
dev.off()

##
## Extract human population density coefficients
##
hpd.coefs <- numeric()
TempMod <- lm(sModel@frame$`poly(logHPD.rs, 2)`[,1]~model.data$logHPD.rs)
hpd.coefs['Poly1_I'] <- TempMod$coefficients['(Intercept)']
hpd.coefs['Poly1_1'] <- TempMod$coefficients['model.data$logHPD.rs']
TempMod <- lm(sModel@frame$`poly(logHPD.rs, 2)`[,2]~model.data$logHPD.rs+I(model.data$logHPD.rs^2))
hpd.coefs['Poly2_I'] <- TempMod$coefficients['(Intercept)']
hpd.coefs['Poly2_1'] <- TempMod$coefficients['model.data$logHPD.rs']
hpd.coefs['Poly2_2'] <- TempMod$coefficients['I(model.data$logHPD.rs^2)']
write.csv(hpd.coefs, file = paste(argv$out, '-hpd-coefs.csv', sep=''))

##
## Extract road-distance coefficients
##
rddist.coefs <- numeric()
TempMod <- lm(sModel@frame$`poly(logDistRd.rs, 2)`[,1]~model.data$logDistRd.rs)
rddist.coefs['Poly1_I'] <- TempMod$coefficients['(Intercept)']
rddist.coefs['Poly1_1'] <- TempMod$coefficients['model.data$logDistRd.rs']
TempMod <- lm(sModel@frame$`poly(logDistRd.rs, 2)`[,2]~model.data$logDistRd.rs+I(model.data$logDistRd.rs^2))
rddist.coefs['Poly2_I'] <- TempMod$coefficients['(Intercept)']
rddist.coefs['Poly2_1'] <- TempMod$coefficients['model.data$logDistRd.rs']
rddist.coefs['Poly2_2'] <- TempMod$coefficients['I(model.data$logDistRd.rs^2)']
write.csv(rddist.coefs, file = paste(argv$out, '-rddist-coefs.csv', sep=''))

##
## Extract land-use coefficients
##
coefs <- numeric()
coefs['PriMin'] <- 0.0
coefs['PriLt'] <- (fixef(sModel))['UIPrimary Vegetation Light use']
coefs['PriInt'] <- (fixef(sModel))['UIPrimary Vegetation Intense use']
coefs['SecMin'] <- (fixef(sModel))['UISecondary Vegetation Minimal use']
coefs['SecLt'] <- (fixef(sModel))['UISecondary Vegetation Light use']
coefs['CrpMin'] <- (fixef(sModel))['UICropland Minimal use']
coefs['CrpLt'] <- (fixef(sModel))['UICropland Light use']
coefs['CrpInt'] <- (fixef(sModel))['UICropland Intense use']
coefs['PasMin'] <- (fixef(sModel))['UIPasture Minimal use']
coefs['PasLt'] <- (fixef(sModel))['UIPasture Light use']
coefs['PasInt'] <- (fixef(sModel))['UIPasture Intense use']
coefs['UrbMin'] <- (fixef(sModel))['UIUrban Minimal use']
coefs['UrbInt'] <- (fixef(sModel))['UIUrban Intense use']
coefs['hpd_1'] <- (fixef(sModel))['poly(logHPD.rs, 2)1']
coefs['hpd_2'] <- (fixef(sModel))['poly(logHPD.rs, 2)2']
coefs['rddist_1'] <- (fixef(sModel))['poly(logDistRd.rs, 2)1']
coefs['rddist_2'] <- (fixef(sModel))['poly(logDistRd.rs, 2)2']

coefs['hpd_1.Sec'] <- (fixef(sModel))['poly(logHPD.rs, 2)1:LandUseSecondary Vegetation'] + coefs['hpd_1']
coefs['hpd_1.Crp'] <- (fixef(sModel))['poly(logHPD.rs, 2)1:LandUseCropland'] + coefs['hpd_1']
coefs['hpd_1.Pas'] <- (fixef(sModel))['poly(logHPD.rs, 2)1:LandUsePasture'] + coefs['hpd_1']
coefs['hpd_1.Urb'] <- (fixef(sModel))['poly(logHPD.rs, 2)1:LandUseUrban'] + coefs['hpd_1']
coefs['hpd_2.Sec'] <- (fixef(sModel))['poly(logHPD.rs, 2)2:LandUseSecondary Vegetation'] + coefs['hpd_2']
coefs['hpd_2.Crp'] <- (fixef(sModel))['poly(logHPD.rs, 2)2:LandUseCropland'] + coefs['hpd_2']
coefs['hpd_2.Pas'] <- (fixef(sModel))['poly(logHPD.rs, 2)2:LandUsePasture'] + coefs['hpd_2']
coefs['hpd_2.Urb'] <- (fixef(sModel))['poly(logHPD.rs, 2)2:LandUseUrban'] + coefs['hpd_2']

coefs['rddist_1.Sec'] <- (fixef(sModel))['poly(logDistRd.rs, 2)1:LandUseSecondary Vegetation'] + coefs['rddist_1']
coefs['rddist_1.Crp'] <- (fixef(sModel))['poly(logDistRd.rs, 2)1:LandUseCropland'] + coefs['rddist_1']
coefs['rddist_1.Pas'] <- (fixef(sModel))['poly(logDistRd.rs, 2)1:LandUsePasture'] + coefs['rddist_1']
coefs['rddist_1.Urb'] <- (fixef(sModel))['poly(logDistRd.rs, 2)1:LandUseUrban'] + coefs['rddist_1']
coefs['rddist_2.Sec'] <- (fixef(sModel))['poly(logDistRd.rs, 2)2:LandUseSecondary Vegetation'] + coefs['rddist_2']
coefs['rddist_2.Crp'] <- (fixef(sModel))['poly(logDistRd.rs, 2)2:LandUseCropland'] + coefs['rddist_2']
coefs['rddist_2.Pas'] <- (fixef(sModel))['poly(logDistRd.rs, 2)2:LandUsePasture'] + coefs['rddist_2']
coefs['rddist_2.Urb'] <- (fixef(sModel))['poly(logDistRd.rs, 2)2:LandUseUrban'] + coefs['rddist_2']

write.csv(coefs, file = paste(argv$out, '-coefs.csv', sep=''))
