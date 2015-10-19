'''
script to create a difference raster stack
'''
SCRIPT_LAST_UPDATED = "09/22/2015"

import sys, gdal
from gdalconst import *
import intersectMask as im
from lthacks import *

def main(inputStack, outputPath):
	#open raster & get info
	ds = gdal.Open(inputStack, GA_ReadOnly)
	numBands = ds.RasterCount
	transform = ds.GetGeoTransform()
	projection = ds.GetProjection()
	driver = ds.GetDriver()
	
	#loop thru bands & calc new bands
	outbands = []
	for b in range(1,numBands+1):
		print b
		curr_band = ds.GetRasterBand(b)
		curr_band_array = curr_band.ReadAsArray()
		#READ AS ARRAY
		if b != 1:
			diff = curr_band_array - last_band_array
			new_band = (diff < 0) * 42 #other disturbance
			new_band = new_band + ((diff > 0) * 52) #other growth
			outbands.append(new_band)
			last_band_array = curr_band_array
		else:
			new_band = np.zeros(curr_band_array.shape)
			outbands.append(new_band)
			datatype = curr_band.DataType
			last_band_array = curr_band_array
			
		print np.max(curr_band_array)
		print curr_band_array.shape
		print outbands
		print len(outbands)
	
	print outbands[0]
	print outbands[0].shape
	#save raster
	im.saveArrayAsRaster_multiband(outbands, transform, projection, driver, outputPath, datatype)
	
	#save metadata
	desc = "MR224 difference raster using NBR fitted images used as an agent source map in aggregation workflow."
	createMetadata(sys.argv, outputPath, description=desc, lastCommit=SCRIPT_LAST_UPDATED)
			

if __name__ == '__main__':
	inputStack = sys.argv[1]
	outputPath = sys.argv[2]
	main(inputStack, outputPath)