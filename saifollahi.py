#!/usr/bin/python3
import argparse, subprocess, sys, signal, os, numpy

commandHistory = None
commandCounter = 1
fake = True

class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

def executeCommand(commandString):
	global commandHistory, commandCounter, fake
	print("[step %d] : %s"%(commandCounter, commandString))
	commandCounter+=1
	commandHistory.write(commandString)
	commandHistory.write("\n")
	commandHistory.flush()
	fields = [str(c) for c in commandString.split()]
	if fake: fields[0] = "fake_" + fields[0]
	subprocess.call(fields)

def logComment(comment):
	global commandHistory
	commandHistory.write("# " + comment)
	commandHistory.write("\n")
	commandHistory.flush()
	
	
def readFocusTable(filename):
	focusTable = {}
	focusFile = open(args.focus, 'rt')
	for line in focusFile:
		line = line.strip()
		if len(line)<3: continue
		if line[0]=='#': continue
		fields = line.split()
		filterName = str(fields[0])
		focusValue = float(fields[1])
		focusTable[filterName] = focusValue
	# print(focusTable)
	return focusTable

def signal_handler(sig, frame):
	global commandHistory
	print(bcolors.ENDC)
	if commandHistory is not None:
		print("command history in command.log")
		commandHistory.close()
	sys.exit(-1)

# Looks for a file called 'fake' in the local directory. If it finds it, it goes into simulation mode. All commands will be pre-pended with 'fake_'.
def checkFake():
	if os.path.exists("fake"): return True
	return False

if __name__ == "__main__":
	signal.signal(signal.SIGINT, signal_handler)
	parser = argparse.ArgumentParser(description='Performs a block observation for SW21021a16 (Saifollahi).')
	parser.add_argument('-f', '--filters', type=str, nargs="+", help="Filters")
	parser.add_argument('-c', '--camera', type=str, default="TWFC2", help="Which camera to use? TWFC1 or TWFC2. Default: TWFC2")
	parser.add_argument('--focus', type=str, default="focus.dat", help="Filename for a text file containing focus values (in mm). Default 'focus.dat'.")
	parser.add_argument('-e', '--exptimes', type=float, nargs="+", help="Exposure times for each filter.")
	parser.add_argument('-b', '--binning', type=int, default=4, help="Binning. Default is 4x4.")
	parser.add_argument('-d', '--ditherstep', type=int, default=1, help="Dither step to start on. Default is 1.")
	
	args = parser.parse_args()
	# print(args)
	
	fake = checkFake()
	if fake: print("\n    --= SIMULATION MODE =--\n")

	camera = args.camera
	binning = args.binning
	focusDat = args.focus

	if args.filters is None:
		print("Please specify which filters you want with -f [filters]. Separate each filter with a space.")
		sys.exit()
	filters = args.filters
	
	if args.exptimes is None:
		print("Please specify the exposure times for each of the filters. Separate each time with a space.")
		sys.exit()
	expTimes = args.exptimes


	# Read the focus values
	try:
		focusTable = readFocusTable(args.focus)
	except: 
		print("You need to create a focus.dat file containing today's focus values for each filter.")
		sys.exit()

	# Make the dither pattern
	dither = []
	ditherSize = 2
	ditherX = 5
	ditherY = 5
	for i in range(ditherX):
		for j in range(ditherY):
			x = ditherSize * (i - numpy.median(range(ditherX)))
			y = ditherSize * (j - numpy.median(range(ditherY)))
			dither.append((x, y))
	
	

	# Present a summary to the observer
	print("OBSERVATION BLOCK\n+++++++++++++++++\n")
	print("Target: %s\tCamera: %s\tbinning: %d"%("<current>", camera, binning))
	print()
	for (f, e) in zip(filters, expTimes):
		print("\tfilter: %s\tfocus: %.2f\texptime: %.2f"%(f, focusTable[f], e))
	print()
	print("Dither:", dither)
#if input("Does this look correct? (y/n) ") != "y":
	#	sys.exit()

	commandHistory = open("command.log", "wt")

	
	for ditherstep in range(1, len(dither)+1):
		i = ditherstep -1
		print("Dither step: ", ditherstep, " = ", dither[i])
		if args.ditherstep>ditherstep:
			print("skipping")
			continue
		# Offset to dither
		logComment("dither step %d : (%d, %d)"%(ditherstep, dither[i][0], dither[i][1]))
		executeCommand("offset arc %d %d"%dither[i])

		for f, e in zip(filters, expTimes):

			# Set the filter
			executeCommand("indicam filter %s -f %s"%(camera, f))

			# Set the focus
			focusValue = focusTable[f]	
			executeCommand("focus %.2f"%(focusValue))

			# Take the exposure
			executeCommand("indicam -b %d run %s %.2f -n %d"%(binning, camera, e, 1))


	sys.exit()	
	for number in range(numExps[0]): 
		for f, e in zip(filters, expTimes):

			# Set the filter
			executeCommand("indicam filter %s -f %s"%(camera, f))

			# Set the focus
			focusValue = focusTable[f]	
			executeCommand("focus %.2f"%(focusValue))

			executeCommand("indicam -b %d run %s %.2f -n %d"%(binning, camera, e, 1))
		
	print("command history in command.log")
	commandHistory.close()

	sys.exit()
