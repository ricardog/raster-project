get_rcp_grid <- function(wdir, scenario,
                         LUtypes=c("primary","secondary","cropland","pasture",
                                   "urban","plantation","ice_water"),
                         years=2005:2100) { 
    
  origDir<-getwd()
  
  if (!(FALSE %in% (as.integer(years)==years))){
    years<-as.integer(years)
    if (!(class(years)=="integer")) stop("Years are in the wrong format")
  } else {
    stop("Non-integer year specified")
  }
  
  # Set up the list to hold the results
  ret<-list()
  
  # Add the specified years to the results list
  ret$years<-years
  
  # Set the working directory
  setwd.try <- try(setwd(wdir), silent=T)
  if (class(setwd.try) == "try-error") {
    stop("Directory not recognized")
  }

  # Check that the specified directory contains all expected folders
  if (!("1500_2005" %in% dir())) warning("Directory appears not to contain all of the RCP data. Results may be incomplete")
  if (!("2005_2100_minicam" %in% dir())) warning("Directory appears not to contain all of the RCP data. Results may be incomplete")
  
  if (scenario %in% ls())
  {
    if (!((scenario=="image") | 
            (scenario == "aim") | (scenario=="message") | 
            (scenario=="minicam"))) stop("Scenario not recognized")
  }
  
  # Read in map to make mask
  mask <- readGDAL("1500_2005/updated_states/gothr.1500.txt", silent = TRUE)
  mask$band1[which(mask$band1 > 0)] <- 1
  
  plantationInLUs <- FALSE
  if ("plantation" %in% LUtypes){
    plantationInLUs <- TRUE
    LUtypes <- c(LUtypes, "plantation_pri", "plantation_sec")
    LUtypes <- LUtypes[-which(LUtypes == "plantation")]
  }
  
  for (lu in LUtypes){
    # For the current PREDICTS land use, specify the prefixes applied to RCP land-use types that
    # should be applied as positive incrememts (pprefix) and that should be applied as
    # negative increments (nprefix). 
    # For full details of the RCP land-use types that the prefixes correspond to, see RCP documentation
    if (lu=="primary"){ pprefix<-c("gothr");nprefix<-c("gfvh1","gfvh2")}
    else if (lu=="secondary"){ pprefix<-c("gsecd");nprefix<-c("gfsh1","gfsh2","gfsh3")}
    else if (lu=="cropland"){ pprefix<-c("gcrop");nprefix<-list()}
    else if (lu=="pasture"){ pprefix<-c("gpast");nprefix<-list()}
    else if (lu=="urban"){ pprefix<-c("gurbn");nprefix<-list()}
    else if (lu=="plantation_pri"){pprefix<-c("gfvh1","gfvh2");nprefix<-list()}
    else if (lu=="plantation_sec"){pprefix<-c("gfsh1","gfsh2","gfsh3");nprefix<-list()}
    else if (lu=="ice_water"){pprefix<-c("gsumm");nprefix<-list("gothr","gsecd","gcrop","gpast","gurbn")}
    else stop("One of the land use types is not supported")

    cat(paste("***\n", lu, "\n", sep = ""))
    temp.results<-list()
    temp.grid<-mask
    temp.grid$band1<-0
    for (yr in 1:length(years)){
      temp.results<-c(temp.results,temp.grid)
    }
    
    i<-1
    for (yr in years){
      if (yr <= 2005) { folder <- "1500_2005/updated_states/" }
      else {
        if (scenario=="image") {folder <- "2005_2100_image/updated_states/"}
        else if (scenario=="aim") {folder< - "2005_2100_aim/updated_states/"}
        else if (scenario=="message") {folder <-"2005_2100_message/updated_states/"}
        else if (scenario=="minicam") {folder <-"2005_2100_minicam/updated_states/"}
        else {stop("Land use scenario not recognized")}
      }
      missingFile <- FALSE
      for (p in pprefix) {
        f.path<-paste(folder, p, ".", yr, ".txt", sep="")
        if (file.exists(f.path)) {
          temp.dat <- readGDAL(f.path,silent=T)$band1
          temp.results[[i]]$band1 <- temp.results[[i]]$band1 + temp.dat
        }
        else { missingFile <- TRUE }
      }
      for (p in nprefix) {
        f.path<-paste(folder, p, ".", yr, ".txt", sep="")
        if (file.exists(f.path)) {
          temp.dat<-readGDAL(f.path,silent=T)$band1
          temp.results[[i]]$band1<-temp.results[[i]]$band1 - temp.dat
        }
        else { missingFile <- TRUE }
      }
      if (lu == "secondary"){
        temp.results[[i]]$band1 <- mapply(function(x,y) {
            return(max(x,y))
        }, temp.results[[i]]$band1, 0)
      }
      else if (lu == "plantation_pri") {
        f.path <- paste(folder, "gothr.", yr, ".txt", sep="")
        pri<-readGDAL(f.path,silent=TRUE)
        temp.results[[i]]$band1 <- mapply(function(x,y) {
            return(min(x,y))
        }, temp.results[[i]]$band1, pri$band1)
      }
      else if (lu == "plantation_sec"){
        f.path <- paste(folder, "gsecd." ,yr, ".txt", sep="")
        sec <- readGDAL(f.path,silent=TRUE)
        temp.results[[i]]$band1 <- mapply(function(x,y) {
            return(min(x,y))
        }, temp.results[[i]]$band1, sec$band1)
      }
      
      if (missingFile == TRUE) { temp.results[[i]]$band1 <- NA }
      i <- i + 1
    }
    for (yr in 1:length(years)){
      temp.results[[yr]]$band1[which(mask$band1==0)] <- NA
    }
    ret<-c(ret, lapply(lu, function(rcp) return(temp.results)))
    
  }
  if (missingFile) stop("Error a required land-use file could not be found")
  names(ret) <- c("year", LUtypes)
  
  if(plantationInLUs){
    i <- 1
    ret$plantation<-list()
    for (yr in years) {
      ret$plantation[[i]] <- ret$plantation_pri[[i]]
      ret$plantation[[i]]$band1 <- ret$plantation_pri[[i]]$band1 + ret$plantation_sec[[i]]$band1
      i <- i+1
    }
    ret$plantation_pri<-NULL
    ret$plantation_sec<-NULL
  }
  
  setwd(origDir)

  return(ret)
}

dump_maps <-  function(maps, years) {
  if (!(FALSE %in% (as.integer(years) == years))){
    years <- as.integer(years)
    if (!(class(years) == "integer")) stop("Years are in the wrong format")
  } else {
    stop("Non-integer year specified")
  }
  cols = names(maps)
  for (yr in years) {
    for (lu in cols[-which(cols == "year")]) {
        idx <- yr - years[1] + 1
        writeGDAL(maps[[lu]][[idx]], paste(lu, ".", yr, ".asc", sep=""),
                  drivername="AAIGrid", type="Float32", mvFlag=(-9999))
    }
  }  
}    
