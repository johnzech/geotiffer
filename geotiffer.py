import os, sys
import threading
import time
import ConfigParser
from gdal_wrappers.geoPDFlayers import LayerList
from gdal_wrappers.geoPDFneatline import Neatline
from gdal_wrappers.geoPDFwarp import Warp

class GeoTiffer(object):
	def __init__(self, file_or_dir, config_path='geotiffer.cfg'):
		self.pdf_list, self.source_dir = self.getPDFList(file_or_dir)
		if not self.initConfigParser(os.path.abspath(config_path)):
			print "ERROR reading config file"
		self.readConfigItems()

	def readConfigItems(self):
		self.layers = self.getConfigOption('layers').split(",")
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

		if self.getConfigOption('threaded').upper() in ['YES', 'Y', 'TRUE', 'T', 'ON']:
			self.threaded = True
		else:
			self.threaded = False

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

	def printPDFList(self):
		print " -- %s --" % self.source_dir
		for path in self.pdf_list:
			print "   %s" % path

	def getFullPath(self,path):
		return "%s\\%s" % (self.source_dir, path)

	def getCSVOutputPath(self, path):
		return "%s\\%s_output.csv" % (self.source_dir, path)

	def processNeatlines(self):
		for path in self.pdf_list:
			neatline = Neatline(self.getFullPath(path), self.getCSVOutputPath(path), self.x_trim_factor, self.y_trim_factor)
			neatline.outputToFile()

	def processWarps(self):
		if self.threaded:
			self.processWarpsThreaded()
		else:
			self.processWarpsSequential()

	def processWarpsThreaded(self):
		start_time = time.time()
		threads = {}
		for path in self.pdf_list:
			threads[path] = threading.Thread(target=self.processWarp, args=[path])
			threads[path].start()

		running = True
		while running:
			running = False
			for path, thread in threads.items():
				if thread.isAlive():
					running = True
			if running:
				print "Waiting for gdalwarp threads to process."
				time.sleep(2)

		duration = time.time() - start_time
		print "Warp Timer: %s" % duration

	def processWarpsSequential(self):
		start_time = time.time()
		for path in self.pdf_list:
			self.processWarp(path)
		duration = time.time() - start_time
		print "Warp Timer: %s" % duration

	def processWarp(self, path):
		warp = Warp(self.getFullPath(path), self.getCSVOutputPath(path), self.append_filename, self.layers, self.layers_include_exclude, self.dpi, self.fix_no_data)
		warp.executeGdalWarp()

	def cleanUpCSVOutputFiles(self):
		for path in self.pdf_list:
			os.unlink(self.getCSVOutputPath(path))

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
	geotiffer.cleanUpCSVOutputFiles()