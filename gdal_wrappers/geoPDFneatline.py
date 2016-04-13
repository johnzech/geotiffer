import sys, os
from osgeo import gdal, ogr
from collections import OrderedDict

class Neatline(object):
	def __init__(self, input_file, output_file, x_trim_factor=120, y_trim_factor=100, edge_smoothing_factor=0):
		self.input_file = input_file
		self.output_file = output_file
		self.x_trim_factor = float(x_trim_factor)
		self.y_trim_factor = float(y_trim_factor)
		self.edge_smoothing_factor = edge_smoothing_factor
		self.processNeatline()

	def processNeatline(self):
		# neatline, aka a bounding box around the given topo map
		gdalObject = gdal.Open(self.input_file)
		self.neatline = gdalObject.GetMetadataItem("NEATLINE")
		self.geometry = ogr.CreateGeometryFromWkt(self.neatline)

		# max extents contains 4 values (max x and y, min x and y)
		self.max_extents = self.geometry.GetEnvelope()

	def processOutput(self):
		# set min and max by adding or subtracting trim factors
		self.minX = self.max_extents[0] + self.x_trim_factor
		self.maxX = self.max_extents[1] - self.x_trim_factor
		self.minY = self.max_extents[2] + self.y_trim_factor
		self.maxY = self.max_extents[3] - self.y_trim_factor

		# output polygon to csv file
		self.outputWKTToFile(self.createCutlinePolygonWkt(self.minX, self.maxX, self.minY, self.maxY))

		# if edge smoothing, create many more csv files to cover edge regions
		if self.edge_smoothing_factor > 0:
			self.processEdgeSmoothing()

	def processEdgeSmoothing(self):
		# for all four edges, divide into x cutlines (where x is the edge_smoothing_factor)
		section_count = int(self.edge_smoothing_factor)
		for section in range(1,section_count):
			# each call to createEdgeCutlines will produce 1 new neatline and csv for each side (left, right, top, bottom)
			self.createEdgeCutlines(section_count,section)

	def createEdgeCutlines(self, divide_by, section):
		# these cutlines are meant to fill in space left out of the scene due to overcropping of the main topo images
		# overcropping is necessary to avoid extra white regions around corners, but the tradeoff is missing data on 
		# the oposite corner. so this edge smoothing creates small rectangles around the corners with missing data. when
		# creating a superoverlay, these small rectangles will be merged with the rest of the scene to fill in the missing
		# gaps. subsequent calls to this method (with a fixed 'divide_by' value and a series of 'section' values) will
		# produce a series of smaller and smaller rectangles, producing a wedge (or technically, four wedges since we're
		# producing it for each side)

		# total width and height of the map
		x_total = self.maxX - self.minX
		y_total = self.maxY - self.minY

		# x and y trim (modified main trim factors)
		# generally speaking, this value: 
		# 		specifies the section width of the rectangles on the left and right
		#		specifies the section height of the rectangles on the top and bottom
		# these values will be closest to the main trim values near the corners
		# and decrease in height/width as they gradually approach the middle
		x_trim = self.calculateSteppedTrim(self.x_trim_factor,section)
		y_trim = self.calculateSteppedTrim(self.y_trim_factor,section)

		# section_width defines the width of the top/bottom sections 
		# section_height defines the height of the right/left sections
		# the number of sections ('divide_by') determines these
		# the total is multiplied by 2/3 to limit the wedge to 2/3 of 
		# the total width and height of the map
		section_width = x_total / 3 * 2 / divide_by
		section_height = y_total / 3 * 2 / divide_by

		# special case added for the four outermost corner sections
		# just a small amount of extra crop is needed in each corner
		corner_trim = 0
		if section == 1:
			corner_trim = 40

		# offsets help define the bounds of this individual rectangle
		# aka the position relative to the main bounding box
		offset = section - 1
		x_offset = section_width * offset
		y_offset = section_height * offset 

		# having calculated all of the above, we're ready to define our four rectangles for this section...

		# top
		minX = self.minX + x_offset + corner_trim
		maxX = self.minX + x_offset + section_width
		minY = self.maxY
		maxY = self.maxY + y_trim
		self.outputWKTToFile(self.createCutlinePolygonWkt(minX, maxX, minY, maxY), "top_%s_%s" % (section, divide_by))

		#right
		minX = self.maxX
		maxX = self.maxX + x_trim
		minY = self.maxY - y_offset - section_height
		maxY = self.maxY - y_offset - corner_trim
		self.outputWKTToFile(self.createCutlinePolygonWkt(minX, maxX, minY, maxY), "right_%s_%s" % (section, divide_by))

		#left
		minX = self.minX - x_trim
		maxX = self.minX
		minY = self.minY + y_offset + corner_trim
		maxY = self.minY + y_offset + section_height
		self.outputWKTToFile(self.createCutlinePolygonWkt(minX, maxX, minY, maxY), "left_%s_%s" % (section, divide_by))

		#bottom
		minX = self.maxX - x_offset - section_width
		maxX = self.maxX - corner_trim - x_offset
		minY = self.minY - y_trim
		maxY = self.minY
		self.outputWKTToFile(self.createCutlinePolygonWkt(minX, maxX, minY, maxY), "bottom_%s_%s" % (section, divide_by))

	def calculateSteppedTrim(self, trim_value, step):
		# stepped trim, modified based on position (step)

		# base case = 95% of the standard trim_value
		if step < 2:
			return .95 * trim_value

		# else, 70% of the previous section/step
		else:
			return .7 * self.calculateSteppedTrim(trim_value, step - 1)

	def createCutlinePolygonWkt(self,minX,maxX,minY,maxY):
		# create neatline based on min and max values
		cutline = ogr.Geometry(ogr.wkbLinearRing)
		wkbPolygon = ogr.Geometry(ogr.wkbPolygon)

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

	def outputWKTToFile(self, wkt, filename_prepend=''):
		with open("%s%s.csv" % (self.output_file,filename_prepend), 'wt') as file:
			file.write('id,WKT\n')
			file.write('1,"%s"\n' % wkt)

	def outputToFile(self):
		with open(self.output_file, 'wt') as file:
			file.write('id,WKT\n')
			file.write('1,"%s"\n' % self.getTrimmedWKT())

if __name__ == "__main__":
	targetFile = sys.argv[1]
	neatline = Neatline(targetFile, 'output.csv')
	neatline.printMaxExtents()
	neatline.outputToFile()