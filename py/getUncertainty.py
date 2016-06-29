'''
getUncertainty.py

input: full summary csv

output: melted summary csv w/ median, min, & max calcs

'''
import sys, os
import numpy as np
from lthacks import *

def main(summaryFile):

	#define output filename	
	uncertaintyFile = os.path.splitext(summaryFile)[0] + "_uncertainty.csv"
	
	#extract summary data
	summaryData = csvToArray(summaryFile)
	
	#get list of years & agents
	years = np.unique(summaryData['YEAR'])
	agents = np.unique(summaryData['AGENT'])
	#agentCodes = np.unique(summaryData['AGENT_CODE'])
	
	#create an ordered agentCodes list
	agentCodes = []
	for a in agents:
		code = summaryData[summaryData["AGENT"] == a]["AGENT_CODE"][0]
		agentCodes.append(code)
	
	#define uncertainty fields to calculate
	uncertaintyHeaders = ["AGENT_CODE", "AGENT", "YEAR", "MEDIAN DELTABIO KG/HA", 
						  "MAX DELTABIO KG/HA", "MIN DELTABIO KG/HA"]
	uncertaintyHeaderDtypes = [(i, 'a32') for i in uncertaintyHeaders]
	uncertaintyData = np.zeros(years.size*agents.size, dtype=uncertaintyHeaderDtypes)
	
	uncertaintyData["AGENT_CODE"] = np.repeat(agentCodes, len(years))
	uncertaintyData["AGENT"] = np.repeat(agents, len(years))
	uncertaintyData["YEAR"] = np.tile(years, len(agents))
	
	#loop through agents & years + fille in median, min, & max deltabio 
	#from summary table data
	for ind,i in enumerate(uncertaintyData):
	
		agent = i["AGENT_CODE"]
		year = i["YEAR"]
		
		print "\nWorking on agent: ", agent, " and year: ", year, " ..."

		rows = summaryData[(summaryData["AGENT_CODE"] == int(agent)) & (summaryData["YEAR"] == int(year))]
			   
		uncertaintyData[ind]["MEDIAN DELTABIO KG/HA"] = np.median(rows["DELTABIO_TOTAL"])
		uncertaintyData[ind]["MAX DELTABIO KG/HA"] = np.max(rows["DELTABIO_TOTAL"])
		uncertaintyData[ind]["MIN DELTABIO KG/HA"] = np.min(rows["DELTABIO_TOTAL"])
		
	#write uncertainty file
	arrayToCsv(uncertaintyData, uncertaintyFile)
	
	#write metadata file
	createMetadata(sys.argv, uncertaintyFile, description="This is a summary table of \
	delta biomass data by change agent containing median, max & min values of biomass \
	flavors.")
		
	print("\n PROCESS COMPLETE!")
	
	

if __name__ == '__main__':
	args = sys.argv
	sys.exit(main(args[1]))
	
