library(rgdal)

cat("Preparing data\n")

inDir<-"C:/HYDE data/"
outDir<-"C:/HYDE data - coarse/"

if(!file.exists(outDir)) dir.create(outDir)

setwd(inDir)

if(!file.exists("temp")) dir.create("temp")

all.yrs<-c(paste(seq(from=10000,to=1000,by=-1000),"bc",sep=""),
            paste(seq(from=0,to=1600,by=100),"ad",sep=""),
            paste(seq(from=1700,to=2000,by=10),"ad",sep=""),
            "2005ad")

# Set land uses for resampling
lus<-list("crop","gras","uopp")

# Set the grid for the output maps and create a dummy map
grid.coarse<-GridTopology(cellcentre.offset=c(-179.75,-89.75),
                          cellsize=c(0.5,0.5),cells.dim=c(720,360))
dummy.coarse<-raster(SpatialGridDataFrame(
  grid=grid.coarse,data=data.frame(band1=rep(NA,720*360))))

# First aggregate the land-area map
area.f<-readGDAL(paste(inDir,"garea_cr.asc",sep=""),silent=TRUE)
data.c<-aggregate(raster(area.f),fact=6,fun=sum)@data@values
area.c<-SpatialGridDataFrame(grid=grid.coarse,data=data.frame(band1=data.c))

cat("Processing land-area map\n")
writeGDAL(area.c,paste(outDir,"/garea_cr.asc",sep=""),drivername="AAIGrid",mvFlag=(-9999))
temp<-lapply(as.list(dir(outDir)[grep(".aux",dir(outDir))]),FUN=
               function(x) file.remove(paste(outDir,x,sep="")))

for (y in all.yrs){
  cat(paste("\rProcessing Year:",y,"              ",sep=""))
  # Unzip the files in the land-use and population directories for this year
  unzip(zipfile=paste(y,"_lu.zip",sep=""),exdir=paste(inDir,"/temp",sep=""))
  unzip(zipfile=paste(y,"_pop.zip",sep=""),exdir=paste(inDir,"/temp",sep=""))
  
  # For all selected land uses, resample the maps
  temp<-lapply(lus,FUN=function(x){
    fName<-(dir(paste(inDir,"/temp",sep=""))[
      grep(x,dir(paste(inDir,"/temp",sep="")))])
    lu.f<-readGDAL(paste(inDir,"/temp/",fName,sep=""),silent=TRUE)
    data.c<-aggregate(raster(lu.f),fact=6,fun=sum)@data@values
    lu.c<-SpatialGridDataFrame(grid=grid.coarse,data=data.frame(band1=data.c))
    writeGDAL(lu.c,paste(outDir,"/",fName,sep=""),drivername="AAIGrid",mvFlag=(-9999))
  })
  
  # Delete .aux files and the output directory and all files in the temp directory
  temp<-lapply(as.list(dir(outDir)[grep(".aux",dir(outDir))]),FUN=
                 function(x) file.remove(paste(outDir,x,sep="")))
  temp<-lapply(as.list(dir(paste(inDir,"/temp",sep=""))),FUN=
                 function(x) file.remove(paste(inDir,"/temp/",x,sep="")))
  
}

