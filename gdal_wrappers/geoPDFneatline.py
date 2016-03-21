import sys, os
from osgeo import gdal, ogr
from collections import OrderedDict

class Neatline(object):
	def __init__(self, input_file, output_file, x_trim_factor=120, y_trim_factor=100):
		self.input_file = input_file
		self.output_file = output_file
		self.x_trim_factor = float(x_trim_factor)
		self.y_trim_factor = float(y_trim_factor)
		self.processNeatline()

	def processNeatline(self):
		gdalObject = gdal.Open(self.input_file)
		self.neatline = gdalObject.GetMetadataItem("NEATLINE")
		self.geometry = ogr.CreateGeometryFromWkt(self.neatline)
		self.max_extents = self.geometry.GetEnvelope()

	def getTrimmedWKT(self):
		cutline = ogr.Geometry(ogr.wkbLinearRing)
		wkbPolygon = ogr.Geometry(ogr.wkbPolygon)

		minX = self.max_extents[0] + self.x_trim_factor
		maxX = self.max_extents[1] - self.x_trim_factor
		minY = self.max_extents[2] + self.y_trim_factor
		maxY = self.max_extents[3] - self.y_trim_factor

		cutline.AddPoint(minX,maxY)
		cutline.AddPoint(maxX,maxY)
		cutline.AddPoint(maxX,minY)
		cutline.AddPoint(minX,minY)
		wkbPolygon.AddGeometry(cutline)

		return wkbPolygon.ExportToWkt()

	def printMaxExtents(self):
		print "Min X = %s" % self.max_extents[0]
		print "Max X = %s" % self.max_extents[1]
		print "Min Y = %s" % self.max_extents[2]
		print "Max Y = %s" % self.max_extents[3]

	def outputToFile(self):
		with open(self.output_file, 'wt') as file:
			file.write('id,WKT\n')
			file.write('1,"%s"\n' % self.getTrimmedWKT())

if __name__ == "__main__":
	targetFile = sys.argv[1]
	neatline = Neatline(targetFile, 'output.csv')
	neatline.printMaxExtents()
	neatline.outputToFile()