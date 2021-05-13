#!/usr/bin/env python3
import argparse, sys, numpy, os
import matplotlib.pyplot
import datetimelib
import photometrylib
import generallib
import astropy
import subprocess

if __name__ == "__main__":
	parser = argparse.ArgumentParser(description='Loads a FITS file bins it.')
	parser.add_argument('inputfile', type=str, nargs='+', help='File(s) to rebin.')
	parser.add_argument('-b', '--bin', type=int, default=2, help="New binning factor.")
	parser.add_argument('-o', '--output', type=str, default="auto", help="Name of the output file. By default it will add an _nxn suffix to the input filename.")
	arg = parser.parse_args()
	print(arg)

	for FITSfile in arg.inputfile:
		hdul = astropy.io.fits.open(FITSfile)
		header = hdul[0].header
		binning = "unknown"
		try:
			binning = header['CCDSUM']
		except KeyError:
			pass
		imageData = hdul[0].data
		
		print("Image dimensions:", numpy.shape(imageData))
		width = numpy.shape(imageData)[1]
		height = numpy.shape(imageData)[1]
		binningStrings = binning.split()
		binning = [ int(b) for b in binningStrings]
		print("Binning of original image: ", binning)
		hdul.close()

		rebin = arg.bin

		a = numpy.array(imageData)
		width = numpy.shape(a)[1]
		height = numpy.shape(a)[0]
		new_height = int(height/rebin)
		new_width = int(width/rebin)
		b = a.reshape(new_height, rebin, new_width, rebin)
		c = rebin*rebin * b.mean(axis=3).mean(axis=1)	
		d = numpy.clip(c, 0, 65535)

		print(a)
		print(d)
		print("Old shape:", numpy.shape(a), " New shape:",numpy.shape(d))
		
		hdr = astropy.io.fits.Header()
		hdu = astropy.io.fits.PrimaryHDU(d)
		header['CCDSUM'] = "%d %d"%(rebin, rebin)
		header['CCDXBIN'] = rebin
		header['CCDYBIN'] = rebin
		hdu.header = header
		

		if arg.output=="auto":
			filename = os.path.splitext(FITSfile)[0] + "_%dx%d"%(rebin,rebin) + os.path.splitext(FITSfile)[1]
		else:
			filename = arg.output 
		hdul = astropy.io.fits.HDUList([hdu])
		hdul.writeto(filename, overwrite=True)
		print("Written rebinned image to: %s"%filename)
	
	sys.exit()
