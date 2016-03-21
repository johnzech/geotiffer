# geotiffer

## STATUS

	Geotiffer is in early dev phase (pre-alpha at best)... use at your discretion.

## WHAT

	Geotiffer is a geopdf to geotiff converter, built specifically to handle batch conversion. It is based on the topics covered in a USGS whitepaper titled "Converting US Topo GeoPDF® Layers to GeoTIFF"

	Currently, Geotiffer is being developed for use on Windows machines.

## WHO

	Principal Author: John Zechlin

	Credits: 
		- Geotiffer uses Python, the GDAL library, and GDAL python bindings (http://gdal.org/).
		- Thanks to MotionDSP for sponsoring this effort (www.motiondsp.com)
		- Also, thanks to Larry Moore (U.S.G.S) for writing this paper: http://nationalmap.gov/ustopo/documents/ustopo2gtif_current.pdf

## HOW

	To use...

	obvious pre step: Obtain geoPDFs from https://store.usgs.gov, make sure you download one of the latest year's mapserver-6-4-1

	If running the python version:
		1. You'll need these installed:
			-Python 2.6 or 2.7 variants
			-GDAL and Python bindings (the ones found here: http://www.gisinternals.com/query.html?content=filelist&file=release-1600-gdal-1-11-0-mapserver-6-4-1.zip
		2. Run print_layers.py to confirm your map/maps have the layers you expect. Pass a file or a directory (if directory, all pdf files in the dir will be analyzed).
			- python print_layers.py <file_or_directory>
		3. Review config items in config file, geotiffer.cfg (or create your own config file). Most notable is a list of layers you want to include.
		4. Run geotiffer.py on a file or directory (works like print_layers.py) to produce geotiffs.
			- python geotiffer.py <file_or_directory> <config_file_path>

	If running the portable version:
		1. Run print_layers.exe to confirm your map/maps have the layers you expect. Pass a file or a directory (if directory, all pdf files in the dir will be analyzed).
			- print_layers.exe <file_or_directory>
		3. Review config items in config file, geotiffer.cfg (or create your own config file). Most notable is a list of layers you want to include.
		4. Run geotiffer.exe on a file or directory (works like print_layers.py) to produce geotiffs.
			- geotiffer.exe <file_or_directory> <config_file_path>

	To build/install portable version:
		TODO: write steps
