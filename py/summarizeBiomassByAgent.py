'''
summarizeBiomassByAgent.py

Creates summary CSV files containing yearly total change in biomass values for each change agent. 

Author: Tara Larrue (tlarrue2991@gmail.com)

Inputs:
	- path to key file
	- path to map file
	- biomass directory
	- allometric (crm/jenk)
	- output path for full summary csv
	- OPTIONAL: path to graph order file

Outputs: 
	- csv with biomass diff per year by change agent for every biomass biomass source 
	- csv with median biomass diff per year by change agent
	
Usage:
python summarizeBiomassByAgent.py [keyPath] [mapPath] [bioDir] [allometric] [outputPath] [graphOrderPath]
'''

import os, sys, glob, gdal
from gdalconst import *
import numpy as np
from lthacks import *

LAST_UPDATED = "02/02/2016"

YEARS = range(1991,2011) #1990-2010
BIOBANDS = {i[0]: i[1] for i in zip(YEARS, range(2,22))}
AGENTBANDS = {i[0]: i[1] for i in zip(YEARS, range(8,28))} 

def txtToDict(txtfile):
	print txtfile
	txt = open(txtfile, 'r')

	dictionary = {}
	for line in txt:
		comps = line.split(":")
		dictionary[int(comps[0])] = comps[1].strip()

	return dictionary
	
def main(keyPath, mapPath, bioDir, allometric, outputPath, graphOrderPath=None):
	
	#find delta biomass files
	biofiles = glob.glob(os.path.join(bioDir, "*"+allometric+"*.bsq"))
	
	#define agent key parameters as dictionary
	agents = txtToDict(keyPath)
	
	#define graph stacking order
	if graphOrderPath: graphOrder = txtToDict(graphOrderPath)
	
	if not os.path.exists(outputPath):
	
		#open agent map
		dsAgent = gdal.Open(mapPath, GA_ReadOnly)
	
		#create CSV listing each biomass source separately
		headers = ['BIOMASS_SOURCE', 'AGENT_CODE', 'AGENT', 'YEAR', 'DELTABIO_NEGATIVE', 
					'DELTABIO_POSITIVE', 'DELTABIO_TOTAL', 'DELTABIO_MAGNITUDE']
		dtypes = [(i,'a32') for i in headers]
		alldata = np.zeros(len(biofiles)*len(agents)*len(YEARS), dtype=dtypes)
	
		#loop thru maps, years & agents to fill out csv data
		row = 0
		for file in biofiles:
	
			dsBio = gdal.Open(file, GA_ReadOnly)
		
			for year,bioband in BIOBANDS.iteritems():
			
				print "\nWorking on map '", file, "' year ", year, " ..."
			
				bandAgent = dsAgent.GetRasterBand(AGENTBANDS[year])
				dataAgent = bandAgent.ReadAsArray()
			
				bandBio = dsBio.GetRasterBand(bioband)
				dataBio = bandBio.ReadAsArray()
			
				for code,agent in agents.iteritems():
			
					alldata[row]['BIOMASS_SOURCE'] = os.path.splitext(os.path.basename(file))[0]
					alldata[row]['AGENT_CODE'] = code
					alldata[row]['AGENT'] = agent
					alldata[row]['YEAR'] = year
				
					agentPixels = (dataAgent == int(code)) #bool array 
				
					bioForAgent = dataBio[agentPixels] #data array
				
					total = np.sum(bioForAgent)
					mag = np.sum(np.absolute(bioForAgent))
					pos = (mag+total)/2
					neg = mag - pos
				
					alldata[row]['DELTABIO_NEGATIVE'] = neg
					alldata[row]['DELTABIO_POSITIVE'] = pos
					alldata[row]['DELTABIO_TOTAL'] = total
					alldata[row]['DELTABIO_MAGNITUDE'] = mag
			
					row += 1
				
			del dsBio
		
		#save csv
		arrayToCsv(alldata, outputPath)
		
		# write metadata file
		desc = "This is a summary table of delta biomass data by change agent before melt."
		createMetadata(sys.argv, outputPath, description=desc, lastCommit=LAST_UPDATED)
		
	else:
	
		print "\nOutput file already exists. Skipping to melt.."
		
		alldata = csvToArray(outputPath)
			
	#melt table with median values
	headers = ["AGENT_CODE", "AGENT", "YEAR", "DELTABIO_TOTAL", "DELTABIO_MAGNITUDE", 
	           "DELTABIO_NEGATIVE", "DELTABIO_POSITIVE", "ORDER"]
	dtypes = [(i,'a32') for i in headers]
	meltdata = np.zeros(len(YEARS)*len(agents), dtype=dtypes)
	
	meltdata["AGENT_CODE"] = np.repeat(agents.keys(), len(YEARS))
	meltdata["AGENT"] = np.repeat(agents.values(), len(YEARS))
	meltdata["YEAR"] = np.tile(YEARS, len(agents))
	
	for ind,i in enumerate(meltdata):
		agent = i["AGENT_CODE"]
		year = i["YEAR"]
		print "\nWorking on agent: ", agent, " and year: ", year, " ..."

		rows = alldata[(alldata["AGENT_CODE"] == int(agent)) & (alldata["YEAR"] == int(year))]
		meltdata[ind]["DELTABIO_TOTAL"] = np.median([int(r) for r in rows["DELTABIO_TOTAL"]])
		meltdata[ind]["DELTABIO_MAGNITUDE"] = np.median([int(r) for r in rows["DELTABIO_MAGNITUDE"]])
		meltdata[ind]["DELTABIO_NEGATIVE"] = np.median([int(r) for r in rows["DELTABIO_NEGATIVE"]])
		meltdata[ind]["DELTABIO_POSITIVE"] = np.median([int(r) for r in rows["DELTABIO_POSITIVE"]])
		
		if graphOrderPath: meltdata[ind]["ORDER"] = graphOrder[agent]
	
	
	#save csv
	outputPath_melt = os.path.splitext(outputPath)[0] + "_median.csv"
	arrayToCsv(meltdata, outputPath_melt)

	#write metadata file
	desc = "This is a summary table of delta biomass data by change agent containing median values of biomass flavors."
	createMetadata(sys.argv, outputPath_melt, description=desc, lastCommit=LAST_UPDATED)

	print "\n PROCESS COMPLETE!"
	
if __name__ == '__main__':
	args = sys.argv
	if len(args) == 6:
		sys.exit(main(args[1], args[2], args[3], args[4], args[5]))
	elif len(args) == 7:
		sys.exit(main(args[1], args[2], args[3], args[4], args[5], args[6]))
	else:
		usage = "python summarizeBiomassByAgent.py [keyPath] [mapPath] [bioDir] [allometric] [outputPath] ([graphOrderPath])"
		sys.exit("Invalid number of arguments.\nUsage: " + usage)
	
	