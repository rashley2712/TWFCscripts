#!/usr/bin/python3
import argparse, subprocess, time, sys, os, signal

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
	
def readFocusTable(filename):
	focusTable = {}
	try:
		focusFile = open(args.focus, 'rt')
		for line in focusFile:
			line = line.strip()
			if len(line)<2: continue
			if line[0]=='#': continue
			fields = line.split()
			filterName = str(fields[0])
			focusValue = float(fields[1])
			focusTable[filterName] = focusValue
		focusFile.close()
	except Exception as e: 
		print("You need to create a focus.dat file containing today's focus values for each filter.")
		sys.exit()

	return focusTable

def signal_handler(sig, frame):
	global commandHistory
	print(bcolors.ENDC)
	if commandHistory is not None:
		print("command history in command.log")
		commandHistory.close()
	sys.exit()

signal.signal(signal.SIGINT, signal_handler)

# Looks for a file called 'fake' in the local directory. If it finds it, it goes into simulation mode. All commands will be pre-pended with 'fake_'.
def checkFake():
	if os.path.exists("fake"): return True
	return False

if __name__ == "__main__":

	parser = argparse.ArgumentParser(description='Runs through a catalogue file, taking exposures.')
	parser.add_argument('cat', type=str, help='Catalogue file.' )	
	parser.add_argument('-f', '--filter', type=str, nargs='+', help="Filter(s). Specify which filter(s) to expose.")
	parser.add_argument('-c', '--camera', type=str, default="TWFC2", help="Which camera to use? TWFC1 or TWFC2. Default: TWFC2")
	parser.add_argument('--focus', type=str, default='focus.dat', help="Name of the file containing focus values. Default is focus.dat.")
	parser.add_argument('-e', '--exptime', type=float, nargs='+', help="Exposure time(s) in seconds for each filter.")
	parser.add_argument('-n', '--numexp', type=float, nargs='+', help="Number of exposures for each filter. Default is 1.")
	parser.add_argument('-b', '--binning', type=int, default=4, help="Binning. Default is 4x4.")
	args = parser.parse_args()
	camera = args.camera
	expTime = args.exptime
	binning = args.binning
	print(args)

	fake = checkFake()

	if args.filter is None:
		print("Please specify which filters you want with -f [filters]")
		sys.exit()
	filterNames = args.filter
	
	if args.exptime is None:
		print("Please specify the exposure times for each filter. Use the -e option.")
		sys.exit()
	if len(args.exptime)!=len(args.filter): 
		print("We need an exposure time for each filter.")
		sys.exit()
	expTimes = args.exptime

	if args.numexp is None:
		numExps = [ 1 for i in range(len(filterNames))]
	else:
		numExps = args.numexp	
	if len(numExps)!=len(args.filter): 
		print("We need a number of exposures for each filter.")
		sys.exit()
	
	# Read the focus values
	focusTable = readFocusTable(args.focus)
	
	# Present a summary to the observer
	print("OBSERVATION BLOCK\n+++++++++++++++++\n")
	print("Target: %s\tCamera: %s\tbinning: %d"%(args.cat, camera, binning))
	print()
	for (f, e, n) in zip(filterNames, expTimes, numExps):
		print("\tfilter: %s\tfocus: %.2f\texptime: %.2f\tnumexposures: %d"%(f, focusTable[f], e, n))
	print()
	if input("Does this look correct? (y/n) ") != "y":
		sys.exit()



	commandHistory = open("command.log", "wt")

	inputFile = open(args.cat, 'rt')
	for line in inputFile:
		fields = line.strip().split()

		# Go to the field
		target = fields[0]
		executeCommand("gocat %s"%target)

		for f, e, n in zip(filterNames, expTimes, numExps):
			# Set the filter
			executeCommand("indicam filter %s -f %s"%(camera, f))
			# Set the focus 
			focusValue = focusTable[f]	
			executeCommand("focus %.2f"%(focusValue))

			# Expose the camera
			executeCommand("indicam -b %d run %s %.2f -n %d"%(binning, camera, e, n))
		
	print("Command history in command.log")	
