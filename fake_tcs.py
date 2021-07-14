#!/usr/bin/env python3 

import sys, subprocess, os
import time

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


def getUserHome():
	homeDir = os.path.expanduser('~')
	return str(homeDir)

def getUsername():
	username = os.getlogin()
	return str(username)

if __name__ == "__main__":	
	print(bcolors.BOLD,"\tfake_tcs")
	print("\t", sys.argv)
	time.sleep(1)
	print(bcolors.ENDC)
	sys.exit()
