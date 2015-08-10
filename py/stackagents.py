'''
stackagents.py
Creates a raster image stack that identifies that dominant 
change agents attributed to each pixel for each year.

Authors: Tara Larrue (tlarrue2991@gmail.com) & Jamie Perkins

Inputs: 
    - modelregion
    - outputfile path
Outputs:
    -  ENVI image stack (.bsq file type) w/ 1 band per year 
       identifying dominant change agents
    -  meta data file

Usage: python stackagents.py [modelregion] [outputfile]
Example: python stackagents.py mr224 /projectnb/trenders/proj/aggregation/aggregation-git/outputs/mr224/mr224_agent_aggregation.bsq
'''
import sys, os, glob, re, shutil
from osgeo import ogr, gdal, gdalconst
from gdalconst import *
import numpy as np
from tempfile import mkstemp
from validation_funs import *

SCRIPT_LAST_UPDATED = "08/10/2015"

AGGREGATION_GIT_PATH = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
AGGREGATION_PATH = os.path.dirname(AGGREGATION_GIT_PATH)

def getScenes(modelregion):
    '''Reads "tsa_list.txt" parameter file for specified modelregion.
    Returns a list of TSAs'''

    paramfile = os.path.join(AGGREGATION_GIT_PATH, "data/parameters", modelregion, "tsa_list.txt")
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

    paramfile = os.path.join(AGGREGATION_GIT_PATH, "data/parameters", modelregion, "agent_source_priorities.txt")
    paramdata = open(paramfile, 'r')

    priorities = {}
    for line in paramdata:
        line_split = line.split(":")
        priorities[int(line_split[0])] = line_split[1].strip()

    paramdata.close()

    return priorities


def getUASize(path):

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

    for agentID in sorted(agentDict.keys()):
       
        #since bug layers only have 1 band, have to create a new variable to hold fetched band 
        fetchband = bn
        agentPath = agentDict[agentID]
        agentbase = os.path.basename(agentPath)
        
        #Assign different parameter values if the agent is a bug file
        if 'WSB' in agentbase or 'MPB' in agentbase or 'recov' in agentbase:
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
	elif 'recov' in agentbase:
	    recoval = 51
	    agentArray = np.where(agentArray != 0, recoval, agentArray)
        
        image = np.where(image == 0, agentArray, image)
	
	#Test to see if recov layer helps explain some issues...
	recovtest = np.where(image == 51, image, 0)
	rtest = np.sum(recovtest)
	if rtest > 0: print "Found {0} 51's!".format(rtest/51)

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

def createMetadata_tile(outpath_git, outpath_bigdata, agents, scene):
  
    timeStamp = datetime.now().strftime('%Y%m%d %H:%M:%S')
    user = getpass.getuser()
    commandline = " ".join(sys.argv)
    desc = "This is an yearly image stack of dominant land cover change agents for TSA {0} aggregated from the following sources:".format(scene)
    desc2 = "\n-".join(agents)

    outpath_git_meta = os.path.splitext(outpath_git)[0] + "_meta.txt"
    outpath_bigdata_meta = os.path.splitext(outpath_bigdata)[0] + "_meta.txt"

    f = open(outpath_git_meta, "w")
    f.write(desc + desc2)
    f.write("\nFULL IMAGE PATH: " + outpath_bigdata)
    f.write("\nCREATED BY: " + os.path.realpath(__file__))
    f.write("\nSCRIPT LAST UPDATED: " + SCRIPT_LAST_UPDATED)
    f.write("\nCOMMAND: " + commandline)
    f.write("\nTIME: " + timeStamp)
    f.write("\nUSER: " + user)
    f.close()

    f = open(outpath_bigdata_meta, "w")
    f.write(desc + desc2)
    f.write("\nFULL IMAGE PATH: " + outpath_bigdata)
    f.write("\nCREATED BY: " + os.path.realpath(__file__))
    f.write("\nSCRIPT LAST UPDATED: " + SCRIPT_LAST_UPDATED)
    f.write("\nCOMMAND: " + commandline)
    f.write("\nTIME: " + timeStamp)
    f.write("\nUSER: " + user)
    f.close()


def main(modelregion, outputfile):

    print '\nAggregation Script'
    #get parameters for specified model region
    agents = getPriorities(modelregion.lower())
    scenes = getScenes(modelregion.lower())

    tiles = []
    for scene in scenes:

        print '\n'
        print 'For Scene: {0}'.format(scene)
        print 'From Files:\n'
        
        for key, value in sorted(agents.items()):
            print os.path.basename(value)
        
        print '\n'

        UAPath = '/projectnb/trenders/scenes/gnn_snapped_cmon_usearea_files/{0}_usearea.bsq'.format(scene)
        
        bigdatadir = os.path.join(AGGREGATION_PATH, "big_data")
        relpath = os.path.relpath(outputfile, AGGREGATION_GIT_PATH)
        outdir_bigdata = os.path.join(os.path.dirname(os.path.join(bigdatadir, relpath)), "tiles")
        outdir_git = os.path.join(os.path.dirname(outputfile), "tiles")
        outname = '{0}_agent_aggregation.bsq'.format(scene)
        outpath_bigdata = os.path.join(outdir_bigdata, outname)
        outpath_git = os.path.join(outdir_git, outname)
        for d in [outdir_bigdata, outdir_git]:
            if not os.path.exists(d):
                os.makedirs(d)
        
        UASizeDict, outfileDict = getUASize(UAPath)

        #Open sample iamge to get Band Count
        sample = gdal.Open(agents[1], GA_ReadOnly)
        bands = sample.RasterCount
        sample = None

        for b in range(bands):

            band = b + 1

            #Set up aggregate image array
            agImage = np.zeros((UASizeDict['masterYsize'], UASizeDict['masterXsize']))
            agImage = aggregate(agImage, agents, UASizeDict, band)

            print 'Writing band {0}'.format(band)
            writeFile(outpath_bigdata, agImage, outfileDict, UASizeDict, band, bands)
        
        
        edithdr(outpath_bigdata, 1984)
        print 'Created {0}'.format(outpath_bigdata)
        if os.path.exists(outpath_bigdata):
            tiles.append(outpath_bigdata)
        createMetadata_tile(outpath_git, outpath_bigdata, agents, scene)

    #mosaicTiles(tiles)



if __name__ == '__main__':
    args = sys.argv
    sys.exit(main(args[1], args[2]))
