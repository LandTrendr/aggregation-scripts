'''
stackagents.py
Creates a raster image stack that identifies dominant 
change agents attributed to each pixel for each year.

Authors: Tara Larrue (tlarrue2991@gmail.com) & Jamie Perkins

Inputs: 
	- modelregion
	- outputfile path
Outputs:
	-  ENVI image stack (.bsq file type) w/ 1 band per year identifying dominant change agents
	-  metadata file

Usage: python stackagents.py [modelregion] [outputfile]
Example: python stackagents.py mr224 /projectnb/trenders/proj/aggregation/outputs/mr224/mr224_agent_aggregation.bsq
'''
import sys, os, glob, re, shutil, subprocess
sys.path.insert(0,'/vol/v1/general_files/script_library/mosaic')
from osgeo import ogr, gdal, gdalconst
from gdalconst import *
import numpy as np
from tempfile import mkstemp
from lthacks import *
from mosaicDisturbanceMaps_nobuffer import *

LAST_COMMIT = getLastCommit(os.path.abspath(__file__))
AGGREGATION_SCRIPTS_PATH = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
AGGREGATION_PARAMETERS_PATH = os.path.join(AGGREGATION_SCRIPTS_PATH, "parameters")
AGGREGATION_PATH = os.path.dirname(AGGREGATION_SCRIPTS_PATH)
MR224_MASK_PATH = "/vol/v1/proj/cmonster/mr224/mr224_extent_mask.bsq"
MR200_MASK_PATH = "/vol/v1/proj/cmonster/mr200/mr200_mask.bsq"
FOREST_MASK_PATH = "/vol/v1/general_files/datasets/spatial_data/forestmask/final/forestNonForestmask_WAORCA.bsq"
NONFOREST_VALUE = 60
NODATA_VALUE = 70

def getScenes(modelregion):
	'''Reads "tsa_list.txt" parameter file for specified modelregion.
	Returns a list of TSAs'''

	paramfile = os.path.join(AGGREGATION_PARAMETERS_PATH, modelregion, "tsa_list.txt")
	paramdata = open(paramfile, 'r')

	tsas = []
	for line in paramdata:
		line_nospaces = line.strip()
		tsas.append(sixDigitTSA(line_nospaces))

	paramdata.close()

	return tsas

def getPriorities(modelregion):
	'''Reads "agent_source_priorities.txt" parameter file for specified modelregion. 
	Returns a dictionaries of agent source priorities.'''

	paramfile = os.path.join(AGGREGATION_PARAMETERS_PATH, modelregion, "agent_source_priorities.txt")
	paramdata = open(paramfile, 'r')

	priorities = {}
	for line in paramdata:
		line_split = line.split(":")
		priorities[int(line_split[0])] = line_split[1].strip()

	paramdata.close()

	return priorities

def getUASize(path):
	'''Extract bounding info & projection, driver, transform from usearea map'''

	#open and get bounding information from the cloudmask
	UA_image=gdal.Open(path, GA_ReadOnly)
	if UA_image is None:
		print("Failed to open "+UA_image)
		#return 1
	#Define extent
	UA_gt=UA_image.GetGeoTransform()
	ulx=UA_gt[0]
	uly=UA_gt[3]

	#the size of the use area file drives everything else
	masterXsize = UA_image.RasterXSize
	masterYsize = UA_image.RasterYSize

	#use that to figure out the lower right coordinate
	lrx=ulx+masterXsize*UA_gt[1]
	lry=uly+masterYsize*UA_gt[5]

	UASize = {

		'masterXsize': masterXsize,
		'masterYsize': masterYsize,
		'ulx': ulx,
		'uly': uly,
		'lrx': lrx,
		'lry': lry

		}
	
	
	driver = UA_image.GetDriver()
	projection = UA_image.GetProjection()

	outfileParams = {

		'driver': driver,
		'transform': UA_gt,
		'projection': projection
	}

	UA_image = None
	return UASize, outfileParams


