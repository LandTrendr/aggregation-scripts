'''
deltaBiomass.py
Creates yearly delta biomass image stacks for specified biomass flavors.
Outputs from this script can be used to integrate with change agent aggregation layers.

Author: Jamie Perkins

Inputs: 
    - yearly biomass images
Outputs:
    -  ENVI image stack (.bsq file type) of yearly delta biomass images
    -  metadata file

Usage: python deltaBiomass.py [path/to/parameterfile]
Example: python deltaBiomass.py /vol/v1/proj/aggregation/log/mr224_deltabiomass_params.txt
'''
import sys, os, glob, re, shutil
from osgeo import ogr, gdal, gdalconst
from gdalconst import *
import numpy as np
from tempfile import mkstemp
from lthacks import *


def ReadParams(filepath):

    txt = open(filepath, 'r')

    next(txt)
    biomass = []
    name = []
    for line in txt:
        if not line.startswith('#'):
            prams = line.split(':')
            var = prams[1].strip(' \n')
            if prams[0] != '':
                title = prams[0].strip(' \n').lower()
            
            if title == 'name': name.append(var)
            elif title == 'biomass': biomass.append(var)
            elif title == 'region': region = var

    txt.close()
    
    return name, biomass, region


def getBounds(sampleImage):


    #open and get bounds from sample image
    sample = gdal.Open(sampleImage, GA_ReadOnly)
    if sample is None:
        print 'Failed to Open {0}'.format(sampleImage)
    #Get transform
    sample_gt = sample.GetGeoTransform()
    #get bounds
    #upper left
    ulx = sample_gt[0]
    uly = sample_gt[3]
    
    #master size
    masterXsize = sample.RasterXSize
    masterYsize = sample.RasterYSize

    #lower right
    lrx = ulx + masterXsize * sample_gt[1]
    lry = uly + masterYsize * sample_gt[5]

    #store bounds
    bounds = {

        'masterXsize': masterXsize,
        'masterYsize': masterYsize,
        'ulx': ulx,
        'uly': uly,
        'lrx': lrx,
        'lry': lry,
        'driver': sample.GetDriver(),
        'transform': sample_gt,
        'projection': sample.GetProjection()

    }

    sample = None

    return bounds


def getDiff(cPath, pPath, params):

    start = 1984
    end = 2012

    for year in range(start, end+1):
        
        year = str(year)
        
        #find starting and ending years for difference
        if year in pPath:
            year1 = year
        if year in cPath:
            year2 = year

    print 'Getting Difference between {0} and {1}'.format(year1, year2)
    
    bandName = '{0}_{1}'.format(year2, year1)

    current = gdal.Open(cPath, GA_ReadOnly)
    past = gdal.Open(pPath, GA_ReadOnly)

    #get current corners

    cgt = current.GetGeoTransform()
    culx = cgt[0]
    culy = cgt[3]
    clrx = culx+current.RasterXSize*cgt[1]
    clry = culy+current.RasterYSize*cgt[5]

    #determine current offset and round

    cdiffx = (params['ulx'] - culx)/cgt[1]
    cdiffy = (params['uly'] - culy)/cgt[5]
    cdiffx = int(round(cdiffx))
    cdiffy = int(round(cdiffy))

    #determine past corners
    pgt = past.GetGeoTransform()
    pulx = pgt[0]
    puly = pgt[3]
    plrx = pulx+past.RasterXSize*pgt[1]
    plry = puly+past.RasterYSize*pgt[5]

    #determine past offset and round

    pdiffx = (params['ulx'] - pulx)/pgt[1]
    pdiffy = (params['uly'] - puly)/pgt[5]
    pdiffx = int(round(pdiffx))
    pdiffy = int(round(pdiffy))

    #define arrays
    currentArray = current.GetRasterBand(1).ReadAsArray(cdiffx, cdiffy, params['masterXsize'], params['masterYsize'])
    pastArray = past.GetRasterBand(1).ReadAsArray(pdiffx, pdiffy, params['masterXsize'], params['masterYsize'])

    #subtract arrays for difference
    diff = (currentArray - pastArray)/100

    #close files
    current, past = None, None

    return diff, bandName


def writeFile(array, outparams, path, bn, totalbns):

    #create file on first pass
    if bn == 1:
        outfile = outparams['driver'].Create(path, outparams['masterXsize'], outparams['masterYsize'], totalbns, gdalconst.GDT_Int16)
        outfile.SetGeoTransform(outparams['transform'])
        outfile.SetProjection(outparams['projection'])
    else:
        outfile = gdal.Open(path, GA_Update)

    outfile.GetRasterBand(bn).WriteArray(array)

    if bn == totalbns:
        outfile == None

def edithdr(hdrPath, names):

    #import pdb; pdb.set_trace()
    print 'Renaming hdr band names'
    hdrPath = hdrPath.replace('bsq', 'hdr')
    #open hdr file
    hdr = open(hdrPath, 'r')
    #create new tmp file
    tmpPath = '{0}.tmp.txt'.format(os.path.basename(hdrPath))
    tmp, tmpPath = mkstemp()

    new_file = open(tmpPath, 'w')

    #replace band names in file
    for line in hdr:
        if not line.startswith('Band'):
            new_file.write(line)
        else:
            info = line.split(' ')
            bandnum = int(info[1].strip(',}\n'))
            oldname = 'Band {0}'.format(bandnum)
            newname = names[bandnum]
            new_file.write(line.replace(oldname, newname))
    new_file.close()
    os.close(tmp)
    hdr.close()

    os.remove(hdrPath)
    shutil.move(tmpPath, hdrPath)



def main(name, regdir, region):

    #region = 'mr224'
    #regdir = '/projectnb/trenders/proj/cmonster/mr224/biomassApril2014/nbr/tc_nbr_k1/bph_ge_3_jenk'

    out = os.path.join('/vol/v1/proj/aggregation/outputs', region.lower(), 'biomass_maps')
    if not os.path.exists(out):
        os.makedirs(out)
    outPath = os.path.join(out, 'biomass_{0}_{1}.bsq'.format(name, region))

    imageList = sorted(glob.glob(os.path.join(regdir, '*[0-9].bsq')))

    print 'Fetching Parameters'
    boundsDict = getBounds(imageList[0])
    totalbands = len(imageList)
    band = 0

    bandNames = {}

    for f in imageList:

        band += 1

        #set up array to hold differences
        if band == 1: 
            diffArray = np.zeros((boundsDict['masterYsize'], boundsDict['masterXsize']))
            for year in range(1984, 2013):
                year = str(year)
                if year in f:
                    break
            bandNames[band] = year
        
        #otherwise, feed in current and previous year images
        else:
            fprev = imageList[imageList.index(f)-1]
            diffArray, bandNames[band] = getDiff(f, fprev, boundsDict)

        print 'Writing band {0}'.format(band)
        writeFile(diffArray, boundsDict, outPath, band, totalbands)

    edithdr(outPath, bandNames)
    print 'Created {0}'.format(outPath)
    
    createMetadata(sys.argv, outPath)

if __name__ == '__main__':
    #import pdb; pdb.set_trace()
    name, biomassdirs, region = ReadParams(sys.argv[1])
    if len(sys.argv) > 2:
        i = int(sys.argv[2])-1
        print biomassdirs[i]
        main(name[i], biomassdirs[i], region)
    else:
        for i in xrange(len(biomassdirs)):
            print biomassdirs[i]
            main(name[i], biomassdirs[i], region)
    #end if
    
    sys.exit
