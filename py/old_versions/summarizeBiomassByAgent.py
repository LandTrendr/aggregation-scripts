'''
summarizeBiomassByAgent.py
Creates summary CSV files containing yearly total change in biomass values for each change agent. 

Author: Tara Larrue (tlarrue2991@gmail.com)

Inputs:
	- model region
	- crm/jenkins

Outputs:
	- csv with biomass diff per year by change agent for every biomass biomass source 
	- csv with median biomass diff per year by change agent

Usage: python summarizeBiomassByAgent.py [modelregion] [crm/jenk] [key_filename] [map_filename]
Example: python summarizeBiomassByAgent mr224 jenk agent_key_reduced.txt mr224_yearly_change_agents_reduced.bsq
'''
import os, sys, glob, gdal
import numpy as np
from lthacks import *
import intersectMask as im

LAST_COMMIT = getLastCommit(os.path.abspath(__file__))
AGGREGATION_SCRIPTS_PATH = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
AGGREGATION_PARAMETERS_PATH = os.path.join(AGGREGATION_SCRIPTS_PATH, "parameters")
AGGREGATION_PATH = os.path.dirname(AGGREGATION_SCRIPTS_PATH)

def biomass_to_agentband(bandnum):
	return bandnum + 6

def txtToDict(txtfile):
	print txtfile
	txt = open(txtfile, 'r')

	dictionary = {}
	for line in txt:
		comps = line.split(":")
		dictionary[int(comps[0])] = comps[1].strip()

	return dictionary

def main(modelregion, biotype, keyfilename, mapfilename):

	biotype = biotype.lower()
	modelregion = modelregion.lower()

	#define agent key parameters as dictionary
	agent_key_path = os.path.join(AGGREGATION_PARAMETERS_PATH, modelregion, keyfilename)
	agents = txtToDict(agent_key_path)
	print "\nSummarizing using agents: \n", agents, "\n..." 

	#define agent aggregation map
	agent_map = os.path.join(AGGREGATION_PATH, "outputs", modelregion, "change_agent_maps", mapfilename)

	#define list of deltaBiomass maps & find # of bands
	biomass_maps_path = os.path.join(AGGREGATION_PATH, "outputs", modelregion, "biomass_maps")
	biomass_maps = glob.glob(os.path.join(biomass_maps_path, "*"+biotype+"*.bsq"))
	biomap1 = biomass_maps[0]
	ds = gdal.Open(biomap1)
	numbands = ds.RasterCount
	bands = range(2, numbands+1)
	del ds
	print "\nand maps: \n", biomass_maps, "\n..."
	print "\nwith bands: ", bands

	#loop through years & agents & populate CSV
	outputfile = '/vol/v1/proj/aggregation/outputs/mr224/summary_tables/{model}_{type}_{key}_deltabiomass_summary.csv'.format(model=modelregion, type=biotype, key=os.path.splitext(keyfilename)[0])
	if not os.path.exists(os.path.dirname(outputfile)):
		os.makedirs(os.path.dirname(outputfile))
	summary_csv = open(outputfile, 'w')
	print "Created New Summary File: ", outputfile
	
	summary_csv.write('BIOMASS_SOURCE, AGENT_CODE, AGENT, YEAR, DELTABIO_NEGATIVE, DELTABIO_POSITIVE, DELTABIO_TOTAL, DELTABIO_MAGNITUDE\n')
	for m in biomass_maps: 
		for b in bands:
			print "\nWorking on map '", m, "' band ", b, " ..."
			for c,a in agents.iteritems():

				outBandArray, finalTransform, projection, driver, nodata, datatype = im.maskAsArray(m, agent_map, src_band=b, msk_band=biomass_to_agentband(b), msk_value=c)
				total_change = np.sum(outBandArray)
				magnitude_change = np.sum(np.absolute(outBandArray))
				pos = (magnitude_change+total_change)/2
				neg = magnitude_change - pos

				bionames = m.split("_")
				start = bionames.index("delta")
				end = bionames.index(modelregion)
				biomass_flavor = "_".join(bionames[start:end]).upper()
				line = '{biomass},{code},{agent},{year},{neg},{pos},{total},{change}\n'
				line = line.format(biomass=biomass_flavor,code=c,agent=a,year=b+1989,neg=-neg,pos=pos,total=total_change,change=magnitude_change)
				summary_csv.write(line)

	summary_csv.close()
	print "\nDone extracting summary values."

	# write metadata file
	createMetadata(sys.argv, outputfile, description="This is a summary table of delta biomass data by change agent before melt.", lastCommit=LAST_COMMIT)

	#melt table w/ medians : YEAR | AGENT | deltaBio total | deltabio mag | deltabio neg | deltabio pos
	print "\nMelting summary values for median delta biomass values...."
	outputfile_melt = os.path.splitext(outputfile)[0] + "_median.csv"
	sumdata = csvToArray(outputfile)

	headers = ["AGENT_CODE", "AGENT", "YEAR", "DELTABIO_TOTAL", "DELTABIO_MAGNITUDE", "DELTABIO_NEGATIVE", "DELTABIO_POSITIVE"]
	dtypes = [(i,'a32') for i in headers]
	meltdata = np.zeros(len(bands)*len(agents), dtype=dtypes)

	meltdata["AGENT_CODE"] = np.repeat(agents.keys(), len(bands))
	meltdata["AGENT"] = np.repeat(agents.values(), len(bands))
	meltdata["YEAR"] = np.tile([i+1989 for i in bands], len(agents))
	for ind,i in enumerate(meltdata):
		agent = i["AGENT_CODE"]
		year = i["YEAR"]
		print "\nWorking on agent: ", agent, " and year: ", year, " ..."

		rows = sumdata[(sumdata["AGENT_CODE"] == int(agent)) & (sumdata["YEAR"] == int(year))]
		meltdata[ind]["DELTABIO_TOTAL"] = np.median(rows["DELTABIO_TOTAL"])
		meltdata[ind]["DELTABIO_MAGNITUDE"] = np.median(rows["DELTABIO_MAGNITUDE"])
		meltdata[ind]["DELTABIO_NEGATIVE"] = np.median(rows["DELTABIO_NEGATIVE"])
		meltdata[ind]["DELTABIO_POSITIVE"] = np.median(rows["DELTABIO_POSITIVE"])

	#write summary file
	arrayToCsv(meltdata, outputfile_melt)

	#write metadata file
	createMetadata(sys.argv, outputfile_melt, description="This is a summary table of delta biomass data by change agent containing median values of biomass flavors.", lastCommit=LAST_COMMIT)

	print "\n PROCESS COMPLETE!"


if __name__ == '__main__':
	args = sys.argv
	sys.exit(main(args[1], args[2], args[3], args[4]))
