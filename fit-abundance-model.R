#!/usr/bin/env Rscript

##
## "Parse" command-line arguments
##
library(argparser, quietly=TRUE)
p <- arg_parser("Run PREDICTS total abundance model")
p <- add_argument(p, "--site-data", help="site diversity rds file")
p <- add_argument(p, "--out", help="filename prefix for output files",
                  default='ab-model')
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
## Run total abundance model
##
cat("****\n* Running total abundance model\n")
model.data <- sites.div[,c('LogAbund', 'UI', 'logHPD.rs', #'logDistRd.rs',
                           'LandUse', 'UseIntensity', 'SS', 'SSB', 'SSBS')]
model.data <- na.omit(model.data)
saveRDS(model.data, file = paste(argv$out, '-data.rds', sep=''))
aModel <- lmer(LogAbund ~ UI +
                   poly(logHPD.rs, 2) +
                   LandUse:poly(logHPD.rs, 2) +
##                   LandUse:poly(logDistRd.rs, 2) +
                   (1 + LandUse | SS) + (1 | SSB),
               data = model.data,
               REML = TRUE,
               control = lmerControl(optimizer="bobyqa",
                                     optCtrl=list(maxfun=100000)))
saveRDS(aModel, file = paste(argv$out, '.rds', sep=''))

##
## Plot total abundance graph
##
cat("****\n* Plotting total abundance model\n")
png("abundance-response-plot.png",
    width=8.5, height=10, units="cm", res=300)
par(mfrow=c(2,1))
par(cex=0.66)

PlotErrBar(model = aModel, data=aModel@frame, responseVar="Abundance", logLink="e",
           catEffects="UI", forPaper=TRUE, ylim=c(-70,50))
mtext("A", side=3, line=-1, adj=-0.15)

PlotContEffects(model=aModel, data=model.data, effects="logHPD.rs",
##                otherContEffects="logDistRd.rs",
                otherFactors=list(LandUse="Primary Vegetation",
                                  UI="Primary Vegetation Minimal use"),
                xlab="Human population density",
                ylab="Abundance",
                seMultiplier=0.5,
                byFactor="LandUse",
                logLink="e")
mtext("B", side=3, line=-0.1, adj=-0.19)
dev.off()

##
## Extrcat human poulation density coefficients (for total abundance model)
##
hpd.coefs <- numeric()
TempMod <- lm(aModel@frame$`poly(logHPD.rs, 2)`[, 1] ~ model.data$logHPD.rs)
hpd.coefs['Poly1_I'] <- TempMod$coefficients['(Intercept)']
hpd.coefs['Poly1_1'] <- TempMod$coefficients['model.data$logHPD.rs']
TempMod <- lm(aModel@frame$`poly(logHPD.rs, 2)`[, 2] ~
                  model.data$logHPD.rs + I(model.data$logHPD.rs^2))
hpd.coefs['Poly2_I'] <- TempMod$coefficients['(Intercept)']
hpd.coefs['Poly2_1'] <- TempMod$coefficients['model.data$logHPD.rs']
hpd.coefs['Poly2_2'] <- TempMod$coefficients['I(model.data$logHPD.rs^2)']
write.csv(hpd.coefs, file = paste(argv$out, '-hpd-coefs.csv', sep=''))

##
## Extract land-use and land-use intensity coefficients
##
coefs <- numeric()
coefs['PriMin'] <- 0.0
coefs['PriLt'] <- (fixef(aModel))['UIPrimary Vegetation Light use']
coefs['PriInt'] <- (fixef(aModel))['UIPrimary Vegetation Intense use']
coefs['SecMin'] <- (fixef(aModel))['UISecondary Vegetation Minimal use']
coefs['SecLt'] <- (fixef(aModel))['UISecondary Vegetation Light use']
coefs['CrpMin'] <- (fixef(aModel))['UICropland Minimal use']
coefs['CrpLt'] <- (fixef(aModel))['UICropland Light use']
coefs['CrpInt'] <- (fixef(aModel))['UICropland Intense use']
coefs['PasMin'] <- (fixef(aModel))['UIPasture Minimal use']
coefs['PasLt'] <- (fixef(aModel))['UIPasture Light use']
coefs['PasInt'] <- (fixef(aModel))['UIPasture Intense use']
coefs['UrbMin'] <- (fixef(aModel))['UIUrban Minimal use']
coefs['UrbInt'] <- (fixef(aModel))['UIUrban Intense use']
coefs['hpd_1'] <- (fixef(aModel))['poly(logHPD.rs, 2)1']
coefs['hpd_2'] <- (fixef(aModel))['poly(logHPD.rs, 2)2']
coefs['rddist_1'] <- 0#(fixef(aModel))['poly(logDistRd.rs, 2)1']
coefs['rddist_2'] <- 0#(fixef(aModel))['poly(logDistRd.rs, 2)2']

coefs['hpd_1.Sec'] <- (fixef(aModel))['poly(logHPD.rs, 2)1:LandUseSecondary Vegetation']+ coefs['hpd_1']
coefs['hpd_1.Crp'] <- (fixef(aModel))['poly(logHPD.rs, 2)1:LandUseCropland']+ coefs['hpd_1']
coefs['hpd_1.Pas'] <- (fixef(aModel))['poly(logHPD.rs, 2)1:LandUsePasture']+ coefs['hpd_1']
coefs['hpd_1.Urb'] <- (fixef(aModel))['poly(logHPD.rs, 2)1:LandUseUrban']+ coefs['hpd_1']
coefs['hpd_2.Sec'] <- (fixef(aModel))['poly(logHPD.rs, 2)2:LandUseSecondary Vegetation']+ coefs['hpd_2']
coefs['hpd_2.Crp'] <- (fixef(aModel))['poly(logHPD.rs, 2)2:LandUseCropland']+ coefs['hpd_2']
coefs['hpd_2.Pas'] <- (fixef(aModel))['poly(logHPD.rs, 2)2:LandUsePasture']+ coefs['hpd_2']
coefs['hpd_2.Urb'] <- (fixef(aModel))['poly(logHPD.rs, 2)2:LandUseUrban']+ coefs['hpd_2']

coefs['rddist_1.Sec'] <- 0#(fixef(aModel))['poly(logDistRd.rs, 2)1:LandUseSecondary Vegetation']+coefs['rddist_1']
coefs['rddist_1.Crp'] <- 0#(fixef(aModel))['poly(logDistRd.rs, 2)1:LandUseCropland']+coefs['rddist_1']
coefs['rddist_1.Pas'] <- 0#(fixef(aModel))['poly(logDistRd.rs, 2)1:LandUsePasture']+coefs['rddist_1']
coefs['rddist_1.Urb'] <- 0#(fixef(aModel))['poly(logDistRd.rs, 2)1:LandUseUrban']+coefs['rddist_1']
coefs['rddist_2.Sec'] <- 0#(fixef(aModel))['poly(logDistRd.rs, 2)2:LandUseSecondary Vegetation']+coefs['rddist_2']
coefs['rddist_2.Crp'] <- 0#(fixef(aModel))['poly(logDistRd.rs, 2)2:LandUseCropland']+coefs['rddist_2']
coefs['rddist_2.Pas'] <- 0#(fixef(aModel))['poly(logDistRd.rs, 2)2:LandUsePasture']+coefs['rddist_2']
coefs['rddist_2.Urb'] <- 0#(fixef(aModel))['poly(logDistRd.rs, 2)2:LandUseUrban']+coefs['rddist_2']

write.csv(coefs, file = paste(argv$out, '-coefs.csv', sep=''))
