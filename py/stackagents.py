'''
stackagents.py
Creates a raster image stack that identifies dominant 
change agents attributed to each pixel for each year.

Authors: Tara Larrue (tlarrue2991@gmail.com) & Jamie Perkins

Inputs: 
	- modelregion
	- modelregion mask path
	- forest mask path
	- starting year, assigned to band 1
	- outputfile path

Outputs:
	-  ENVI image stack (.bsq file type) w/ 1 band per year identifying dominant change agents
	-  metadata file

Usage: python stackagents.py [modelregion] [mr_mask] [forest_mask] [band1_year] [outputfile]

Example: python stackagents.py mr224 /vol/v1/proj/cmonster/mr224/mr224_mask.bsq 
/vol/v1/general_files/datasets/spatial_data/orcawa_forestnonforestmask.bsq 1984
/vol/v1/proj/aggregation/outputs/mr224/mr224_agent_aggregation.bsq
'''
import sys, os, glob, re, shutil, subprocess
# sys.path.insert(0,'/vol/v1/general_files/script_library/mosaic/mosaic-scripts')
from osgeo import ogr, gdal, gdalconst
from gdalconst import *
import numpy as np
from tempfile import mkstemp
from lthacks.lthacks import *
import lthacks.intersectMask as imask
# from mosaicDisturbanceMaps_nobuffer import *
import random

#global variables
LAST_COMMIT = getLastCommit(os.path.abspath(__file__))
AGGREGATION_SCRIPTS_PATH = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
AGGREGATION_PARAMETERS_PATH = os.path.join(AGGREGATION_SCRIPTS_PATH, "parameters")
AGGREGATION_PATH = os.path.dirname(AGGREGATION_SCRIPTS_PATH)
NOBUFFER_MASK_TEMPLATE = "/vol/v1/general_files/datasets/spatial_data/us_contiguous_tsa_masks_nobuffer/us_contiguous_tsa_nobuffer_{0}.bsq"
SEARCHKEYS = {"nodata": ["no", "data"],
			  "nonforest": ["non", "forest"],
			  "mpb-29": ["mpb", "29"],
			  "mpb-239": ["mpb", "239"],
			  "wsb-29": ["wsb", "29"],
			  "wsb-239": ["wsb", "239"]}

def getScenes(modelregion):
	'''Reads "tsa_list.txt" parameter file for specified modelregion.
	Returns a list of TSAs'''

	paramfile = os.path.join(AGGREGATION_PARAMETERS_PATH, modelregion, "tsa_list.txt")
	paramdata = open(paramfile, 'r')

	tsas = []
	for line in paramdata:
		line_nospaces = line.strip()
		if line_nospaces != '':
			tsas.append(sixDigitTSA(line_nospaces))

	paramdata.close()

	return tsas

def getKeyDict(modelregion):

	paramfile = os.path.join(AGGREGATION_PARAMETERS_PATH, modelregion, "agent_key.txt")
	paramdata = open(paramfile, 'r')

	keydict = {}

	for line in paramdata:
		try:
			key,desc = line.split(":") 
			desc=desc.lower().replace(" ", "")
		except ValueError:
			sys.exit("ERROR: Check agent_key.txt, make sure each line has format 'key#:description'")

		for name,searchwords in SEARCHKEYS.items():
			all_in_bools = [word in desc for word in searchwords]
			if all(all_in_bools):
				keydict[name] = int(key)

	paramdata.close()

	return keydict

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

def getUASize(uaPath, allAgentPaths):
	'''returns a dictionary with output raster parameters, by calculating least common 
	bounds between all agent sources and TSA use area'''

	allmaps = allAgentPaths + [uaPath]	
	
	#find single sample map for each insect band
	for ind,i in enumerate(allmaps):
		if 'mpb' in i.lower() or 'wsb' in i.lower():
			searchpath = i.replace("_X_", "_*_")
			matches = glob.glob(searchpath)
			sample_map = matches[0]
			
			allmaps[ind] = sample_map
			
	#find common bounds between use area & all agent source maps
	common_size, common_transform, projection, driver = imask.findLeastCommonBoundaries(allmaps)
	cols = int(common_size[0])
	rows = int(common_size[1])
	(midx, midy) = imask.transformToCenter(common_transform, cols, rows)

	outsize_dict = {
		'cols': cols,
		'rows': rows,
		'midx': midx,
		'midy': midy,
		'transform': common_transform,
		'projection': projection,
		'driver': driver
		}

	return outsize_dict	

