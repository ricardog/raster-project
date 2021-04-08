FROM rocker/tidyverse:4.0.0
MAINTAINER Ricardo E. Gonzalez <ricardog@ricardog.com>

RUN apt-get update -qq \
	&& apt-get upgrade -y \
  && apt-get install -y --no-install-recommends \
    gdal-bin \
    lbzip2 \
    libfftw3-dev \
    libgdal-dev \
    libgeos-dev \
    libgsl0-dev \
    libgl1-mesa-dev \
    libglu1-mesa-dev \
    libhdf4-alt-dev \
    libhdf5-dev \
    libjq-dev \
    libpq-dev \
    libproj-dev \
    libprotobuf-dev \
    libnetcdf-dev \
    libspatialindex-dev \
    libsqlite3-dev \
    libssl-dev \
    libudunits2-dev \
    lsb-release \
    netcdf-bin \
    protobuf-compiler \
    sqlite3 \
    tk-dev \
    unixodbc-dev
RUN install2.r --error --skipinstalled \
    BiocManager \
    RColorBrewer \
    RandomFields \
    RNetCDF \
    classInt \
    crayon \
    deldir \
    devtools \
    gstat \
    ggplot2 \
    hdf5r \
    lme4 \
    mapdata \
    maptools \
    mapview \
    ncdf4 \
    pbdZMQ \
    proj4 \
    raster \
    rgdal \
    rgeos \
    rlas \
    sf \
    sjPlot \
    sp \
    spacetime \
    spatstat \
    spdep \
    tmap \
    geoR \
    geosphere \
    && R -e "devtools::install_github(paste0('IRkernel/', c('repr', 'IRdisplay', 'IRkernel')))"
    ## from bioconductor
    ## && R -e "BiocManager::install('rhdf5')"
