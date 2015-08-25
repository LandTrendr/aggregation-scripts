'''Converting a 28 band raster to a 29 band raster for years 1984-2012
Creted in order to fix agent_aggregation map for MR224.'''

import gdal, os, sys, shutil
import numpy as np
from gdalconst import *
import intersectMask as im
from validation_funs import *
from tempfile import mkstemp

CREATED = "08/25/2015" 

def edithdr(path, start):
	'''Assigns years as band names'''
	hdrPath = path.replace('bsq', 'hdr')
	#open hdr file
	hdr = open(hdrPath, 'r')
	#create new tmp file
	tmpPath = '{0}.tmp.txt'.format(os.path.basename(hdrPath))
	tmp, tmpPath = mkstemp()

	new_file = open(tmpPath, 'w')

	#replace band names in file
	band = 0
	year = start-1
	for line in hdr:
		if not line.startswith('Band'):
			new_file.write(line)
		else:
			band += 1
			year += 1
			oldline = 'Band {0}'.format(band)
			new_file.write(line.replace(oldline, str(year)))

	#close files
	new_file.close()
	os.close(tmp)
	hdr.close()
	#replace old hdr file
	os.remove(hdrPath)
	shutil.move(tmpPath, hdrPath)

def main(inputfile, outputfile):
	#open raster, count bands
	ds = gdal.Open(inputfile, GA_Update)
	numbands = ds.RasterCount
	print "Starting number of bands: ", numbands

	#get projection, driver & extent info
	projection = ds.GetProjection()
	driver = ds.GetDriver()
	transform = ds.GetGeoTransform()
	cols = ds.RasterXSize
	rows = ds.RasterYSize

	#get bands & datatype
	outbands = []
	for b in range(1, numbands+1):
		band = ds.GetRasterBand(b)
		if b == 1:
			dt = band.DataType
			nodata = band.GetNoDataValue()
		outband = band.ReadAsArray()
		outbands.append(outband)

	outbands.insert(0, np.zeros((rows, cols)))

	im.saveArrayAsRaster_multiband(outbands, transform, projection, driver, outputfile, dt, nodata=nodata)

	edithdr(outputfile, 1984)

	desc = "This is a transformation of MR224 attribution map so it has 29 bands representing years 1984-2012"
	createMetadata(sys.argv, outputfile, description=desc, lastCommit=CREATED)


if __name__ == '__main__':
	args = sys.argv
	sys.exit(main(args[1], args[2])) #input file name, output file name