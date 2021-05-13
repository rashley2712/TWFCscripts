#!/usr/bin/env python3
import argparse, sys, numpy, os
import matplotlib.pyplot
import datetimelib
import photometrylib
import generallib
import astropy
import subprocess

if __name__ == "__main__":
	parser = argparse.ArgumentParser(description='Loads a FITS file and looks for hot pixels.')
	parser.add_argument('inputfile', type=str, nargs='+', help='File(s) to analyse.')
	parser.add_argument('-s', '--save', type=str, help="Save to the plot to a file.")
	parser.add_argument('-b', '--bias', type=str, help="Name of the bias frame.")
	parser.add_argument('--saturation', type=int, default=65535, help="Saturation level in ADU. Default is 65535.")
	parser.add_argument('--sigmafactor', type=int, default=10, help="n x sigma from the media will mean a bright pixel. Default is 10.")
	parser.add_argument('--noplot', action="store_true", help="Skips the plots.")
	parser.add_argument('--list', action="store_true", help="Filename is a text file with a list of files to be analysed.")
	parser.add_argument('-o', '--output', type=str, default="auto", help="Name of the output mask file. By default it will create filename of the form [camera]_[exp]_[bin].fits.gz.")
	
	#parser.add_argument('-p', '--pause', type=float, default=0.25, help="Number of seconds to pause on each plot.")
	#parser.add_argument('-i', '--interactive', action="store_true", help="Make each plot interactive (mouse to zoom, etc).")
	#parser.add_argument("--preview",  action="store_true", help="Preview each CCD in 'ds9'.")
	#parser.add_argument("-o", "--outputfilename", type=str, help="Output filename for the flat.")
	#parser.add_argument('-j', '--json', type=str, help="Save to a JSON file (specify filename).")
	arg = parser.parse_args()
	
	if arg.bias is not None:
		print("loading the bias frame", arg.bias)
		hdul = astropy.io.fits.open(arg.bias)
		bias = hdul[0].data
		hdul.close()

	saturation = arg.saturation
	sigmaFactor = arg.sigmafactor
	
	
	print(arg)

	pixelDB = []

	if arg.list:
		FITSFilenames = []
		# Load the list of files.
		filename = arg.inputfile[0]
		fileList = open(filename, 'r')
		for line in fileList:
			if len(line)>1: FITSFilenames.append(str(line.strip()))
	else:
		FITSFilenames = arg.inputfile

	print("Files to load:",FITSFilenames)

	for index, FITSfile in enumerate(FITSFilenames):
		if not arg.noplot: matplotlib.pyplot.figure(figsize=(10,10/1.62))
		hdul = astropy.io.fits.open(FITSfile)
		header = hdul[0].header
		expTime = "unknown"
		binning = "unknown"
		try:
			expTime = header['EXPTIME']
			binning = header['CCDSUM']
		except KeyError:
			continue
		imageData = hdul[0].data
		# Subtract the bias
		if arg.bias is not None: imageData = imageData - bias
		
		# Count the number of saturated pixels
		saturatedPixels = numpy.where(imageData == saturation)
		saturatedMask = numpy.array(imageData == saturation)
		pixels_x = []
		pixels_y = []
		colors = []
		for y, x in zip(saturatedPixels[0], saturatedPixels[1]):
			pixels_x.append(x)
			pixels_y.append(y)
			colors.append('r')

		numSaturated = len(pixels_x)
		dimensions = numpy.shape(imageData)
		totalPixels = numpy.shape(imageData)[0] * numpy.shape(imageData)[1]
		print("Image contains %d pixels."%totalPixels)
		print("Image contains %d saturated pixels."%numSaturated)
		median = numpy.median(imageData)
		stddev = numpy.std(imageData)
		print("median pixel value is %d ADU with a stdev of %.2f."%(median, stddev))
		medianClip = median + sigmaFactor*stddev
		brightPixels = numpy.where((imageData > medianClip) & (imageData !=saturation))
		brightMask = numpy.array((imageData > medianClip))
		numBright = len(brightPixels[0])
		for y, x in zip(brightPixels[0], brightPixels[1]):
			pixels_x.append(x)
			pixels_y.append(y)
			colors.append('y')
		print("%d pixels brighter than %.2f ADU which is %d times sigma above the median."%(numBright, medianClip,sigmaFactor))
		
		print("total hot pixels: %d, hot pixel fraction is %f%% where the exposure time is: %f"%((numBright+numSaturated), 100*(numBright+numSaturated)/totalPixels, expTime))

		amplifiedImage = generallib.percentiles(imageData, 5, 95)
		if not arg.noplot: 
			matplotlib.pyplot.imshow(amplifiedImage)
			matplotlib.pyplot.gca().invert_yaxis()
			# Draw circles around hot pixels
			from matplotlib.patches import Circle
			for xx,yy,cc in zip(pixels_x,pixels_y, colors):
				circ = Circle((xx,yy),5, edgecolor=cc, fill=False)
				matplotlib.pyplot.gca().add_patch(circ)	

		hotPixelMask = brightMask | saturatedMask

		if not arg.noplot: 
			if arg.save:
				matplotlib.pyplot.savefig(arg.save)
			matplotlib.pyplot.show(block=True)

		# Dump hot pixels to a text file
		pixelFile = os.path.splitext(FITSfile)[0] + "_pixels.dat"
		print("Dumping pixel list to: %s"%pixelFile)
		pixelWriter = open(pixelFile, 'wt')
		pixelWriter.write("# filename: %s\n# exptime: %f\n# binning: %s\n"%(FITSfile, expTime, binning))
		for x, y in zip(pixels_x, pixels_y):
			pixelWriter.write("%d, %d\n"%(x, y))
		pixelWriter.close()	

		# Add to the pixelDB
		pixelEntry = { "filename": FITSfile, "expTime": expTime, "binning": binning, "x": pixels_x, "y": pixels_y, "hotPixels": hotPixelMask }
		pixelDB.append(pixelEntry)
		print()

	# Compute common hot pixels
	overallMask = pixelDB[0]['hotPixels']
	for index in range(1, len(pixelDB)):
		overallMask = overallMask & pixelDB[index]['hotPixels']

	numHotPixels = numpy.sum(overallMask)
	print("Hot pixels common to all images: %d"%numHotPixels)
	commonPixels = numpy.where(overallMask)
	pixels_x = commonPixels[1]
	pixels_y = commonPixels[0]
	# Dump hot pixels to a text file
	pixelFile = "hotpixels.dat"
	print("Dumping pixel list to: %s"%pixelFile)
	pixelWriter = open(pixelFile, 'wt')
	for x, y in zip(pixels_x, pixels_y):
		pixelWriter.write("%d, %d\n"%(x, y))
	pixelWriter.close()	
	
	# Write the pixel mask to a FITS file
	ones = overallMask * 1.0
	if arg.output=="auto":
		filename = os.path.splitext(FITSfile)[0] + "_mask.fits.gz" 
	else:
		filename = arg.output 
	fitsmask = filename
	maskdump = numpy.array(ones, dtype=int)
	print("Dumping mask to %s"%fitsmask)
	print(numpy.shape(maskdump))
	hdu = astropy.io.fits.PrimaryHDU(maskdump)
	hdul = astropy.io.fits.HDUList([hdu])
	hdul.writeto(fitsmask, overwrite=True)
	
	sys.exit()
