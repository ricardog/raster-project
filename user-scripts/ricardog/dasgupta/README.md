* Dasgupta Report Projection

** Introduction

This folder holds the scripts we used to generate PREDICTS projections
for the Dasgupta report.

There are three types of scripts.  First, scripts to pre-process or
validate the data we received from Vidid.  Second, scripts to run the
projections.  Third, scripts to summarize and report the results. 

** Setup

These script have to be run once for each new scenarios we receive from
Vivid.  Some scripts *need* to be run at least once before running
projections and some *should* be run to validate the data. 

*** Mask Generation

We require a number of masks to split the world into tempeate forest,
tropical forest, and non-forested regions (which is how Adriana split
the models).  I wrote a simple script to generate one of those masks
and the rest I generate with *gdal_translate* from the Terrestrial
Ecosystems of the World (TEOW) shapefile.

** Run

** Summary

