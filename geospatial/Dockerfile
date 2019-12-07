FROM rocker/tidyverse:3.5.3
MAINTAINER "Carl Boettiger" cboettig@ropensci.org

RUN apt-get update \
  && apt-get install -y --no-install-recommends \
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
    liblwgeom-dev \
    libproj-dev \
    libprotobuf-dev \
    libnetcdf-dev \
    libspatialindex-dev \
    libsqlite3-dev \
    libssl-dev \
    libudunits2-dev \
    netcdf-bin \
    protobuf-compiler \
    tk-dev \
    unixodbc-dev
RUN install2.r --error \
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
