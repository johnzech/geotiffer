import sys, os
import subprocess
from osgeo import gdal, ogr, osr
from collections import OrderedDict

class Warp(object):
	def __init__(self, geopdf_input_file, csv_input_file, output_file_append, layers, layers_on_off, dpi, fix_nodata, z=''):
		self.geopdf_input_file = geopdf_input_file
		self.csv_input_file = csv_input_file
		self.output_file_append = output_file_append
		self.layers = layers
		self.layers_on_off = layers_on_off
		self.dpi = dpi
		self.fix_nodata = fix_nodata
		self.z = z

	def buildLayerString(self):
		return '%s' % ",".join(self.layers)

	def getOutputFile(self):
		dir = os.path.dirname(self.geopdf_input_file)
		base = os.path.basename(self.geopdf_input_file)
		return "%s\\%s_%s_%s.tiff" % (dir,self.z,base,self.output_file_append)

	def getGdalLayersOnOff(self):
		# either exclude the layers in self.layers or include only those layers
		if self.layers_on_off == 'off':
			return "GDAL_PDF_LAYERS_OFF"
		else:
			return "GDAL_PDF_LAYERS"

	def executeGdalWarp(self):
		args = [
			'gdalwarp',
			self.geopdf_input_file,
			self.getOutputFile(),
			'-crop_to_cutline',
			'-cutline',
			self.csv_input_file,
			'-overwrite',
			'--config',
			self.getGdalLayersOnOff(),
			self.buildLayerString(),
			'--config',
			'GDAL_PDF_DPI',
			str(self.dpi)
		]

		# fix no data, basically replace all white (255,255,255) with transparent (0,0,0)
		# this method produces mixed results (in other words, it could use improvement)
		if self.fix_nodata:
			args.extend([
				'-dstalpha',
				'-srcnodata',
				'255',
				'-dstnodata',
				'0'
			])
		subprocess.call(args)

if __name__ == "__main__":
	targetFile = sys.argv[1]
	warp = Warp(targetFile, 'output.csv', 'test_test_test', ["Map_Frame.Projection_and_Grids","Map_Collar","Map_Frame.Woodland"], 'off', 200)
	warp.executeGdalWarp()