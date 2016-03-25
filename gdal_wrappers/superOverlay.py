import sys, os
import subprocess
from osgeo import gdal, ogr, osr
from collections import OrderedDict
from gdal2tiles import GDAL2Tiles

class SuperOverlay(object):
	def __init__(self, working_directory, output_name, min_zoom, max_zoom):
		self.working_directory = working_directory
		self.output_name = output_name
		self.min_zoom = min_zoom
		self.max_zoom = max_zoom

	def getInputPathString(self):
		return "%s\\*.tiff" % self.working_directory

	def getOutputVrt(self):
		return "%s\\%s.vrt" % (self.working_directory,self.output_name)

	def process(self):
		self.executeBuildVrt()
		self.executeGdal2Tiles()

	def executeBuildVrt(self):
		args= [
			'gdalbuildvrt',
			'-allow_projection_difference',
			self.getOutputVrt(),
			self.getInputPathString()
		]
		subprocess.call(args)

	def executeGdal2Tiles(self):
		args = [
			'-p', 
			'geodetic', 
			'-k', 
			'-z', 
			"%s-%s" % (self.min_zoom, self.max_zoom),
			self.getOutputVrt(), 
			self.working_directory
		]
		gdal2tiles = GDAL2Tiles(args)
		gdal2tiles.process()
