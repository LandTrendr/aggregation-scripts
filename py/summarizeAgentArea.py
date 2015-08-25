'''
summarizeAgentArea.py
Creates summary CSV file containing yearly area in hectares affected by agent by year. 

Author: Tara Larrue (tlarrue2991@gmail.com)

Inputs:
	- model region

Outputs:
	- csv with amt of hectares affected by agent by year

Usage: python summarizeAgentArea.py [modelregion]
Example: python summarizeAgentArea.py mr224
'''

import os, sys, glob, gdal
import numpy as np
from validation_funs import *
from collections import OrderedDict

AGGREGATION_SCRIPTS_PATH = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
AGGREGATION_PARAMETERS_PATH = os.path.join(AGGREGATION_SCRIPTS_PATH, "parameters")
AGGREGATION_PATH = os.path.dirname(AGGREGATION_SCRIPTS_PATH)

def hdrbandsToDict(hdrfile):
	#string: int
	hdr = open(hdrfile, 'r')

	dictionary = {}
	bands = False
	bandnum = 1
	for line txt:
		if line = "band names = {":
			bands = True 

		if bands:
			year = line.strip(" ")
			year = year.strip(",")
			year = year.strip("}")
			if len(year) == 4:
				dictionary[year, bandnum]
				bandnum += 1

	hdr.close()

	return dictionary

def txtToDict(txtfile):
	txt = open(txtfile, 'r')

	dictionary = {}
	for line in txt:
		comps = line.split(":")
		dictionary[int(comps[0])] = comps[1].strip()

	txt.close()

	return dictionary

def main(modelregion):

	modelregion = modelregion.lower()

	#define agent key parameters as dictionary
	agent_key_path = os.path.join(AGGREGATION_PARAMETERS_PATH, modelregion, "agent_key.txt")
	agents = txtToDict(agent_key_path)
	print "\nSummarizing using agents: \n", agents, "\n..." 

	#define agent aggregation map
	agent_map = os.path.join(AGGREGATION_PATH, "outputs", modelregion, "change_agent_maps", modelregion+"_agent_aggregation.bsq")

	#define new structured array to hold summary table
	years = range(1990,2011)
	dtypes = [("AGENT_CODE", 'i4'), ("AGENT_NAME", 'a25')] + [(str(y),'i4') for y in years]
	summary = np.zeros(len(agents), dtype=dtypes)

	agents = OrderedDict(agents)
	summary["AGENT_CODE"] = agents.keys()
	summary["AGENT_NAME"] = agents.values()

	#open agent map
	ds = gdal.Open(agent_map)
	bands = hdrbandsToDict(agentmap.replace('bsq', 'hdr'))
	print "\nbands = ", bands

	for y_ind, y in enumerate([str(i) for i in years]): 
		print "Working on year: ", y, " ..."
		for a_ind,a in enumerate(agents):
			#get raster band
			agent_band = ds.GetRasterBand(bands[y])
			agent_band_array = agent_band.ReadAsArray()

			#make mask of desired agent pixels
			outband = (agent_band_array == a)

			#calc amt of hectares
			numpixels = np.sum(outband).astype('float')
			meters_squared = numpixels * 30. * 30.
			hectares = meters_squared/10000. 

			#insert into summary table
			summary[y][a_ind] = hectares

	#define output path & save summary table
	outputfile = os.path.join(AGGREGATION_PATH, "outputs", modelregion, "summary_tables", "mr224_agent_hectares_summary.csv")
	arrayToCsv(summary, outputfile)


if __name__ == '__main__':
	args = sys.argv
	sys.exit(main(args[1]))