#!/usr/bin/env python

import gdal
import sys

def error(msg, code=1):
  print "Error: %s" % msg
  sys.exit(1)
  
if len(sys.argv) < 2:
  error("please specify a raster file")

src_path = sys.argv[1]
src_band = 1
src_ds = gdal.Open(src_path)
if src_ds is None:
  error("could not open source raster '%s'" % src_path)
sband = src_ds.GetRasterBand(src_band)
block_sizes = sband.GetBlockSize()
transform = src_ds.GetGeoTransform()
src_x_offset = src_y_offset = 0

x_size = src_ds.RasterXSize * 2
y_size = src_ds.RasterYSize * 2
drv = gdal.GetDriverByName("VRT")
vrt = drv.Create("test.vrt", x_size, y_size, 0)
vrt.SetGeoTransform([transform[0], transform[1]/2.0, transform[2],
                     transform[3], transform[4], transform[5]/2.0])
vrt.SetProjection(src_ds.GetProjection())

vrt.AddBand(gdal.GDT_Float32)
band = vrt.GetRasterBand(1)
dst_x_offset = src_x_offset
dst_y_offset = src_y_offset

complex_source = '''
<ComplexSource>
  <SourceFilename relativeToVRT="1">%s</SourceFilename>
  <SourceBand>%i</SourceBand>
  <SourceProperties RasterXSize="%i" RasterYSize="%i"
                    DataType="Real" BlockXSize="%i" BlockYSize="%i"/>
  <SrcRect xOff="%i" yOff="%i" xSize="%i" ySize="%i"/>
  <DstRect xOff="%i" yOff="%i" xSize="%i" ySize="%i"/>
  <NODATA>%s</NODATA>
</ComplexSource>
''' % (src_path, src_band, src_ds.RasterXSize, src_ds.RasterYSize,
       block_sizes[0], block_sizes[1],
       src_x_offset, src_y_offset, src_ds.RasterXSize, src_ds.RasterYSize,
       dst_x_offset, dst_y_offset, x_size, y_size, sband.GetNoDataValue())
band.SetMetadataItem("source_0", complex_source, "new_vrt_sources")
band.SetMetadataItem("NoDataValue", sband.GetNoDataValue())

