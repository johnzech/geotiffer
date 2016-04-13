import os, sys
import threading
import time
import glob
import Queue
import ConfigParser
from gdal_wrappers.geoPDFlayers import LayerList
from gdal_wrappers.geoPDFneatline import Neatline
from gdal_wrappers.geoPDFwarp import Warp
from gdal_wrappers.superOverlay import SuperOverlay

class GeoTiffer(object):
	def __init__(self, file_or_dir, config_path='geotiffer.cfg'):
		self.pdf_list, self.source_dir = self.getPDFList(file_or_dir)
		if not self.initConfigParser(os.path.abspath(config_path)):
			print "ERROR reading config file"
		self.populateProcessingQueue()
		self.readConfigItems()

	def readConfigItems(self):
		self.layers = [layer.strip() for layer in self.getConfigOption('layers').split(",")]
		if self.getConfigOption('layers_mode').upper() in ['EXCLUDE','OFF','SKIP']:
			self.layers_include_exclude = 'off'
		else:
			self.layers_include_exclude = 'on'
		self.append_filename = self.getConfigOption('append_filename')
		self.dpi = self.getConfigOption('dpi')
		if self.getConfigOption('fix_no_data').upper() in ['YES', 'Y', 'TRUE', 'T', 'ON']:
			self.fix_no_data = True
		else:
			self.fix_no_data = False
		self.x_trim_factor = self.getConfigOption('x_trim_factor')
		self.y_trim_factor = self.getConfigOption('y_trim_factor')
		self.edge_smoothing_factor = self.getConfigOption('edge_smoothing_factor')

		if self.getConfigOption('threaded').upper() in ['YES', 'Y', 'TRUE', 'T', 'ON']:
			self.threaded = True
			self.thread_count = self.getConfigOption('threads')
		else:
			self.threaded = False

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
		if os.path.isdir(path):
			pdf_paths = []
			dir = os.path.abspath(path)
			for root, dirs, files in os.walk(path):
				for file in files:
					if file.endswith(".pdf"):
						pdf_paths.append(file)
				break
			return pdf_paths, dir
		elif path.endswith(".pdf"):
			return [os.path.basename(path)], os.path.dirname(os.path.abspath(path))
		else:
			return []

	def populateProcessingQueue(self):
		self.processingQueue = Queue.Queue()
		for path in self.pdf_list:
			self.processingQueue.put(path)

	def printPDFList(self):
		print " -- %s --" % self.source_dir
		for path in self.pdf_list:
			print "   %s" % path

	def getFullPath(self,path):
		return "%s\\%s" % (self.source_dir, path)

	def getCSVOutputPath(self, path):
		return "%s\\%s_output" % (self.source_dir, path)

	def processNeatlines(self):
		for path in self.pdf_list:
			neatline = Neatline(self.getFullPath(path), self.getCSVOutputPath(path), self.x_trim_factor, self.y_trim_factor, self.edge_smoothing_factor)
			neatline.processOutput()

	def processWarps(self):
		if self.threaded:
			self.processWarpsThreaded()
		else:
			self.processWarpsSequential()

		if self.produce_tiles:
			print "done with warps, starting with super overlay"
			overlay = SuperOverlay(self.source_dir, 'super', self.tiles_min_zoom, self.tiles_max_zoom)
			overlay.process()

	def processWarpsThreaded(self):
		start_time = time.time()
		threads = []
		pdfs_by_thread = self.getPartitionedPaths()

		for thread_id in range(1,int(self.thread_count)):
			path_list = pdfs_by_thread[thread_id-1]
			if len(path_list) > 0:
				thread = threading.Thread(target=self.processWarp, args=(path_list))
				threads.append(thread)

		for thread in threads:
			thread.start()

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
		pdfs_by_thread = []
		for thread_id in range(1, int(self.thread_count)):
			pdfs_by_thread.append([])

		thread_id = 1
		for path in self.pdf_list:
			pdfs_by_thread[thread_id].append(path)
			thread_id += 1
			if thread_id == self.thread_count:
				thread_id = 1
		return pdfs_by_thread

	def processWarpsSequential(self):
		start_time = time.time()
		for path in self.pdf_list:
			self.processWarp(path)
		duration = time.time() - start_time
		print "Warp Timer: %s" % duration

	def processWarp(self, path):
		warp = Warp(self.getFullPath(path), "%s.csv" %self.getCSVOutputPath(path), self.append_filename, self.layers, self.layers_include_exclude, self.dpi, self.fix_no_data)
		warp.executeGdalWarp()

		if self.edge_smoothing_factor > 0:
			self.processEdgeWarps(path)

	def processEdgeWarps(self,path):
		section_count = int(self.edge_smoothing_factor)
		for section in range(1,section_count):
			for file_prepend in ['top', 'right', 'left', 'bottom']:
				warp = Warp(self.getFullPath(path), "%s%s_%s_%s.csv" % (self.getCSVOutputPath(path),file_prepend,section,section_count), "%s_%s_%s_%s" % (self.append_filename, file_prepend,section,section_count), self.layers, self.layers_include_exclude, self.dpi, self.fix_no_data, 'z')
				warp.executeGdalWarp()

	def cleanup(self):
		for file in glob.glob("%s\\z*.tiff" % self.source_dir):
			os.unlink(file)
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

	geotiffer.printPDFList()
	geotiffer.processNeatlines()
	geotiffer.processWarps()
	geotiffer.cleanup()