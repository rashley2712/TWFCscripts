#!/usr/bin/env python3
import argparse, sys, numpy
import matplotlib.pyplot
import datetimelib
import photometrylib
import generallib
import astropy
import subprocess

if __name__ == "__main__":
	parser = argparse.ArgumentParser(description='Loads a list of FITS files and previews them.')
	parser.add_argument('inputfiles', type=str, help='A text file listing which files to load.')
	parser.add_argument('-s', '--save', type=str, help="Save to the plot to a file.")
	parser.add_argument('-b', '--bias', type=str, help="Name of the bias frame.")
	parser.add_argument('-p', '--pause', type=float, default=0.25, help="Number of seconds to pause on each plot.")
	parser.add_argument('-i', '--interactive', action="store_true", help="Make each plot interactive (mouse to zoom, etc).")
	parser.add_argument("--preview",  action="store_true", help="Preview each CCD in 'ds9'.")
	parser.add_argument("-o", "--outputfilename", type=str, help="Output filename for the flat.")
	parser.add_argument('-j', '--json', type=str, help="Save to a JSON file (specify filename).")
	arg = parser.parse_args()
	scale = False
	blocking = False
	if arg.interactive: blocking = True

	upperLimit = 62000
	lowerLimit = 5000

	fileList = []

	listFile = open(arg.inputfiles, 'rt')
	for line in listFile:
		filename = line.strip()
		if filename[0] == '#': continue
		fileList.append(filename)
	listFile.close()
	
	
	if arg.bias is not None:
		print("loading the bias frame", arg.bias)
		hdul = astropy.io.fits.open(arg.bias)
		bias = hdul[0].data
		hdul.close()

	matplotlib.pyplot.figure(figsize=(10,10/1.6))
	
	flatFrames = []
	for index, FITSfile in enumerate(fileList):
		frameNo = index+1
		print("%s: Frame no: %d"%(FITSfile, frameNo))
		hdul = astropy.io.fits.open(FITSfile)
		header = hdul[0].header
		try:
			expTime = header['EXPTIME']
		except KeyError:
			expTime = "unknown"
		imageData = hdul[0].data
		# Subtract the bias
		if arg.bias is not None: imageData = imageData - bias
		
		flatDict = { "filename": FITSfile, "data": imageData, "reject": False, "expTime": expTime }
		hdul.close()
		flatDict['median'] = numpy.median(imageData)
		flatDict['min'] = numpy.min(imageData)
		flatDict['max'] = numpy.max(imageData)
		print("Median: %d, Max: %d, Min: %d"%(int(flatDict['median']), int(flatDict['max']), int(flatDict['min'])))
		# if flatDict['max']>upperLimit: flatDict['reject'] = True
		if flatDict['min']<lowerLimit: flatDict['reject'] = True
		if flatDict['reject']: print("\trejected!")
		flatFrames.append(flatDict)
		
		amplifiedImage = generallib.percentiles(imageData, 5, 95)
		matplotlib.pyplot.imshow(amplifiedImage)
		matplotlib.pyplot.gca().invert_yaxis()
		matplotlib.pyplot.show(block=False)
		matplotlib.pyplot.pause(arg.pause)
		matplotlib.pyplot.clf()


	# 
	# Plot the median, min, max counts of the flats
	
	matplotlib.pyplot.figure(figsize=(8,8/1.6))
	symbols = []
	for f in flatFrames:
		if f['reject']: symbols.append('x')
		else: symbols.append('.')
	yValues = [ f['median'] for f in flatFrames]
	for x, y, s in zip(range(1, len(yValues)+1), yValues, symbols): 
		matplotlib.pyplot.scatter(x, y, marker=s, label = "median", color='r')
	yValues = [ f['max'] for f in flatFrames]
	for x, y, s in zip(range(1, len(yValues)+1), yValues, symbols): 
		matplotlib.pyplot.scatter(x, y, marker=s, label = "median", color='b')
	yValues = [ f['min'] for f in flatFrames]
	for x, y, s in zip(range(1, len(yValues)+1), yValues, symbols): 
		matplotlib.pyplot.scatter(x, y, marker=s, label = "median", color='g')
	
	matplotlib.pyplot.ylim(0, 65535)
	matplotlib.pyplot.ylabel("Counts")
	matplotlib.pyplot.xlabel("Frame number")
	matplotlib.pyplot.plot([1, len(yValues)] , [upperLimit, upperLimit], ls=":", color='k')
	matplotlib.pyplot.plot([1, len(yValues)] , [lowerLimit, lowerLimit], ls=":", color='k')
	matplotlib.pyplot.draw()
	matplotlib.pyplot.show(block=False)
	
	validFrames = []
	for f in flatFrames:
		if not f['reject']: validFrames.append(f)
	flatDataArray = [ f['data'] for f in validFrames]
	if len(flatDataArray)<1: 
		print("No valid flats in the list.")
		print("...exit without success")
		sys.exit()

	flat = numpy.median(flatDataArray, axis = 0)
	amplifiedImage = generallib.percentiles(flat, 5, 95)
	matplotlib.pyplot.figure(figsize=(10,10/1.6))
	matplotlib.pyplot.imshow(amplifiedImage)
	matplotlib.pyplot.gca().invert_yaxis()
	matplotlib.pyplot.show(block=blocking)

	hdu = astropy.io.fits.PrimaryHDU(flat)
	hdul = astropy.io.fits.HDUList([hdu])
	hdul.writeto('flat.fits', overwrite=True)
	midx, midy = ( int(numpy.shape(flat)[0] / 2), int(numpy.shape(flat)[1] / 2))
	pixelRange = 15
	centralRegion = flat[midx-pixelRange:midx+pixelRange, midy-pixelRange:midy+pixelRange]
	print("Size of central sample:", numpy.shape(centralRegion),"or", numpy.shape(centralRegion)[0] * numpy.shape(centralRegion)[1],"pixels.")
	mean = numpy.mean(centralRegion)
	balance = numpy.divide(flat, mean)
	hdu = astropy.io.fits.PrimaryHDU(balance)
	hdul = astropy.io.fits.HDUList([hdu])
	hdul.writeto('balance.fits', overwrite=True)
		
	if arg.preview:
		ds9Command = ['ds9']
		ds9Command.append('flat.fits')
		ds9Command.append('-zscale')
		subprocess.Popen(ds9Command)

		#ds9Command = ['ds9']
		#ds9Command.append('balance.fits')
		#ds9Command.append('-zscale')
		#subprocess.Popen(ds9Command)
			
	sys.exit()
