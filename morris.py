#!/usr/bin/python3
import argparse, subprocess, sys, signal, os

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
	parser = argparse.ArgumentParser(description='Performs a block observation (9 point dithering) for SW2021a19 (Morris).')
	parser.add_argument('-c', '--camera', type=str, default="TWFC2", help="Which camera to use? TWFC1 or TWFC2. Default: TWFC2")
	parser.add_argument('-e', '--exptime', default=10, type=float, help="Exposure time.")
	parser.add_argument('-b', '--binning', type=int, default=4, help="Binning. Default is 4x4.")
	parser.add_argument('-n', '--numcycles', type=int, default=1, help="Number of exposures. Default is 1. ")
	parser.add_argument('-d', '--dithersize', type=float, default=5, help="Dither size in arcseconds. Default is 5.")
	args = parser.parse_args()
	print(args)
	
	fake = checkFake()
	if fake: print("\n    --= SIMULATION MODE =--\n")

	camera = args.camera
	binning = args.binning
	expTime = args.exptime
	numCycles = args.numcycles
	
	
	if args.exptime is None:
		print("Please specify the exposure time.")
		sys.exit()
	expTime = args.exptime

	commandHistory = open("command.log", "wt")

	size = args.dithersize
	ninePointDither = [ [0, 0], [size, size], [size, 0], [size, -size], [0, -size], [-size, -size], [-size, 0], [-size, size], [0, size] ]
	#print(len(ninePointDither))
	print("Dither pattern is:", ninePointDither)
	
	for cycle in range(numCycles):
		print("Iteration %d of %d"%(cycle+1, numCycles))
		for offset in ninePointDither:
			executeCommand("offset arc %.1f %.1f"%(offset[0], offset[1]))
			executeCommand("indicam -b %d run %s %.2f -n %d"%(binning, camera, expTime, 1))

	sys.exit()

	# Run through the observing block
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
