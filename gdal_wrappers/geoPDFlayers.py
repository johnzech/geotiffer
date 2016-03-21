import sys, os
from osgeo import gdal
from collections import OrderedDict

class LayerList(object):
	def __init__(self, filepath):
		self.filepath = filepath
		self.fileCount = 0
		self.layerCounts = OrderedDict()
		self.processGdalLayers()

	def processGdalLayers(self):
		if os.path.isdir(self.filepath):
			files = []
			for (dirpath, dirnames, filenames) in os.walk(self.filepath):
				for filename in filenames:
					if filename.lower().endswith(".pdf"):
						files.append(os.path.join(dirpath, filename))
						gdalObject = gdal.Open(os.path.join(dirpath, filename))
						layers = gdalObject.GetMetadata_List("LAYERS")
						self.appendLayers(layers)
				break
		else:
			gdalObject = gdal.Open(self.filepath)
			layers = gdalObject.GetMetadata_List("LAYERS")
			self.appendLayers(layers)

	def appendLayers(self, layers):
		self.fileCount += 1
		for layer in layers:
			trimmed = layer.split("=")[1]
			if trimmed in self.layerCounts:
				self.layerCounts[trimmed] += 1
			else:
				self.layerCounts[trimmed] = 1

	def printSummary(self):
		print "Total Files: %d" % self.fileCount
		print "----------------------------------------------"
		print "Count\tLayer"
		for name,count in self.layerCounts.items():
			print " %d\t %s" % (count, name)
		print "----------------------------------------------"


if __name__ == "__main__":
	targetFile = sys.argv[1]
	layerList = LayerList(targetFile)
	layerList.printSummary()