def aggregate(agentDict, outsize_dict, bn, keydict):
	'''apply priorities to assign a change agent to each pixel in scene'''
	
	image = np.zeros((outsize_dict['rows'], outsize_dict['cols']))

	for agentID in sorted(agentDict.keys()):
	   
		#since bug layers only have 1 band, have to create a new variable to hold fetched band 
		fetchband = bn
		agentPath = agentDict[agentID]
		agentbase = os.path.basename(agentPath)
		
		#Assign different parameter values if the agent is a bug file
		# if 'WSB' in agentbase or 'MPB' in agentbase or 'recov' in agentbase:
		if ('wsb' in agentbase.lower()) or ('mpb' in agentbase.lower()):
			agentPath = agentPath.replace('X', str(bn))
			fetchband = 1
		
		if bn == 1: print 'Working on {0}'.format(os.path.basename(agentPath))
		
		#load agent source data within output bounds
		agent = gdal.Open(agentPath, GA_ReadOnly)
		agent_transform = agent.GetGeoTransform()
		agentArray = extract_kernel(agent, outsize_dict['midx'], outsize_dict['midy'], 
		outsize_dict['cols'], outsize_dict['rows'], fetchband, agent_transform)
		
		#Where image is 0, assign agent file value, elsewhere keep original value
		#Also added MPB and WSB values
		if 'mpb' in agentbase.lower():
			if '29' in agentbase:
				MPBval = keydict['mpb-29']
			else:
				MPBval = keydict['mpb-239']
			agentArray = np.where(agentArray != 0, MPBval, agentArray)

		elif 'wsb' in agentbase.lower():
			if '29' in agentbase:
				WSBval = keydict['wsb-29']
			else:
				WSBval = keydict['wsb-239']
			agentArray = np.where(agentArray != 0, WSBval, agentArray)
			
		image = np.where(image == 0, agentArray, image)
	
	#clean up
	del agent, agentArray

	return image
	
def writeFile(path, writeImage, outparams, writeband, bandsum):
	'''Writes a raster band'''
	#create outfile on first pass
	if writeband == 1:
		outImg = outparams['driver'].Create(path, outparams['cols'], 
		outparams['rows'], bandsum, gdalconst.GDT_Int16)
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
	desc = "This is an yearly image stack of dominant land cover change agents for TSA \
	{0} aggregated from the following sources:".format(scene)
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



