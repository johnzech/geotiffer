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
		# two steps to producing tiles from tiffs

		# step 1: create a virtual 'mosaic' of any tiffs in the working directory
		self.executeBuildVrt()

		# step 2: pass the vrt (from step 1) to gdal2tiles
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
			'-p', # profile
			'geodetic', # profile = geodetic
			'-k', # kml output flag (creates superoverlay kml file)
			'-z', # zoom levels
			"%s-%s" % (self.min_zoom, self.max_zoom), # zoom levels = min-max
			self.getOutputVrt(), 
			self.working_directory
		]
		gdal2tiles = GDAL2Tiles(args)
		gdal2tiles.process()
