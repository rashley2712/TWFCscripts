#!/usr/bin/python3
import argparse, subprocess, sys, signal, os

commandHistory = None
commandCounter = 1
fake = True

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
	parser = argparse.ArgumentParser(description='Performs a block observation for SW21021a07 (Chornay).')
	parser.add_argument('-t', '--target', type=str, help='Target name. (Must match the name in the TCS catalog). Optional... if not specified the script will not issue the ''GOCAT'' command')	
	parser.add_argument('-f', '--filters', type=str, nargs="+", help="Filters. Space separated list of filters.")
	parser.add_argument('-c', '--camera', type=str, default="TWFC2", help="Which camera to use? TWFC1 or TWFC2. Default: TWFC2")
	parser.add_argument('--focus', type=str, default="focus.dat", help="Filename for a text file containing focus values (in mm). Default 'focus.dat'.")
	parser.add_argument('-n', '--numexps', type=int, nargs="+", help="Number of exposures for each filter.")
	parser.add_argument('-e', '--exptimes', type=float, nargs="+", help="Exposure times for each filter.")
	parser.add_argument('-b', '--binning', type=int, default=4, help="Binning. Default is 4x4.")
	parser.add_argument('-r', '--repeat', type=int, default = 1, help="Repeat the entire observation block a number of times (but skipping the GOCAT command). Default is no repeats")
	args = parser.parse_args()
	# print(args)
	
	fake = checkFake()
	if fake: print("\n    --= SIMULATION MODE =--\n")

	skipGOCAT = False
	if args.target is None:
		skipGOCAT = True
		args.target = "<current pointing>"
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
	
	if args.numexps is None:
		print("Please specify the number of exposures for each of the filters. Separate each 'n' with a space.")
		sys.exit()
	numExps = args.numexps

	# Read the focus values
	focusTable = readFocusTable(args.focus)

	# Present a summary to the observer
	print("OBSERVATION BLOCK\n+++++++++++++++++\n")
	print("Target: %s\tCamera: %s\tbinning: %d"%(args.target, camera, binning))
	if args.repeat>1: print("Iterations: %d"%args.repeat)
	print()
	for (f, e, n) in zip(filters, expTimes, numExps):
		print("\tfilter: %s\tfocus: %.2f\texptime: %.2f\tnumexposures: %d"%(f, focusTable[f], e, n))
	print()
	if input("Does this look correct? (y/n) ") != "y":
		sys.exit()

	commandHistory = open("command.log", "wt")

	# GOCAT to the target
	if not skipGOCAT:
		executeCommand("gocat %s"%args.target)

	for repeat in range(args.repeat):
		# Run through the observing block
		if repeat>0:
			print("\n\tIteration: %d"%repeat)
		for f, e, n in zip(filters, expTimes, numExps):
			# Set the filter
			executeCommand("indicam filter %s -f %s"%(camera, f))

			# Set the focus
			focusValue = focusTable[f]	
			executeCommand("focus %.2f"%(focusValue))

			executeCommand("indicam -b %d run %s %.2f -n %d"%(binning, camera, e, n))
		
	print("command history in command.log")
	commandHistory.close()

	sys.exit()