def aggregate(image, agentDict, masterSize, bn):
	'''apply priorities to assign a change agent to each pixel in scene'''

	for agentID in sorted(agentDict.keys()):
	   
		#since bug layers only have 1 band, have to create a new variable to hold fetched band 
		fetchband = bn
		agentPath = agentDict[agentID]
		agentbase = os.path.basename(agentPath)
		
		#Assign different parameter values if the agent is a bug file
		# if 'WSB' in agentbase or 'MPB' in agentbase or 'recov' in agentbase:
		if ('WSB' in agentbase) or ('MPB' in agentbase): 
			agentPath = agentPath.replace('X', str(bn))
			fetchband = 1
		
	
		if bn == 1: print 'Working on {0}'.format(os.path.basename(agentPath))
		agent = gdal.Open(agentPath, GA_ReadOnly)

		#get agentfile corners
		agt = agent.GetGeoTransform()
		aulx = agt[0]
		auly = agt[3]
		alrx = aulx+agent.RasterXSize*agt[1]
		alry = auly+agent.RasterYSize*agt[5]

		#determine offset
		diffx = (masterSize['ulx'] - aulx)/agt[1]
		if diffx < 0:
			raise NotImplementedError('Agent {0} ULX is within study area mask'.format(os.path.basename(agentPath)))

		diffy = (masterSize['uly'] - auly)/agt[5]
		if diffy < 0:
			raise NotImplementedError('Agent {0} ULY is within study area mask'.format(os.path.basename(agentPath)))

		#Round diff values to integer values
		diffx = int(round(diffx))
		diffy = int(round(diffy))

		#check to make sure the lower right is not going to be offensive
		lorXoffset = diffx + masterSize['masterXsize']
		lorYoffset = diffy + masterSize['masterYsize']
		if lorXoffset > agent.RasterXSize:
			print 'Agent {0} LORX is not large enough to accomodate study area'.format(os.path.basename(agentPath))
			continue
			#raise NotImplementedError('Agent {0} LORX is not large enough to accomodate study area'.format(os.path.basename(agentPath)))
		if lorYoffset > agent.RasterYSize:
			print 'Agent {0} LORY is not large enough to accomodate study area'.format(os.path.basename(agentPath))
			continue
			#raise NotImplementedError('Agent {0} LORY is not large enough to accomodate study area'.format(os.path.basename(agentPath)))

		agentArray = agent.GetRasterBand(fetchband).ReadAsArray(diffx, diffy, masterSize['masterXsize'], masterSize['masterYsize'])
		#Where image is 0, assign agent file value, elsewhere keep original value
		#Also added MPB and WSB values
		if 'MPB' in agentbase:
			if '29' in agentbase:
				MPBval = 21
			else:
				MPBval = 22
			agentArray = np.where(agentArray != 0, MPBval, agentArray)

		elif 'WSB' in agentbase:
			if '29' in agentbase:
				WSBval = 25
			else:
				WSBval = 26
			agentArray = np.where(agentArray != 0, WSBval, agentArray)
			
# 		elif 'recov' in agentbase:
# 			recoval = 51
# 			agentArray = np.where(agentArray != 0, recoval, agentArray)
# 			
# 		elif 'second_greatest_disturbance' in agentbase:
# 			sec_val = 41
# 			agentArray = np.where(agentArray != 0, sec_val, agentArray)
			
		image = np.where(image == 0, agentArray, image)
	
	#Test to see if recov layer helps explain some issues...
# 	recovtest = np.where(image == 51, image, 0)
# 	rtest = np.sum(recovtest)
# 	if rtest > 0: print "Found {0} 51's!".format(rtest/51)

	#Close agent file
	agent = None

	return image


