'''
vertyrs_split.py

'''

import sys, os, gdal
from gdalconst import *
from lthacks.intersectMask import *

YEARS = range(1984,2013)

def main(vertyrsPath, outputPath):

	ds = gdal.Open(vertyrsPath, GA_ReadOnly)
	numBands = ds.RasterCount #vertices bands
	cols = ds.RasterXSize
	rows = ds.RasterYSize
	transform = ds.GetGeoTransform()
	projection = ds.GetProjection()
	driver = ds.GetDriver()

	#accumulate bands into list
	print "\nAccumulating vertyrs bands..."
	allBands = []
	for b in range(1, numBands+1):
	
		band = ds.GetRasterBand(b)
		inputData = band.ReadAsArray()
		allBands.append(inputData)
		
	print "\nCalculating vertices duration..."	
	outBands = [np.zeros((rows, cols)) for i in YEARS]		
	for ind,bandData in enumerate(allBands):
		print "\n\tBand: ", ind+1
		
		if ind == 0:
			prevData = bandData
			continue
		else:
			diffData = bandData - prevData
			
			print "Min,Max:", np.max(diffData), np.min(diffData)
		
		for y in YEARS:
			print "\t\tYear: ", y 
		
			changePixels = (diffData > 0)
			print "Cond 1: ", np.sum(changePixels)
			changePixels = np.logical_and(changePixels, (bandData > y))
			print "Cond 2: ", np.sum(bandData > y)
			print "Cond 1+2: ", np.sum(changePixels)
			
			changePixels = np.logical_and(changePixels, (prevData <= y))
			print "Cond 3: ", np.sum(prevData <= y)
			print "Cond 1+2+3: ", np.sum(changePixels)
			#changePixels = np.where((diffData > 0) & (bandData > y) & (prevData <= y))
			
			#print changePixels
			outBands[y-1984][changePixels] = diffData[changePixels]
			
		prevData = bandData
	
		#integer type; save after each iteration
		saveArrayAsRaster_multiband(outBands, transform, projection, driver, outputPath, 3)
		
	createMetadata(sys.argv, outputPath, description="Yearly segment duration.")
	
	
if __name__ == '__main__':
	args = sys.argv
	sys.exit(main(args[1], args[2]))
			
			
		
		
		
		
		
		
			
		
		
		
		
		
		
		