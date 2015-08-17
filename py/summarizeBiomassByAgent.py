'''
summarizeBiomassByAgent.py
inputs:
- region
- crm/jenkins
- outputfile

outputs:
- csv with median biomass diff per year

AGENT CODE | AGENT NAME | BAND5_K1_1991
'''
import os, sys, glob
import numpy as np
from validation_funs import *
from intersectMask import *

LAST_COMMIT = getLastCommit(os.path.abspath(__file__))
AGGREGATION_SCRIPTS_PATH = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
AGGREGATION_PARAMETERS_PATH = os.path.join(AGGREGATION_SCRIPTS_PATH, "parameters")
AGGREGATION_PATH = os.path.dirname(AGGREGATION_SCRIPTS_PATH)

def biomass_to_agentband(bandnum):
	return bandnum + 6

def main(modelregion, biotype):

	biotype = biotype.lower()
	modelregion = modelregion.lower()

	#define agent key parameters as dictionary

	#define agent aggregation map
	agent_map = os.path.join(AGGREGATION_PATH, "outputs", modelregion, "change_agent_maps", modelregion+"_agent_aggregation.bsq")

	#define list of deltaBiomass maps
	biomass_maps_path = os.path.join(AGGREGATION_PATH, "outputs", modelregion, "biomass_maps")
	biomass_maps = glob.glob(os.path.join(biomass_maps_path, "*"+biotype+"*.bsq"))

	#loop through years & agents & populate CSV
	summary_csv = open('/projectnb/trenders/proj/aggregation/outputs/mr224/summary_tables/{model}_{type}_deltabiomass_summary.csv'.format(model=modelregion, type=biotype), 'w')
	if not os.path.exists(os.path.dirname(summary_csv)):
		os.makedirs(os.path.dirname(summary_csv))

	summary_csv.write('BIOMASS SOURCE, AGENT, YEAR, NEGATIVE CHANGE, POSITIVE CHANGE, TOTAL CHANGE, MAGNITUDE CHANGE\n')
	for m in biomass_maps: 
		for b in bands:
			for a in agents:

				outBandArray, finalTransform, projection, driver, nodata, datatype = maskAsArray(m, agent_map, src_band=b, msk_band=biomass_to_agentband(b), msk_value=a)
				total_change = np.sum(outBandArray)
				magnitude_change = np.sum(np.absolute(outBandArray))
	            pos = (magnitude_change+total_change)/2
	            neg = magnitude_change - pos

	            bionames = m.split("_")
	            start = bionames.index("delta")
	            end = bionames.index(modelregion)
	            biomass_flavor = "_".join(bionames[start:end]).upper()
	            line = '{biomass},{agent},{year},{neg},{pos},{total},{change}\n'.format(biomass=biomass_flavor,agent=a,year=b+1989,neg=-neg,pos=pos,total=total_change,change=magnitude_change)
	            summary_csv.write(line)

    summary_csv.close()

    #write meta data file
    createMetadata(sys.argv, summary_csv, description="This is a summary table of delta biomass data by change agent.", lastCommit=LAST_COMMIT)

if __name__ == '__main__':
    args = sys.argv
    sys.exit(main(args[1], args[2]))
