
Overview
========

This directory provides a fast implementation of the PREDICTS projection
code. There are three main components:

1.  r2py
2.  rasterset
3.  predicts-specific code

All three components are in the directory projections and get installed
as a single python module (it's easier to only install one python module
for now).

The directory also contains a number of driver scripts (luh2-test.py,
luh5-test.py), utility scripts, and throw-away scripts I used while
writing my masters' dissertation. Over time I will try to clean up this
stuff and only leave here code related to projections.

Data acquisition, cleanup, and normalization
============================================

The code requires the following data-sets:

- Global roads database:
  [gRoads v1](http://sedac.ciesin.columbia.edu/data/set/groads-global-roads-open-access-v1)

- Global rural-urban population density:
  [GRUMP v1](http://sedac.ciesin.columbia.edu/data/set/grump-v1-population-density/data-download)

- Global rural-urban population density (v4): 
  The latest version of the [GRUMP (v4)](http://sedac.ciesin.columbia.edu/data/collection/gpw-v4)
  database is available. Perhaps I should switch to this new version?

  * Citation: 
    Center for International Earth Science Information Network -
    CIESIN - Columbia University. 2016. Gridded Population of the World,
    Version 4 (GPWv4): Population Density Adjusted to Match 2015
    Revision UN WPP Country Totals. Palisades, NY: NASA Socioeconomic
    Data and Applications Center (SEDAC).
    <http://dx.doi.org/10.7927/H4HX19NJ>.

    -   When authors make use of data they should cite both the data set
        and the scientific publication, if available. Such a practice
        gives credit to data set producers and advances principles of
        transparency and reproducibility. Please visit the data
        citations page for details. Users who would like to choose to
        format the citation(s) for this dataset using a myriad of
        alternate styles can copy the DOI number and paste it into
        Crosscite's website.

- Historical land-use maps (optional): 
  The code grovels over the historical land-use maps to calculate the
  age of secondary vegetation. Not all projections use this information,
  e.g. the fine resolution projections don't take into account secondary
  vegetation age. [HYDE 3.1 Land-use
  data](http://themasites.pbl.nl/tridion/en/themasites/hyde/download/index-2.html)

- Spatial Population Scenarios:
  These are human population projections that match the SSPs and
  include urbanization. The data is available only for each decade
  (2010, 2020, etc.) and is available on a 1/8 grid. For use with the
  LUG2 data is needs to be scaled and interpolated (see the gen~sps~
  script).
  [SPS](https://www2.cgd.ucar.edu/sections/tss/iam/spatial-population-scenarios)

- Land-use intensity calculation:
  this data is required to generate a predictive model for land-use
  intensity. There are two sources of information: 1km grid maps (used
  in the fine resolution projection code) and .csv files for each
  land-use type. This correspond to Table 2 in the Nature
  supplementary information section

- UN countries database:
  Rasters are generated from a shape file called
  [Natural Earth 10m Admin 0 -- Countries](http://www.naturalearthdata.com/http//www.naturalearthdata.com/download/10m/cultural/ne_10m_admin_0_countries.zip).

  Much of the information available in this vector file is also
  available in **TM-WORLDBORDER** but the later has follen out of date
  and does not have the latest information and the former does not
  include the numerical code for the UN subregions. 

- UN subregion database::
  Rasters are generated from a shape file called
  [TM-WORLDBORDERS](http://thematicmapping.org/downloads/TM_WORLD_BORDERS-0.3.zip).

- UP world population prospects database:
  WPP 2010](https://esa.un.org/unpd/wpp/)
- RCP land-use projection database:
  [RCP 1.1](https://tntcat.iiasa.ac.at/RcpDb/dsd?Action=htmlpage&page=welcome)

- Global high-resolution (30") land-use data:
  This is the data set used in the 2016 Science paper. [Fine
  resolution land-use data (2005)](https://data.csiro.au/dap/landingpage?pid=csiro:15276)

- Terrestrial ecoregions of the world:
  WWF dataset [Terrestrial ecoregions of the world (2012)](http://www.worldwildlife.org/publications/terrestrial-ecoregions-of-the-world)

- PREDCITS database:
  only needed ig you plan to fit new models.

All map / grid based data needs to be cleaned up and normalized, that is
make sure they all have the same projection, dimensions, and cell size.

How to
======

There are a number of scripts to can be used to generate projections
using PREDICTS models.

- luh2-test.py:
  Generates projections using LUH2 data and Sam's forested/non-forested
  models.

- luh5-test.py:
  Generates projections using LUH2 data and Tim's models (from Science
  manuscript). Or any model that has similar structure.

- adrid-test.py:
  Generates projections using RCP data and Adriana's model for
  tropical abundance. I wrote this mainly to test the code using the
  low resolution data before moving on to the high-resolution data.

- adrid-1km.py:
  Generates projections using 30" rasters and Adriana's tropical
  abundance model. Uses streaming to reduce memory and CPU
  requirements during the computation. I haven't tried running it in
  some time so likely broken.

These scripts are meant as starting points from which you should develop
your own code.  They have hard-coded assumptions about where to find
input rasters and models, and where to save output rasters.  They expect
source data to be under `$DATA_ROOT` and generated data under
`$OUTDIR/<name>/...`

You will need to have a number of input data rasters, e.g. UN
sub-regions, reference human population density.

The script `setup.sh` will attempt to generate all the derived data for
all land use data sources (luh2, luh5, rcp, 1km) but will likely not
work under windows :(. But it at does have the recipes required to
generate the data.

Code structure
==============

- projections:
  all the library code and most likely place to start if you want to
  understand how the code works.  There are three independent python modules

  - r2py: converts n R model to a python module.  Includes an executable
    script (`r2py`) which does the conversion.
  - rasterset: defines a data-frame-like structure which each column is
    defined by a function that computes a raster.
  - predicts.py: PREDICTS-specific code.  This is what defines the four
    sets of PREDICTS templates (one each fo RCP, LUH2, LUH5 (five
    land-use classes), and 1km.

- lu:
  Land use stuff. One python module per source of data. The rcp module
  has code for extracting data from the distribution tar files into
  individual files that are easier to work with

- lui:
  Code corresponding to the UI variable in models. The python modules
  define classes used when evaluating projectiosn to compute land use
  intensity.

- ui:
  Code corresponding to UseIntensity UseIntensity variable in models.

- hpd:
  Code for projecting human population density. I implemented three
  algorithms.

  - scale GRUMPS based on WPP (scaling by country)
  - Interpolate SPS
  - Scale GRUMPS by interpolated SPS (scaling by pixel)

  Note that WPP only extends back to 1950 so there is currently no
  mechanism for projecting/calculating population density before 1950.
  
- roads:
  Code for computing and rasterizing distance to a road using GDAL.

- scripts:
  top-level scripts that are installed as executable tools.

- attic:
  miscellaneous scripts that I found useful and didn't want to delete
  but didn't expect to keep using.

Installation
============

Ubuntu
------

```bash
pip install -e .
```

In the directory you are in should take care of things. But, I've found
this often fails. On linux the following seems to do the trick

```bash
sudo apt-get -y install software-properties-common
sudo apt-key adv --keyserver keyserver.ubuntu.com --recv-keys E298A3A825C0D65DFD57CBB651716619E084DAB9
sudo add-apt-repository 'deb [arch=amd64,i386] https://cran.rstudio.com/bin/linux/ubuntu xenial/'
sudo apt-get update
sudo apt-get install virtualenv libgdal-dev libnetcdf-dev libnetcdf11 libproj-dev python-dev libgdal1-dev gdal-bin virtualenv python-pip python-gdal libnetcdf-dev libudunits2-dev libcairo2-dev libxt-dev mosh r-base
virtualenv venv
. ./venv/bin/activate
pip install numpy
CPLUS_INCLUDE_PATH=/usr/include/gdal C_INCLUDE_PATH=/usr/include/gdal pip install GDAL==1.11.2 --no-binary GDAL
pip install -e .
```

This will install all the required libraries in a virtual environment
(so you can keep python packages for different project separate).

Windows (or Mac) with Anaconda
------------------------------

The easiest way to install the code on Windows is to use
[Anaconda](https://www.anaconda.com/) (or miniconda) and
[git](https://git-scm.com/download/win).  If they are not already
installed on your system, follow the instructions in the Download page.

To follow this instructions, on Windows open an Anaconda prompt (should
be in the start menu if Anaconda was installed properly).  On macOS open
a terminal.  Type the commands below into the window you just opened.

Once you have `conda` installed first define which channels to use.  Make
sure the channels are listed with the following priority

1.  conda-forge
2.  r
3.  defaults

I've run into problems when conda decides to mix packages from different
channels.  I solved this problem by making conda-forge the highest
priority channel since it has the largest selection of packages---hence
better chance of solving the dependency quagmire.  Adding a new channel
will make it the highest priority, so add them in reverse order.

```bash
conda config --add channels defaults
conda config --add channels r
conda config --add channels conda-forge
```

The next step is to clone the repo using git.  Unfortunately because of
the way things work on Windows you may need to switch back and forth
between the git window and the conda window.  Use the git window (shell)
to clone the repo (on macOS use the same terminal).  If you are using
(Github Desktop)[https://desktop.github.com] clone the repo and then
`cd` to the folder of the repo.

```bash
git clone https://github.com/NaturalHistoryMuseum/raster-project
```

Go back to the conda window and create and activate a new environment
for your projections.  Use `cd` to go to the repo you just checked out.

```bash
conda env create -n gis python=3.6 --file environment.yml
activate gis # For Windows

# source activate gis # For macOS
```

The last step is to use `pip` to install the projections package.

```bash
pip install -e .
```

The `-e` flag tells `pip` to make the package editable. If you edit the
code the changes will get picked up automatically. You only need to
re-run this step if you add a new entry point.

That's it. Don't forget that to run projections you use the **conda**
window but to use `git` use the **git** window.

Docker
======

**This is an altenative installation method.  If you can't install using
conda, try using docker.**

This repo contains a Dockerfile which you can use to build a docker
image for generating projections.  The image is built using
[jupyter/datascience-notebook](https://hub.docker.com/r/jupyter/datascience-notebook/)
as a base and therefore has the jupyter notebook server installed with
support for python3, R, and Julia.  In addition it contains many packages
useful for fitting models so you can do both model fitting and
projections in the same environment (but you don't have to).

The advantage of using docker is that anyone should be able to download
(`pull` in docker-lingo) the image and get started using the code right
away.  All the packages are already installed and ready to go so you
don't need to install anything.

Using Docker
------------
Use `docker pull` to download the image on a different computer. Once
the image is ready use docker run to run it

```bash
docker run --rm -it ricardog/project-notebook -v
/path/to/data/folder:/data -v /path/to/output/folder:/out -e
GRANT_SUDO=yes -p 8888:8888 --user root  
```

It will print a URL you can use to access the notebook server. From
there you can run or create notebooks and access the console. Notebooks
can be in python, R, or Julia.

When using [docker
toolbox](https://www.docker.com/products/docker-toolbox) (instead of
[docker for windows](https://www.docker.com/docker-windows) or [docker
for mac](https://www.docker.com/docker-mac)) you will need to increase
the resources of the default VM. See this
[page](https://github.com/crops/docker-win-mac-docs/wiki/Windows-Instructions-(Docker-Toolbox)#change-default-vm-settings)
for instructions (see the section title "Change default vm settings").
You will need to choose how much memory (RAM) and CPU to allocate. This
depends on how "big" the computer is and how big are the projections you
want to run. You don't need to change the size of the disk since the
projections place output files in a shared folder (`/out`).

If you use the existing scripts to generate projections, they will write
output files to `/out`, which is a shared folder between the container
and the host computer.  You specify which folder to use when running the
contains (see the `-v` options above).

When you are done, simply press Ctrl-C in the window where the container
started and it will be destroyed and removed.

Build
-----
**Only follow this steps to build a new version of the image.  See steps
above if you want to generate projections.**

Assuming you have docker toolbox or docker installed run

```bash
docker build . -t ricardog/project-notebook
```

If the build succeeds it is a good idea to verify all the packages
installed correctly (or at least verify some troublesome ones installed
correctly). In particular, I've had problem with the conda dependency
calculation decides to install libgdal 2.2.\* when both fiona and
rasterio are pinned to libgdal 2.1.\*. The way I worked around this for
now was to add an explicit dependency on libgdal 2.1.\*. This seems to
make conda do the "right thing".

If you are satisfied with the container, [push it to docker
hub](https://docs.docker.com/docker-cloud/builds/push-images/) with

```bash
docker push ricardog/project-notebook
```

See the inked instructions for more details. I am not certain whether
anyone other than me (ricardog) can push to that image or not but we
will find out when someone tries.


Model building
==============

I wrote these notes early on as I started looking through Tim's code.
They are not relevant to using the code.

- Build a species richness model:
  depends on

    - Human population density (log)
    - Distance to a road (log)
    - Land-use type
    - SS, SSB, SSBS

- Build a (log of) total abundance model:
  depends on

    - Land-use intensity
    - Human population density (log)
    - Land-use type
    - SS, SSB

- Build a land-use intensity model:
  This model is required because we assume land-use intensity data is
  not directly available or it is not consistent with that used for
  building the total abundance model. So the pipeline calculates the
  land-use intensity using other factors and then uses the intensity
  for predicting abundance.

  The model depends on:

  - Land-use type (log + 1)
  - Human population density (log + 1)
  - UN subregion

- Build compositional similarity model:
  **OLD**. This model predicts compositional similarity and is used to
  compute the Biota Intactness Index (BII).
