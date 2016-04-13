import os, sys
import threading
import time
import glob
import Queue
import ConfigParser
from gdal_wrappers.geoPDFneatline import Neatline
from gdal_wrappers.geoPDFwarp import Warp
from gdal_wrappers.superOverlay import SuperOverlay

class GeoTiffer(object):
	def __init__(self, file_or_dir, config_path='geotiffer.cfg'):
		self.pdf_list, self.source_dir = self.getPDFList(file_or_dir)
		if not self.initConfigParser(os.path.abspath(config_path)):
			print "ERROR reading config file"
		self.readConfigItems()

	def readConfigItems(self):
		#layers
		self.layers = [layer.strip() for layer in self.getConfigOption('layers').split(",")]

		#layers mode
		if self.getConfigOption('layers_mode').upper() in ['EXCLUDE','OFF','SKIP']:
			self.layers_include_exclude = 'off'
		else:
			self.layers_include_exclude = 'on'

		#append filename
		self.append_filename = self.getConfigOption('append_filename')

		#dpi
		self.dpi = self.getConfigOption('dpi')

		#fix no data
		if self.getConfigOption('fix_no_data').upper() in ['YES', 'Y', 'TRUE', 'T', 'ON']:
			self.fix_no_data = True
		else:
			self.fix_no_data = False

		#x and y trim factors
		self.x_trim_factor = self.getConfigOption('x_trim_factor')
		self.y_trim_factor = self.getConfigOption('y_trim_factor')

		#edge smoothing
		self.edge_smoothing_factor = self.getConfigOption('edge_smoothing_factor')

		#threaded (and number of threads)
		if self.getConfigOption('threaded').upper() in ['YES', 'Y', 'TRUE', 'T', 'ON']:
			self.threaded = True
			self.thread_count = self.getConfigOption('threads')
		else:
			self.threaded = False

		#produce tiles (super overlay) switch
		if self.getConfigOption('produce_tiles').upper() in ['YES', 'Y', 'TRUE', 'T', 'ON']:
			self.produce_tiles = True
			self.tiles_min_zoom = self.getConfigOption('tiles_min_zoom')
			self.tiles_max_zoom = self.getConfigOption('tiles_max_zoom')
		else:
			self.produce_tiles = False

	def initConfigParser(self, path):
		configParser = ConfigParser.SafeConfigParser()
		if path is not None and os.path.isfile(path):
			configParser.read(path)
			self.configParser = configParser
			return True
		else:
			return False

	def getConfigOption(self, option):
		return self.configParser.get('geotiffer', option)

	def getPDFList(self, path):
		#path is either a directory or a single file
		if os.path.isdir(path):
			pdf_paths = []
			dir = os.path.abspath(path)
			#walk the first level of the directory to find all pdf files
			for root, dirs, files in os.walk(path):
				for file in files:
					if file.endswith(".pdf"):
						pdf_paths.append(file)
				#only want first level, so break
				break
			return pdf_paths, dir
		elif path.endswith(".pdf"):
			return [os.path.basename(path)], os.path.dirname(os.path.abspath(path))
		else:
			return []

	def printPDFList(self):
		print " -- %s --" % self.source_dir
		for path in self.pdf_list:
			print "   %s" % path

	def getFullPath(self,path):
		return "%s\\%s" % (self.source_dir, path)

	def getCSVOutputPath(self, path):
		return "%s\\%s_output" % (self.source_dir, path)

	def process(self):
		# complete all processing steps here
		self.printPDFList()
		self.processNeatlines()
		self.processWarps()
		self.processTiles()
		self.cleanup()

	def processNeatlines(self):
		# processing neatlines, the first step in the conversion
		# output of this process is a csv file that defines the desired crop
		# this process does not actually process the data, it only calculates the rectangle (the neatline)
		for path in self.pdf_list:
			neatline = Neatline(self.getFullPath(path), self.getCSVOutputPath(path), self.x_trim_factor, self.y_trim_factor, self.edge_smoothing_factor)
			neatline.processOutput()

	def processWarps(self):
		# this method acts as the switching mechanism (threaded or sequential processing)
		# see the next two methods
		if self.threaded:
			self.processWarpsThreaded()
		else:
			self.processWarpsSequential(self.pdf_list)

	def processWarpsThreaded(self):
		start_time = time.time()
		threads = []
		pdfs_by_thread = self.getPartitionedPaths()

		# setup x threads, passing a list of pdf paths into processWarpsSequential() for each thread
		for thread_id in range(0,int(self.thread_count)):
			path_list = pdfs_by_thread[thread_id-1]
			if len(path_list) > 0:
				thread = threading.Thread(target=self.processWarpsSequential, args=(path_list,))
				threads.append(thread)

		# start processing them all together
		for thread in threads:
			thread.start()

		# then, set up a loop and wait for all of them to finish
		# loop terminates when none of the threads' isAlive() calls return true
		running = True
		try:
			while running:
				running = False
				for thread in threads:
					if thread.isAlive():
						running = True
				if running:
					print "Waiting for gdalwarp threads to process."
					time.sleep(2)
		except KeyboardInterrupt:
			print "keyboardinterrupt"
			exit()

		duration = time.time() - start_time
		print "Warp Timer: %s" % duration

	def getPartitionedPaths(self):
		# divide pdf list evenly accross threads in preperatation for threaded processing
		# output is a 2d array (i.e. pdfs_by_thread[thread_id][pdf_path])
		pdfs_by_thread = []

		# first create the blank structure
		for thread_id in range(0, int(self.thread_count)):
			pdfs_by_thread.append([])

		# then, fill it with paths
		thread_id = 0
		for path in self.pdf_list:
			pdfs_by_thread[thread_id].append(path)
			thread_id += 1
			if thread_id == int(self.thread_count):
				thread_id = 0

		return pdfs_by_thread

	def processWarpsSequential(self, path_list):
		# for sequential processing, simply process all paths
		# also used by each thread in threaded mode
		start_time = time.time()
		for path in path_list:
			self.processWarp(path)
		duration = time.time() - start_time
		print "Warp Timer: %s" % duration

	def processWarp(self, path):
		# actual warp processing method, just sets up a Warp object and starts it with the given path
		warp = Warp(self.getFullPath(path), "%s.csv" %self.getCSVOutputPath(path), self.append_filename, self.layers, self.layers_include_exclude, self.dpi, self.fix_no_data)
		warp.executeGdalWarp()

		if self.edge_smoothing_factor > 0:
			self.processEdgeWarps(path)

	def processEdgeWarps(self,path):
		# process warps for edge smoothing (series of small samples along the edges)
		# these warp processes simply process small geotiffs based on a series of csv files
		# csv filenames are specifically encoded by the neatline process 
		# expected csv filename format: <baseCSVFilePath><top|right|left|bottom>_<section_number>_<section_count>.csv
		# Note: 'z' is appended to the filenames of these tiffs to facilitate cleanup of edge smoothing tiffs (see cleanup() below)
		section_count = int(self.edge_smoothing_factor)
		for section in range(1,section_count):
			for file_prepend in ['top', 'right', 'left', 'bottom']:
				warp = Warp(self.getFullPath(path), "%s%s_%s_%s.csv" % (self.getCSVOutputPath(path),file_prepend,section,section_count), "%s_%s_%s_%s" % (self.append_filename, file_prepend,section,section_count), self.layers, self.layers_include_exclude, self.dpi, self.fix_no_data, 'z')
				warp.executeGdalWarp()

	def processTiles(self):
		# super overlay creation
		# this processing step uses the geotiffs created during the warp processing
		if self.produce_tiles:
			print "done with warps, starting with super overlay"
			overlay = SuperOverlay(self.source_dir, 'super', self.tiles_min_zoom, self.tiles_max_zoom)
			overlay.process()
		else:
			print "super overlay (tiles) disabled, skipping"

	def cleanup(self):
		# cleanup the small tiffs used for edge smoothing
		for file in glob.glob("%s\\z*.tiff" % self.source_dir):
			os.unlink(file)
		# cleanup the neatline csv files
		for file in glob.glob("%s\\*.csv" % self.source_dir):
			os.unlink(file)

if __name__ == "__main__":
	try:
		target_file = sys.argv[1]
	except IndexError:
		print " >>>> ERROR: must provide filename or directory <<<<"
		sys.exit()

	try:
		config_file = sys.argv[2]
		geotiffer = GeoTiffer(target_file, config_file)
	except IndexError:
		geotiffer = GeoTiffer(target_file)

	geotiffer.process()