def writeFile(path, writeImage, outparams, masterparams, writeband, bandsum):
	'''Writes a raster band'''
	#create outfile on first pass
	if writeband == 1:
		outImg = outparams['driver'].Create(path, masterparams['masterXsize'], masterparams['masterYsize'], bandsum, gdalconst.GDT_Int16) #check datatype
		outImg.SetGeoTransform(outparams['transform'])
		outImg.SetProjection(outparams['projection'])
	else:
		outImg = gdal.Open(path, GA_Update)

	outImg.GetRasterBand(writeband).WriteArray(writeImage)

	if writeband == bandsum: outImg = None


def edithdr(path, start):
	'''Assigns years as band names'''
	hdrPath = path.replace('bsq', 'hdr')
	#open hdr file
	hdr = open(hdrPath, 'r')
	#create new tmp file
	tmpPath = '{0}.tmp.txt'.format(os.path.basename(hdrPath))
	tmp, tmpPath = mkstemp()

	new_file = open(tmpPath, 'w')

	#replace band names in file
	band = 0
	year = start-1
	for line in hdr:
		if not line.startswith('Band'):
			new_file.write(line)
		else:
			band += 1
			year += 1
			oldline = 'Band {0}'.format(band)
			new_file.write(line.replace(oldline, str(year)))

	#close files
	new_file.close()
	os.close(tmp)
	hdr.close()
	#replace old hdr file
	os.remove(hdrPath)
	shutil.move(tmpPath, hdrPath)

def metaDescription_tiles(agents, scene):
	desc = "This is an yearly image stack of dominant land cover change agents for TSA {0} aggregated from the following sources:".format(scene)
	desc2 = "\n -" + "\n -".join(agents.values()) 

	return desc + desc2
	
def createMosaic(files, bands, outputFile):
	print '\nCreating mosaic'
	print 'from files' 
	for f in files:
		print os.path.basename(f)
	print 'and bands: {0}'.format(', '.join([str(b) for b in bands]))
	#print bands
	#import pdb; pdb.set_trace()
	run_id = str(random.randint(0, 1000))
	exec_string = "gdalbuildvrt -srcnodata 0 {0}.vrt ".format(outputFile)
	for f in files: exec_string += "{0} ".format(f)
	os.system(exec_string)

	selected_bands = "gdalbuildvrt -separate -srcnodata 0 temp_stack_{0}.vrt ".format(run_id)
	cleanup = ['temp_stack_{0}.vrt'.format(run_id)]
	for band in bands:
		newfile = "ts_{0}_{1}.vrt".format(band, run_id)
		os.system("gdal_translate -of VRT -b {0} {1}.vrt {2}".format(band, outputFile, newfile))
		selected_bands += newfile + " "
		cleanup.append(newfile)
	os.system(selected_bands)
	os.system("gdal_translate -of ENVI temp_stack_{1}.vrt {0}.bsq".format(outputFile, run_id))
	for f in cleanup:
		try: os.remove(f)
		except: pass
	print "Created {0}".format(outputFile)

