######################################################################################
#
#       Attribution Layers.py
#       
#       Inputs: Image stacks describing agent disturbance
#       Outputs: Single image stack identifying prevalent agent on a per-pixel basis,
#                Agent value determined by file priority
#
#
#
#
######################################################################################

import sys, os, glob, re, shutil
from osgeo import ogr, gdal, gdalconst
from gdalconst import *
import numpy as np
from tempfile import mkstemp


def getScenes(filePath):

    sceneFile = open(filePath, 'r')
    #Skip first line for title
    next(sceneFile)

    List = []
    for item in sceneFile:
        if not item.startswith('#'):
            if (item.lower()).startswith('region'):
                thesplit = item.split(':')
                region = thesplit[1].strip(' \n')
	    else:
		item = item.strip(' \n')
                List.append(item)

    sceneFile.close()
    return List, region


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


def main(scene, area):

    #index specifies priority
    if area == 'mr224_posttc':
        agents = {
           # 1: '/projectnb/trenders/proj/david/magnitude_by_year/mr224_fast/mr224_attribution_by_year_mosaic.bsq' ,
			1: '/projectnb/trenders/proj/ltattribution/mr224_fast/Random_Forest/mr224_trn1thrutrn3_noNA_revposttc/mr224_change_process_trn1thrutrn3_noNA_revposttc/mr224_posttc_attribution_by_year_mosaic.bsq' ,
			2: '/projectnb/trenders/proj/bug_mosaics/MPB_29/insect_mosaic_MPB_29_band_X.bsq' ,
            3: '/projectnb/trenders/proj/bug_mosaics/MPB_239/insect_mosaic_MPB_239_band_X.bsq' ,
            4: '/projectnb/trenders/proj/bug_mosaics/WSB_29/insect_mosaic_WSB_29_band_X.bsq' ,
            5: '/projectnb/trenders/proj/bug_mosaics/WSB_239/insect_mosaic_WSB_239_band_X.bsq' ,
            6: '/projectnb/trenders/proj/david/magnitude_by_year/mr224_unf_longest/mr224_unf_longest_mosaic.bsq' ,
            7: '/projectnb/trenders/proj/david/magnitude_by_year/mr224_unf_fast/mr224_unf_fast_mosaic.bsq' ,
            8: '/projectnb/trenders/proj/david/magnitude_by_year/mr224_unf_wetness_recovery/mr224_unf_wetness_recovery_mosaic.bsq' ,
			9: '/projectnb/trenders/general_files/user_files/jamie/py_scripts/aggregation/mr224/extra_files/greatest_recov_mr224_mosaic.bsq'
        }

    print '\n'
    print 'Aggregation Script'
    print 'For Scene: {0}'.format(scene)
    print 'From Files:\n'
    
    for key, value in sorted(agents.items()):
        print os.path.basename(value)
    
    print '\n'

    UAPath = '/projectnb/trenders/scenes/gnn_snapped_cmon_usearea_files/{0}_usearea.bsq'.format(scene)
    out = os.path.join('/projectnb/trenders/proj/aggregation/outputs', area, 'agent_files/tiles')
    outname = '{0}_Agent_Aggregation.bsq'.format(scene)
    outpath = os.path.join(out, outname)
    if not os.path.exists(out):
        os.makedirs(out)
    
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
        #print agImage.dtype.type
	writeFile(outpath, agImage, outfileDict, UASizeDict, band, bands)
    
    edithdr(outpath, 1984)
    print 'Created {0}'.format(outpath)

if __name__ == '__main__':
    #assert isinstance(sys.argv[2], basestring)
    #place = sys.argv[2].lower()
    if sys.argv[1].endswith('.txt'):
        sceneList, place = getScenes(sys.argv[1])
        print 'Scenes to be Processed:\n{0}'.format('\n'.join(sceneList))
        for scn in sceneList:
            main(scn, place)
            sys.exit
    else:
        assert re.match('[0-9][0-9][0-9][0-9][0-9][0-9]', sys.argv[1]), 'Invalid Scene Code'
        sys.exit(main(sys.argv[1], place))
