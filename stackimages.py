#!/usr/bin/env python3
import argparse, sys, numpy
import matplotlib.pyplot
import generallib
import astropy.io.fits
import classes
import shift
from astropy.stats import sigma_clipped_stats
from photutils import datasets
from photutils import DAOStarFinder
import scipy
import subprocess
		
def onclick(event):
	global ix, iy
	ix, iy = event.xdata, event.ydata
	return None

if __name__ == "__main__":
	parser = argparse.ArgumentParser(description='Loads a list of FITS files and stacks them to a median/mean image.')
	parser.add_argument('inputfiles', type=str, help='A text file listing which files to load.')
	parser.add_argument('-s', '--save', type=str, help="Save to the plot to a file.")
	parser.add_argument('-S', '--skip', type=int, default=5, help="Number of frames to skip before starting the stacking.")
	parser.add_argument('-n', '--nframes', type=int, default=5, help="Number of frames to mean and median. Default value: 5.")
	parser.add_argument('-b', '--bias', type=str, help="Name of the bias frame.")
	parser.add_argument('-f', '--balance', type=str, help="Name of the balance (flat) frame.")
	parser.add_argument('-p', '--pause', type=float, default=0.01, help="Number of seconds to pause on each plot.")
	parser.add_argument('--shift', action="store_true", help="Find bright points and shift images to match before stacking.")
	parser.add_argument('--preview', action="store_true", help="Preview the output in DS9.")
	parser.add_argument('--border', type=int, default=0, help="Trim away this number of pixels from the edges.")
	
	arg = parser.parse_args()

	fileList = []

	listFile = open(arg.inputfiles, 'rt')
	for line in listFile:
		filename = line.strip()
		if filename[0] == '#': continue
		fileList.append(filename)
	listFile.close()

	print(fileList)

	if arg.bias is not None:
		print("loading the bias frame", arg.bias)
		hdul = astropy.io.fits.open(arg.bias)
		bias = hdul[0].data
		hdul.close()

	if arg.balance is not None:
		print("loading the balance frame", arg.balance)
		hdul = astropy.io.fits.open(arg.balance)
		balance = hdul[0].data
		hdul.close()

	medianFrameStack = []	
	startFrame = arg.skip+1
	endFrame = arg.skip + 1 + arg.nframes
	print("Building stack from frame %d to %d."%(startFrame, endFrame))
	offsets = []
	for frame in range(startFrame, endFrame): 
		index = frame - 1
		FITSfile = fileList[index]
		print("Frame number: {:d}, Filename: {}".format(frame, FITSfile))
	
		hdul = astropy.io.fits.open(FITSfile)
		# Put all of the headers into a dictionary object
		FITSHeaders = {}
		header = hdul[0].header
		for h in header:
			FITSHeaders[h] = header[h]
		imageData = hdul[0].data

		hdul.close()
		# Subtract the bias
		if arg.bias is not None: imageData = imageData - bias
		# Divide by the balance frame (apply the flat)
		if arg.balance is not None: imageData = numpy.divide(imageData, balance)

		# Trim away the vignetted regions	
		if arg.border>0:
			width = numpy.shape(imageData)[1]
			height = numpy.shape(imageData)[0]
			imageData = imageData[arg.border:height-arg.border, arg.border:width-arg.border]
			imageData = numpy.rot90(imageData)
		
		if arg.shift:
			if frame == startFrame:
				# Find the point sources
				mean, median, std = sigma_clipped_stats(imageData, sigma=3.0)
				daofind = DAOStarFinder(fwhm=3.0, threshold=5.*std)  
				sources = daofind(imageData - median)  
				for col in sources.colnames:
					sources[col].info.format = '%.8g'  # for consistent table output
				apertureList = classes.apertureDB()
				cat1 = []
				for s in sources:
					target = classes.apertureClass((s['xcentroid'], s['ycentroid']), s['peak'])
					apertureList.add(target)
				apertureList.sort()
				apertureList.enableTrackers(n=10)
				cat1 = numpy.array(apertureList.makeCatalog())
				#print(cat1)
			else:	
				# Find the point sources
				mean, median, std = sigma_clipped_stats(imageData, sigma=3.0)
				daofind = DAOStarFinder(fwhm=3.0, threshold=5.*std)  
				sources = daofind(imageData - median)  
				for col in sources.colnames:
					sources[col].info.format = '%.8g'  # for consistent table output
				apertureList = classes.apertureDB()
				cat2 = []
				for s in sources:
					target = classes.apertureClass((s['xcentroid'], s['ycentroid']), s['peak'])
					apertureList.add(target)
				apertureList.sort()
				apertureList.enableTrackers(n=10)
				cat2 = numpy.array(apertureList.makeCatalog())
				#print(cat2)
				dmax = 50
				fwhm = 4
				psize = 0.5
				mmax = 3
				img, xp,yp,xr,yr = shift.vimage(cat1, cat2, dmax, psize, fwhm)
				offset = { 'frame': frame, 'filesource': FITSfile, 'dx': xr, 'dy': yr}
				print(offset)
				offsets.append(offset)
				shiftedFrame = scipy.ndimage.shift(imageData, (xr, yr))
		else:	
			shiftFrame = imageData

		# Build the average frame
		if frame == startFrame: 
			average = imageData
			shiftedFrame = imageData
		else: average = numpy.add(average, shiftedFrame)
		medianFrameStack.append(shiftedFrame)
		
		amplifiedImage = generallib.percentiles(imageData, 5, 95)
		matplotlib.pyplot.imshow(amplifiedImage)
		matplotlib.pyplot.gca().invert_yaxis()
		matplotlib.pyplot.show(block=False)
		matplotlib.pyplot.pause(arg.pause)
		matplotlib.pyplot.clf()
	
	
	average = numpy.divide(average, arg.nframes)
	medianFrame = numpy.median(medianFrameStack, axis=0)
	amplifiedImage = generallib.percentiles(medianFrame, 5, 95)
	
	fig = matplotlib.pyplot.figure(figsize=(12/1.6, 12))
	matplotlib.pyplot.imshow(amplifiedImage)
	matplotlib.pyplot.gca().invert_yaxis()
	matplotlib.pyplot.draw()
	if arg.save:
		print("Saving image to {}".format(arg.save))
		matplotlib.pyplot.savefig(arg.save)

	matplotlib.pyplot.show(block=True)

	hdr = astropy.io.fits.Header()
	hdu = astropy.io.fits.PrimaryHDU(medianFrame)
	hdul = astropy.io.fits.HDUList([hdu])
	hdul.writeto('median.fits', overwrite=True)

	if arg.preview:
			ds9Command = ['ds9']
			ds9Command.append('median.fits')
			ds9Command.append('-zscale')
			subprocess.Popen(ds9Command)
		


	sys.exit()