def main(modelregion, outputfile):

	print '\nAggregation Script'
	
	#get parameters for specified model region
	agents = getPriorities(modelregion.lower())
	scenes = getScenes(modelregion.lower())
	
	#Open sample image to get Band Count
	sample = gdal.Open(agents[5], GA_ReadOnly)
	bands = sample.RasterCount
	del sample

	if os.path.exists(outputfile):
		print "\n" + outputfile + " already exists. Replacing ALL outputs."
		replace = True
	else:
		replace = False

	tiles = []
	for scene in scenes:

		print '\n'
		print 'For Scene: {0}'.format(scene)
		print 'From Files:\n'
		
		for key, value in sorted(agents.items()):
			print os.path.basename(value)
		
		print '\n'

		#UAPath = '/vol/v1/scenes/gnn_snapped_cmon_usearea_files/{0}_usearea.bsq'.format(scene)
		#no buffer version below
		UAPath = '/vol/v1/general_files/datasets/spatial_data/us_contiguous_tsa_masks_nobuffer/us_contiguous_tsa_nobuffer_{0}.bsq'.format(scene)
		
		#define and create directory for TSA tiles
		#outputsdir = os.path.join(AGGREGATION_PATH, "outputs")
		#relpath = os.path.relpath(os.path.abspath(outputfile), AGGREGATION_SCRIPTS_PATH)
		#outdir = os.path.join(os.path.dirname(os.path.join(outputsdir, relpath)), "change_agent_maps", "agent_tiles")
		outdir = os.path.join(os.path.dirname(outputfile), "agent_tiles")
		outname = '{0}_agent_aggregation.bsq'.format(scene)
		outpath = os.path.abspath(os.path.join(outdir, outname))
		if not os.path.exists(outdir):
			os.makedirs(outdir)

		if (not os.path.exists(outpath)) or replace:
		
			UASizeDict, outfileDict = getUASize(UAPath)

			for b in range(bands):

				band = b + 1

				#Set up aggregate image array
				agImage = np.zeros((UASizeDict['masterYsize'], UASizeDict['masterXsize']))
				agImage = aggregate(agImage, agents, UASizeDict, band)

				print 'Writing band {0}'.format(band)
				writeFile(outpath, agImage, outfileDict, UASizeDict, band, bands)
			
			
			edithdr(outpath, 1984)
			print 'Created {0}'.format(outpath)
			if os.path.exists(outpath):
				tiles.append(os.path.abspath(outpath))

			#create metadata
			dataDesc = metaDescription_tiles(agents, scene)
			createMetadata(sys.argv, outpath, description=dataDesc, lastCommit=LAST_COMMIT)

		else:
			print "\n" + outpath + " already exists. Moving on..."
			tiles.append(os.path.abspath(outpath))

	#mosaic tiles
	mosaicfile = os.path.splitext(os.path.abspath(outputfile))[0] + "_mosaic"
	mosaicfile_ext = mosaicfile + ".bsq"
	metaDesc_mosaic = "This is a mosaic of the following agent aggregation maps: \n -" + "\n -".join(tiles)

	if (not os.path.exists(mosaicfile_ext)) or replace:
		print "\nMosaicking scenes..."

		createMosaic(tiles, range(1,bands+1), mosaicfile)
		createMetadata(sys.argv, mosaicfile_ext, description=metaDesc_mosaic, lastCommit=LAST_COMMIT)
		edithdr(mosaicfile_ext, 1984)
	else:
		print "\n" + mosaicfile_ext + " already exists. Moving on..."


	#apply forest mask
	forestsfile = mosaicfile + "_forestsonly.bsq"
	maskcmd = "intersectMask " + mosaicfile_ext + " " + FOREST_MASK_PATH + " " + forestsfile + \
	" --src_band=ALL --out_value={0} --meta='This is an agent aggregation map with forest mask applied.'".format(NONFOREST_VALUE)
	print "\n" + maskcmd + "\n ...."
	subprocess.call(maskcmd, shell=True)
	while not os.path.exists(forestsfile):
		pass
	else:
		edithdr(forestsfile, 1984)	

	#mask to study region
# 	while not os.path.exists(mosaicfile):
# 		pass
# 	else:
	if modelregion.lower() == "mr224":
		maskpath = MR224_MASK_PATH
	elif modelregion.lower() == "mr200":
		maskpath = MR200_MASK_PATH
	else:
		sys.exit("Mask definition for " + modelregion + "not defined.")
		
	maskcmd = "intersectMask " + forestsfile + " " + maskpath + " " + os.path.realpath(outputfile) + \
		      " --src_band=ALL --out_value={0} --meta='This is an agent aggregation map with forest mask applied clipped by study area'".format(NODATA_VALUE)
	print "\n" + maskcmd + "\n ...."
	subprocess.call(maskcmd, shell=True)

	#wait until processes are finished, then write years to header file
	while not os.path.exists(outputfile):
		pass
	else:
		edithdr(outputfile, 1984)
		print " DONE!"


if __name__ == '__main__':
	args = sys.argv
	sys.exit(main(args[1], args[2]))
