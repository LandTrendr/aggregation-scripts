#!/usr/bin/env python

'''
Replace Pixel Value.

replacePixelValue.py <input_raster> <output_raster> <operators> <in_values> <out_values>
replacePixelValue.py -h | --help

Options:
  -h --help					Show this screen.
  --multiple_list=<ml>		Path to text file containing condition key (each line - "operator:in_value:out_value").
  --meta=<meta> 			Additional notes for meta.txt file.
'''

import sys, os, gdal
import numpy as np
from gdalconst import *
from lthacks.lthacks import *
from lthacks.intersectMask import *
import docopt


def readMultList(txtfile):
	
	txt = open(txtfile, 'r')

	replaceList = []
	for line in txt:
		comps = line.split(":")
		comps = [i.strip().lower() for i in comps]
		
		if len(comps) != 3:
			sys.exit("Line not understood: " + line)
			
		replaceList.append({'operator': getCondition(comps[0]),
							'invalue': float(comps[1]),
							'outvalue': float(comps[2])})

	return replaceList

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
		raise NameError("Operator input not understood:" + astring)
		
	return func


def main(input, output, operators, in_values, out_values, meta=None):
	
	#get replacement info
	operators = operators.split(",")
	in_values = in_values.split(",")
	out_values = out_values.split(",")
	
	replacements = zip(operators, in_values, out_values)
	replace_list = []
	for replacement in replacements:
		try:
			conditionFunc = getCondition(replacement[0])
			replaceList.append({'operator': conditionFunc,
								'invalue': float(replacement[1]),
								'outvalue': float(replacement[2])})
		except NameError:
			sys.exit("ERROR: Input not understood: ", replacement)
	
	#open raster & get info
	ds = gdal.Open(input, GA_ReadOnly)
	projection = ds.GetProjection()
	transform = ds.GetGeoTransform()
	driver = ds.GetDriver()
	numbands = ds.RasterCount
	
	#initialize output
	outdata = [0]*numbands
	
	#loop thru bands & replace values
	for i,item in enumerate(replace_list):
	
		print "\nWorking on converting from ", item['invalue'], " to ", item['outvalue'], " ..."
	
		for b,bandnum in enumerate(range(1, numbands+1)):
	
			#determine if this is the first replacement
			if i == 0:	
				band = ds.GetRasterBand(bandnum)
				if b == 0:
					dt = band.DataType
		
				banddata = band.ReadAsArray()
			
			else:
				banddata = outdata[bandnum]
	
			#locate pixels to replace
			bools = item['operator'](banddata, item['invalue'])
	
			#replace those pixels with specified out value
			banddata[bools] = item['outvalue']
	
			#save band
			outdata[ind] = banddata
		
	#save new arrays as a (multiband) raster
	saveArrayAsRaster_multiband(outdata, transform, projection, driver, output, dt)
	
	#save a metadata file
	fullpath = os.path.abspath(__file__)
	createMetadata(sys.argv, output, description=meta, lastCommit=getLastCommit(fullpath))
	
	
if __name__ == '__main__':

    try:
        #parse arguments, use file docstring as parameter definition
        args = docopt.docopt(__doc__)

        #call main function
        main(args['<input_raster>'], args['<output_raster>'], args['<operators>'], 
             args['<in_values>'], args['<out_values>']), args['--meta'])

    #handle invalid options
    except docopt.DocoptExit as e:
        print e.message
	
	