def main(modelregion, modelregion_mask, forest_mask, start_year, outputfile):

	print '\nAggregation Script'

	#first, check if outputfile already exists
	if os.path.exists(outputfile):
		existsErr = "\n" + outputfile + " already exists. \
		Please delete file & re-run if you want to replace this output."
		sys.exit(existsErr)

	#format inputs
	modelregion = modelregion.lower()
	notFoundErr = "\nInput path not found : "
	if not os.path.exists(modelregion_mask):
		sys.exit(notFoundErr + modelregion_mask)
	if not os.path.exists(forest_mask):
		sys.exit(notFoundErr + forest_mask)
	start_year = int(start_year)
	
	#get parameters for specified model region
	sources = getPriorities(modelregion) #dictionary
	scenes = getScenes(modelregion) #list
	keydict = getKeyDict(modelregion) #dictionary
	
	#open sample image to get band count
	for source in sources.values():
		if ('insect' not in source.lower()) and ('bug' not in source.lower()):
			print "\nCounting bands from: ", source
			break
	sample = gdal.Open(source, GA_ReadOnly)
	numbands = sample.RasterCount
	bands = range(1,numbands+1)
	del sample, source

	#accumulate tiles for each TSA
	tiles = []
	for scene in scenes:

		print '\n'
		print 'For Scene: {0}'.format(scene)
		print 'From Files:\n'
		
		for key, value in sorted(sources.items()):
			print os.path.basename(value)
		
		print '\n'

		#get no buffer use area mask for TSA
		UAPath = NOBUFFER_MASK_TEMPLATE.format(scene)
		
		#define and create directory for TSA tiles
		outdir = os.path.join(os.path.dirname(outputfile), "agent_tiles")
		outname = '{0}_agent_aggregation.bsq'.format(scene)
		outpath = os.path.abspath(os.path.join(outdir, outname))
		if not os.path.exists(outdir):
			os.makedirs(outdir)

		#create TSA tile if it does not already exist
		if not os.path.exists(outpath):
		
			#calculate use area size
			outsize_dict = getUASize(UAPath, sources.values())

			#aggregate sources & write out each band
			for band in bands:

				#Set up aggregate image array
				agImage = aggregate(sources, outsize_dict, band, keydict)

				print 'Writing band {0}'.format(band)
				writeFile(outpath, agImage, outsize_dict, band, numbands)
			
			#edit hdr file with years as band descriptions
			edithdr(outpath, start_year)
			print 'Created {0}'.format(outpath)
			if os.path.exists(outpath):
				tiles.append(os.path.abspath(outpath))

			#create metadata
			dataDesc = metaDescription_tiles(sources, scene)
			createMetadata(sys.argv, outpath, description=dataDesc, lastCommit=LAST_COMMIT)

		else:
			print "\n" + outpath + " already exists. Moving on..."
			tiles.append(os.path.abspath(outpath))

	#mosaic tiles
	mosaicfile = os.path.splitext(os.path.abspath(outputfile))[0] + "_mosaic"
	mosaicfile_ext = mosaicfile + ".bsq"
	metaDesc_mosaic = "This is a mosaic of the following agent aggregation maps: \n -" + "\n -".join(tiles)

	if not os.path.exists(mosaicfile_ext):
		print "\nMosaicing scenes..."

		createMosaic(tiles, bands, mosaicfile)
		createMetadata(sys.argv, mosaicfile_ext, description=metaDesc_mosaic, lastCommit=LAST_COMMIT)
		edithdr(mosaicfile_ext, start_year)
	else:
		print "\n" + mosaicfile_ext + " already exists. Moving on..."


	#apply forest mask
	forestsfile = mosaicfile + "_forestsonly.bsq"

	maskcmd = "intersectMask " + mosaicfile_ext + " " + forest_mask + " " + forestsfile + \
	" --src_band=ALL --out_value={0} --meta='This is an agent aggregation map with forest mask applied.'".format(str(keydict['nonforest']))
	print "\n" + maskcmd + "\n ...."
	subprocess.call(maskcmd, shell=True)
	while not os.path.exists(forestsfile):
		pass
	else:
		edithdr(forestsfile, start_year)	

	#mask to study region
	maskcmd = "intersectMask " + forestsfile + " " + modelregion_mask + " " + os.path.realpath(outputfile) + \
		      " --src_band=ALL --out_value={0} --meta='This is an agent aggregation map with forest mask applied clipped by study area'".format(str(keydict['nodata']))
	print "\n" + maskcmd + "\n ...."
	subprocess.call(maskcmd, shell=True)

	#wait until processes are finished, then write years to header file
	while not os.path.exists(outputfile):
		pass
	else:
		edithdr(outputfile, start_year)
		print " DONE!"


if __name__ == '__main__':

	args = sys.argv[1:]

	if len(args) != 5:

		usageErr = "\nInputs not understood. Usage:\npython stackagents.py \
		[modelregion] [modelregion_mask] [forest_mask] [band1_year] [outputfile]"
		sys.exit(usageErr)

	else:

		sys.exit(main(*args))
