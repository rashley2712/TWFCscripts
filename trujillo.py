#!/usr/bin/python3
import argparse, subprocess, time, sys


if __name__ == "__main__":
	parser = argparse.ArgumentParser(description='Runs through a catalogue file, taking exposures.')
	parser.add_argument('cat', type=str, help='Catalogue file.' )	
	parser.add_argument('-f', '--filter', type=str, help="Filter")
	parser.add_argument('-c', '--camera', type=str, default="TWFC2", help="Which camera to use? TWFC1 or TWFC2. Default: TWFC2")
	parser.add_argument('--focus', type=float, help="focus value (in mm) for the filter.")
	parser.add_argument('-e', '--exptime', type=float, default=180, help="Exposure time in seconds. Default is 180.")
	parser.add_argument('-b', '--binning', type=int, default=4, help="Binning. Default is 4\.")

	args = parser.parse_args()
	camera = args.camera
	expTime = args.exptime
	binning = args.binning
	# print(args)
	if args.filter is None:
		print("Please specify which filter you want with -f [filter]")
		sys.exit()
	filterName = args.filter
	
	if args.focus is None:
		print("Please specify the focus for the filter %s, with -focus [value]"%filterName)
		sys.exit()
	focus = args.focus

	# Set the filter
	icsCommand = ["indicam", "filter", camera, "-f", filterName]
	print("Running:", icsCommand)
	subprocess.call(icsCommand)

	# Set the focus
	tcsCommand = ["focus", str(focus)]
	print("Command:", tcsCommand)
	subprocess.call(tcsCommand)
	time.sleep(10)

	inputFile = open(args.cat, 'rt')
	for line in inputFile:
		fields = line.strip().split()

		# Go to the field
		gocat = fields[0]
		tcsCommand = ["gocat", gocat]
		print("Command:", tcsCommand)
		subprocess.call(tcsCommand)

		# Expose the camera
		icsCommand = ["indicam", "-b", str(binning), "run", camera, str(expTime)]
		print("Command:", icsCommand)
		subprocess.call(icsCommand)
		
	
