'''
Replace Value.

inputs: 
- condition_operator
- condition_value
- out_value
- in_raster_path
- out_raster_path

outputs:
- raster
'''
import sys, os, gdal
import numpy as np
from gdalconst import *
from lthacks import *
from intersectMask import *

LAST_UPDATED = "01/20/2016"

#temporary for loop
change_dict = {7:3, #road to development
			   9:0, #false change to no agent
			   18:0, #N/A to no agent
			   10:35, #unknown agent to Fast Disturbance
			   17:35, #other agent to Fast Disturbance
			   21:6, #MPB-29 to Insects/Disease
			   22:6, #MPB-239 to Insects/Disease
			   25:6, #WSB-29 to Insects/Disease
			   26:6, #WSB-239 to Insects/Disease
			   11:7, #Water to Natural Disturbance
			   12:7, #Wind to Natural Disturbance
			   13:7, #Avalanche-chute to Natural Disturbance
			   14:7, #Avalanche-runout to Natural Disturbance
			   15:7, #Debris Flow to Natural Disturbance
			   16:7} #Landslide to Natural Disturbance

#change_dict = {41:40}

def getCondition(astring):

	if astring.strip(' ').lower() == ">":
		def func(anarray, value):
			return anarray > value
			
	elif astring.strip(' ').lower() == "<":
		def func(anarray, value):
			return anarray < value
			
	elif astring.strip(' ').lower() == "<=":
		def func(anarray, value):
			return anarray <= value
			
	elif astring.strip(' ').lower() == "=>":
		def func(anarray, value):
			return anarray >= value
			
	elif (astring.strip(' ').lower() == "=") or (astring.strip(' ').lower() == "=="):
		def func(anarray, value):
			return anarray == value
			
	else:
		print sys.exit("Operator input not understood:"+ astring)
		
	return func


def main(inputPath, outputPath, conditionOp, conditionVal, outVal):

	#get condition function from operator string
	condition = getCondition(conditionOp)
	#conditions = [getCondition(">"), getCondition("<")]
	#condvals = [0, 0]
	#outvals = [50, 45]
	
	#open raster & get info
	ds = gdal.Open(inputPath, GA_ReadOnly)
	projection = ds.GetProjection()
	transform = ds.GetGeoTransform()
	driver = ds.GetDriver()
	numBands = ds.RasterCount
	
	#loop thru bands & replace values
	newData = [0]*numBands
	
	#for condition, conditionVal, outVal in zip(conditions, condvals, outvals):
	for conditionVal, outVal in change_dict.iteritems():
	
		print "\nWorking on converting from ", conditionVal, " to ", outVal, " ..."
	
		for ind, b in enumerate(range(1, numBands+1)):
	
			if conditionVal == 7:	
				band = ds.GetRasterBand(b)
				if ind == 0:
					dt = band.DataType
		
				data = band.ReadAsArray()
			
			else:
				data = newData[ind]
	
			bools = condition(data, float(conditionVal))
	
			data[bools] = float(outVal)
	
			newData[ind] = data
		
	#save new arrays as a (multiband) raster
	saveArrayAsRaster_multiband(newData, transform, projection, driver, outputPath, dt)
	
	#save a meta file
	createMetadata(sys.argv, outputPath, lastCommit=LAST_UPDATED)
	
	
if __name__ == '__main__':
	#args = sys.argv
	#sys.exit(main(args[1], args[2], args[3], args[4], args[5]))
	inputPath = "/vol/v1/proj/aggregation/outputs/mr224/change_agent_maps/mr224_yearly_change_agents.bsq"
	outputPath = "/vol/v1/proj/aggregation/outputs/mr224/change_agent_maps/mr224_yearly_change_agents_reduced.bsq"
	conditionOp = "="
	conditionVal = ""
	outVal = ""
	sys.exit(main(inputPath, outputPath, conditionOp, conditionVal, outVal))
	
		
		
		
		