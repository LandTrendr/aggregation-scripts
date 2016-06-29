'''
Convert fitted & vertyrs mosaic in to a fast/slow/0 raster.

slow = 30
fast = 35
'''
import os, sys, gdal
import numpy as np
from gdalconst import *
from intersectMask import *
from lthacks import *

LAST_UPDATED = "01/26/2016"
SLOW_VAL = 30
FAST_VAL = 35
GROW_VAL = 50

def main(fittedPath, vertyrsPath, outputPath, disturbanceVal, growthVal):
	
	dval = int(disturbanceVal)
	gval = int(growthVal)
	
	#open both datasets
	fittedDS = gdal.Open(fittedPath, GA_ReadOnly)
	vertyrsDS = gdal.Open(vertyrsPath, GA_ReadOnly)
	
	#get save info
	projection = fittedDS.GetProjection()
	transform = fittedDS.GetGeoTransform()
	driver = fittedDS.GetDriver()
	numBands = fittedDS.RasterCount
	cols = fittedDS.RasterXSize
	rows = fittedDS.RasterYSize
	
	#loop thru bands & replace values
	outData = [np.zeros((rows, cols)) for i in range(numBands)]	
	
	for b in range(1, numBands+1):
		print "\nWorking on Band: ", b, " ..."
		
		#get band data
		fittedBand = fittedDS.GetRasterBand(b)
		fittedData = fittedBand.ReadAsArray()
		
		vertyrsBand = vertyrsDS.GetRasterBand(b)
		vertyrsData = vertyrsBand.ReadAsArray()
		
		#define slow pixels (> 3 yrs duration)
		disturbedPixels = (fittedData == dval)
		
		slowPixels = np.logical_and( disturbedPixels , (vertyrsData>3) ) 
		outData[b-1][slowPixels] = SLOW_VAL
		
		#define fast pixels (<= 3 yrs duration)
		fastPixels = np.logical_and( disturbedPixels , (vertyrsData<=3) ) 
		outData[b-1][fastPixels] = FAST_VAL
		
		#define growth pixels 
		growthPixels = (fittedData==gval)
		outData[b-1][growthPixels] = GROW_VAL
		
		print np.sum(disturbedPixels), np.sum(slowPixels), np.sum(fastPixels), np.sum(growthPixels)
		
	#save new arrays as a (multiband) raster
	saveArrayAsRaster_multiband(outData, transform, projection, driver, outputPath, 3)
	
	#save a meta file
	createMetadata(sys.argv, outputPath, lastCommit=LAST_UPDATED)
	
if __name__ == '__main__':
	args = sys.argv
	sys.exit(main(args[1], args[2], args[3], args[4], args[5]))