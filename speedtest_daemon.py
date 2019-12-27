# -*- coding: utf-8 -*-

# SpeedTest Daemon - A daemon that monitors the internet speed.
# Copyright (C) 2019 Filippo Santarelli
# 
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
# 
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <https://www.gnu.org/licenses/>.

from subprocess import run, PIPE, DEVNULL, CalledProcessError
import argparse
import sys
import json
from time import time, sleep
import re
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.colors import to_rgba
from mpl_finance import candlestick_ochl


# Parse input arguments and provide help
parser = argparse.ArgumentParser()
parser.add_argument("time", type=int, help="Time the daemon will run (seconds)")
parser.add_argument("-o", "--output-file", type=str, help="Path to output file")
parser.add_argument("-d", "--delay", type=float, default=60, help="Time (seconds) between two consecutive measurements.")
parser.add_argument("--IPs", type=str, default="IPs.json", help="Path to JSON file with IPs dictionary.")
args = parser.parse_args()
del parser

# Record start time
start = int(time())
elapsed = int(time()) - start

# Set up common arguments
cmdargs = ['ping', '-c', '10', '-qn', '-i', '0.2']
with open(args.IPs, 'r') as f:
	ips = json.load(f)
speedcmdargs = ['speedtest-cli', '--single', '--simple']

# Setup the regex
# Example: round-trip min/avg/max/stddev = 15.732/87.589/162.111/49.175 ms
pattern = re.compile(".* = (?P<min>[\\d.]+)/(?P<avg>[\\d.]+)/(?P<max>[\\d.]+)/(?P<stddev>[\\d.]+) ms", re.DOTALL)
# Example:
# Ping: 184.681 ms
# Download: 5.27 Mbit/s
# Upload: 2.07 Mbit/s
speedpatt = re.compile('Ping: ([\\d.]+).*Download: ([\\d.]+).*Upload: ([\\d.]+)', re.DOTALL)

# Initialize visualization
colw = 10
speednames = ['Time', 'Ping', 'DownSpeed', 'UpSpeed']
names = ['Time', 'Minimum', 'Average', 'Maximum', 'Dev.Std.']
colsep = " | "
print(colsep.join([x.ljust(colw) for x in names]))
print(colsep.join(["".ljust(colw, '-') for _ in range(len(names))]))

# Initialize outputs
stats = []
speed = []

# Do stuff
while args.time < 0 or elapsed < args.time:
	try:
		curr_stats = []
		for name, ip in ips.items():
			try:
				text = run(cmdargs+[ip], stdout=PIPE, stderr=DEVNULL, check=True).stdout.decode(sys.stdout.encoding)
			except CalledProcessError as err:
				print(err, err.stdout)
				curr_stats.append([time(), *np.zeros((len(names),))])
			else:
				match = pattern.match(text)
				if match:
					curr_stats.append([time(), *[float(x) for x in match.groups()]])
					# Stdout visualization
					print(colsep.join([str(x).ljust(colw)[:colw] for x in curr_stats[-1]]), name)
				else:
					print("Couldn't match ping's output in: {}".format(text))
					curr_stats.append([time(), *np.zeros((4,))])
		# Speed test
		try:
			speedtext = run(speedcmdargs, stdout=PIPE, stderr=DEVNULL, check=True).stdout.decode(sys.stdout.encoding)
		except CalledProcessError as err:
			print(err, err.stdout)
			speed.append([time(), *np.zeros((len(speednames),))])
		else:
			speedmatch = speedpatt.match(speedtext)
			if speedmatch:
				speed.append([time(), *[float(x) for x in speedmatch.groups()]])
		# Stdout visualization
		print(colsep.join([str(x).ljust(colw)[:colw] for x in speed[-1]]), 'Speed test results')
		
		stats.append(curr_stats)
		sleep(args.delay)
		elapsed = int(time()) - start
	except KeyboardInterrupt:
		print("\nDaemon shut down by the user")
		break

# Convert to numpy array
arr = np.array(stats)
speed = np.array(speed)

# Save gathered information
if args.output_file:
	np.save(args.output_file, arr)
	np.save(args.output_file+'_speed', speed)

# Display a plot
colors = ['y','r','g','b','k']
for n, ipname in enumerate(ips.keys()):
	
	idx1 = 1 + n
	idx2 = 1 + len(ips)+1 + n
	
	# Prepare data for candlestick representation
	iparr = np.empty((arr.shape[0], arr.shape[2]))
	iparr[:,0] = arr[:,n,0]
	iparr[:,1] = arr[:,n,2] - arr[:,n,4]
	iparr[:,2] = arr[:,n,2] + arr[:,n,4]
	iparr[:,3] = arr[:,n,3]
	iparr[:,4] = arr[:,n,1]
	
	# Draw candlesticks
	ax = plt.subplot(2, len(ips)+1, idx1)
	candlestick_ochl(ax, iparr, colorup='g')
	plt.title(ipname)
	
	# Compute and draw histogram
	plt.subplot(2, len(ips)+1, idx2)
	plt.hist(arr[:,n,2], color='g')
	
# Plot download speed
plt.subplot(2, len(ips)+1, 1+len(ips))
plt.plot(speed[:,0], speed[:,2], color='b')
plt.title('Download speed')

# Plot upload speed
plt.subplot(2, len(ips)+1, 2*(1+len(ips)))
plt.plot(speed[:,0], speed[:,1], color='r')
plt.plot(speed[:,0], speed[:,3], color='g')
plt.title('Upload speed and ping')
	
plt.savefig(args.output_file+".pdf")
plt.show()
