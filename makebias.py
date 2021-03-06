#!/usr/bin/env python3
import argparse, sys, numpy
import matplotlib.pyplot
import generallib
import astropy
import subprocess
from astropy.io import fits

if __name__ == "__main__":
	parser = argparse.ArgumentParser(description='Loads a list of FITS files makes a bias frame from them.')
	parser.add_argument('inputfiles', type=str, help='A text file listing which files to load.')
	parser.add_argument('-s', '--save', type=str, help="Save to the plot to a file.")
	parser.add_argument('-p', '--pause', type=float, default=0.5, help="Number of seconds to pause on each plot.")
	parser.add_argument('-i', '--interactive', action="store_true", help="Make each plot interactive (mouse to zoom, etc).")
	parser.add_argument("-o", "--outputfilename", type=str, help="Output filename for the bias.")
	parser.add_argument('-j', '--json', type=str, help="Save to a JSON file (specify filename).")
	parser.add_argument("--preview",  action="store_true", help="Preview each CCD in 'ds9'.")
	arg = parser.parse_args()

	blocking = False
	if arg.interactive: blocking = True
	numCCDs = 1

	fileList = []

	listFile = open(arg.inputfiles, 'rt')
	for line in listFile:
		filename = line.strip()
		if filename[0] == '#': continue
		fileList.append(filename)
	listFile.close()

	print("Number of files to process for bias is", len(fileList))

	# Perform some preparation before full processing

	# Check if WFC
	checkFITSFile = fileList[0]
	hdul = astropy.io.fits.open(checkFITSFile)
	print(hdul.info())
	header = hdul[0].header
	allHeaders = {}
	for h in header:
		print(h, header[h])
		allHeaders[h] = header[h]
	if len(hdul)==5:
		print("This exposure has multiple extensions... assuming WFC full image")
		numCCDs = len(hdul) - 1

	# Report and save some important headers
	#CCDXBIN = allHeaders['CCDXBIN'] 
	#CCDYBIN = allHeaders['CCDYBIN'] 
	#RSPEED = allHeaders['CCDSPEED'] 
	#print("CCDXBIN", CCDXBIN)
	#print("CCDYBIN", CCDYBIN)
	#print("RSPEED", RSPEED)

	biasFrames = []
	for index, FITSfile in enumerate(fileList):
		frameNo = index+1
		print("Frame no: %d"%(frameNo))
		hdul = astropy.io.fits.open(FITSfile)
		imageData = hdul[0].data
		biasFrames.append(imageData)
		hdul.close()
		amplifiedImage = generallib.percentiles(imageData, 5, 95)
		matplotlib.pyplot.imshow(amplifiedImage)
		matplotlib.pyplot.gca().invert_yaxis()
		matplotlib.pyplot.show(block=False)
		matplotlib.pyplot.pause(0.01)
		matplotlib.pyplot.clf() #clears figure
		
	biasData = numpy.median(biasFrames, axis = 0)
	matplotlib.pyplot.imshow(biasData)
	matplotlib.pyplot.show(block=False)
	print("Number of bias frames used: ", len(biasFrames))
	print("Bias shape:", numpy.shape(biasData))
	mean = numpy.mean(biasData)
	median = numpy.median(biasData)
	stddev = numpy.std(biasData)
	print("Full frame")
	print("\tmean: {:.1f}\t median: {:.1f}\t std. dev.: {:.2f}".format(mean, median, stddev))
	midx, midy = ( int(numpy.shape(biasData)[0] / 2), int(numpy.shape(biasData)[1] / 2))
	pixelRange = 15
	centralRegion = biasData[midx-pixelRange:midx+pixelRange, midy-pixelRange:midy+pixelRange]
	print("Size of central sample:", numpy.shape(centralRegion),"or", numpy.shape(centralRegion)[0] * numpy.shape(centralRegion)[1],"pixels.")
	mean = numpy.mean(centralRegion)
	median = numpy.median(centralRegion)
	stddev = numpy.std(centralRegion)
	print("\tmean: {:.1f}\t median: {:.1f}\t std. dev.: {:.2f}".format(mean, median, stddev))
	hdr = astropy.io.fits.Header()
	hdu = astropy.io.fits.PrimaryHDU(biasData)
	hdul = astropy.io.fits.HDUList([hdu])
	hdul.writeto('bias.fits', overwrite=True)

	if arg.preview:
			ds9Command = ['ds9']
			ds9Command.append('bias.fits')
			ds9Command.append('-zscale')
			subprocess.Popen(ds9Command)
		

	
	sys.exit()
