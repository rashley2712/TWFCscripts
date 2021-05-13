#!/usr/bin/python3
import argparse, subprocess, time, sys, json, pyfits, numpy

class flatDB:
	def __init__(self): 
		self.filename="flats.json"
		print("Creating an instance of the database")
		
	def createNew(self):
		self.db = { "cameraNames" : [ "TWFC1", "TWFC2"]}
		self.dump()
		
	def dump(self, filename="none"):
		if filename == "none": filename = self.filename
		else: self.filename = filename
		
		jsonFile = open(self.filename, 'wt')
		json.dump(self.db, jsonFile, indent=4)
		jsonFile.close()

	def load(self, filename="none"):
		if filename == "none": filename = self.filename
		else: self.filename = filename
		
		try:
			jsonFile = open(self.filename, 'rt')
			self.db = json.loads(jsonFile.read())
			jsonFile.close()
			information("...loaded from the file: " + str(self.filename))
		except Exception as e:
			# information(e)
			information("Unable to load: " + str(self.filename))
			information("...creating a new datafile from the defaults...")
			self.createNew()
			self.dump()
			
	def checkBiases(self):
		gotBiases = True
		biasesNeeded =[]
		for camera in self.db['cameraNames']:
			try: 
				biasFilename = self.db[camera]['bias'] 
			except KeyError:
				information("No bias saved for camera %s."%camera)
				gotBiases = False
				biasesNeeded.append(camera)
		return gotBiases, biasesNeeded

	def addEntry(self, camera, data): 
		try: 
			self.db[camera] = data
		except KeyError:
			self.db[camera] = {}
			self.db[camera] = data
		self.dump()
		
	def addFlat(self, camera, filter, data):
		keys = self.db.keys()
		for k in keys:
			print(k)
		try:
			self.db[camera][filter].append(data)
		except KeyError:
			self.db[camera][filter] = []
			self.db[camera][filter].append(data)
		self.dump()
			

def execute(command):
	commandParts = []
	for part in command.split(' '):
		commandParts.append(str(part))
	information("executing command: " + command)
	print(commandParts)
	subprocess.call(commandParts)
	cmd = subprocess.Popen(commandParts, stdout=subprocess.PIPE)
	stdoutStr = ""
	for line in cmd.stdout:
		stdoutStr+= str(line.decode('utf-8'))
	# cmd.terminate()
	return stdoutStr
	
		
def information(message, error=False):
	print(message)
	
def makeBias(camera):
	biasCommand = "indicam -b " + str(binning) + " bias " + camera
	stdoutStr = execute(biasCommand)
	for line in stdoutStr.split('\n'):
		if "Image saved as" in line:
			biasFilename = line.split(' ')[-1]
	information("Made a bias for %s, stored as %s."%(camera, biasFilename))
	median, minimum, maximum = getStats(biasFilename)
	print("bias median", median)	
	
	flatData.addEntry(camera, { "bias" : biasFilename, "biasMedian": median} )
	
def getFilenameFromStdout(stdoutStr):
	for line in stdoutStr.split('\n'):
		if "Image saved as" in line:
			filename = line.split(' ')[-1]
	return filename

def getStats(filename):
	h2=pyfits.open(filename)
	data2=h2[0].data
	median=numpy.median(numpy.median(data2, axis=0))
	maximum = numpy.max(data2)
	minimum = numpy.min(data2)
	h2.close()
	return float(maximum), float(minimum), float(median)

def getMedian(filename):
	h2=pyfits.open(filename)
	data2=h2[0].data
	median=numpy.median(numpy.median(data2, axis=0))
	h2.close()
	return median
	
def makeFlat(camera, filter, expTime):
	information("Taking a flat for %s, filter %s"%(camera, filter))
	flatCommand = "indicam -b " + str(binning) + " flat " + camera + " " + str(expTime)
	stdoutStr = execute(flatCommand)
	flatFilename = getFilenameFromStdout(stdoutStr)
	maximum, minimum, median = getStats(flatFilename)
	print(flatFilename, maximum, minimum, median)
	flatData.addFlat(camera, filter, { 'filename' : flatFilename, 'median': median, 'maximum': maximum, })
	
def checkExposureTime(camera, filter):
	checkExp = 1
	information("Checking exposure time for %s, filter %s"%(camera, filter))
	expCommand = "indicam -w \"[3200:6000,1800:4500]\" -b " + str(binning) + " run " + camera + " " + str(checkExp)
	print(expCommand)
	stdoutStr = execute(expCommand) 
	
	
if __name__ == "__main__":
	parser = argparse.ArgumentParser(description='Takes flats at morning and evening twilight for the TWFC cameras at the WHT.')
	parser.add_argument('-b', '--binning', type=int, default=1, help='Binning for the flats. Default is 1x1.' )	
	args = parser.parse_args()
	binning = args.binning
	binning = 4
	maxCounts = 50000
	countsAim = 35000
	minExposure = 0.5
	maxExposure = 45
	
	
	flatData = flatDB()
	flatData.load()
	gotAllBiases, biasesNeeded = flatData.checkBiases()
	if not gotAllBiases:
		information("Biases missing ... doing these first")
		for b in biasesNeeded:
			makeBias(b)

	checkExposureTime("TWFC1", "R")
	makeFlat("TWFC2", "R", 1)
	
	
	
	sys.exit()
	
	
	inputFile = open(args.cat, 'rt')
	for line in inputFile:
		fields = line.strip().split()

		# Go to the field
		gocat = fields[0]
		tcsCommand = ["gocat", gocat]
		print("Command:", tcsCommand)
		subprocess.call(tcsCommand)
		
		# Set the filter
		icsCommand = ["indicam", "filter", "TWFC1", "-f", "B"]
		print("Running:", icsCommand)
		subprocess.call(icsCommand)

		# Set the focus
		tcsCommand = ["focus", "0.53"]
		print("Command:", tcsCommand)
		subprocess.call(tcsCommand)
		time.sleep(10)

		# Expose the camera
		icsCommand = ["indicam", "-b", "2", "run", "TWFC1", "60"]
		print("Command:", icsCommand)
		subprocess.call(icsCommand)
		
		################################################################
	
		# Set the filter
		icsCommand = ["indicam", "filter", "TWFC1", "-f", "R"]
		print("Running:", icsCommand)
		subprocess.call(icsCommand)

		# Set the focus
		tcsCommand = ["focus", "0.53"]
		print("Command:", tcsCommand)
		subprocess.call(tcsCommand)
		time.sleep(10)

		# Expose the camera
		icsCommand = ["indicam", "-b", "2", "run", "TWFC1", "60"]
		print("Command:", icsCommand)
		subprocess.call(icsCommand)

		################################################################
	
		# Set the filter
		icsCommand = ["indicam", "filter", "TWFC1", "-f", "Sloan I"]
		print("Running:", icsCommand)
		subprocess.call(icsCommand)

		# Set the focus
		tcsCommand = ["focus", "1.06"]
		print("Command:", tcsCommand)
		subprocess.call(tcsCommand)
		time.sleep(10)

		# Expose the camera
		icsCommand = ["indicam", "-b", "2", "run", "TWFC1", "60"]
		print("Command:", icsCommand)
		subprocess.call(icsCommand)


		time.sleep(10)

	

