# geotiffer

## STATUS

Geotiffer is in early dev phase (pre-alpha at best)... use at your discretion.

## WHAT

Geotiffer is a geopdf to geotiff converter, built specifically to handle batch conversion. It is based on the topics covered in a USGS whitepaper titled "Converting US Topo GeoPDF® Layers to GeoTIFF"

In addition, support for GE Super Overlay output has been added (via gdal2tiles).

Currently, Geotiffer is being developed for use on Windows machines.

## WHO

Principal Author: John Zechlin

Credits: 
- Geotiffer uses Python, the GDAL library, and GDAL python bindings (http://gdal.org/).
- Geotiffer redistributes (GDAL 1.11.0, released 2014/04/16):
  - gdalwarp.exe 
  - gdal2tiles.py
  - gdalbuildvrt.exe
- Thanks to MotionDSP for sponsoring this effort (www.motiondsp.com)
- Also, thanks to Larry Moore (U.S.G.S) for writing this paper: http://nationalmap.gov/ustopo/documents/ustopo2gtif_current.pdf 

## HOW

To use...

Note: Obtain geoPDFs from https://store.usgs.gov, make sure you download one of the latest editions.

#### If running the python version:
1. You'll need these installed:
  - Python 2.6 or 2.7 variants
  - GDAL and Python bindings (the packages found here: http://www.gisinternals.com/query.html?content=filelist&file=release-1600-gdal-1-11-0-mapserver-6-4-1.zip
2. Run print_layers.py to confirm your map/maps have the layers you expect. Pass a file or a directory (if directory, all pdf files in the dir will be analyzed).
  - python print_layers.py <file_or_directory>
3. Review config items in config file, geotiffer.cfg (or create your own config file). Most notable is a list of layers you want to include. See below for more on config items.
4. Run geotiffer.py on a file or directory (works like print_layers.py) to produce geotiffs.
  - python geotiffer.py <file_or_directory> <config_file_path>

#### If running the portable version:
1. Run print_layers.exe to confirm your map/maps have the layers you expect. Pass a file or a directory (if directory, all pdf files in the dir will be analyzed).
  - print_layers.exe <file_or_directory>
2. Review config items in config file, geotiffer.cfg (or create your own config file). Most notable is a list of layers you want to include. See below for more on config items.
3. Run geotiffer.exe on a file or directory (works like print_layers.py) to produce geotiffs.
  - geotiffer.exe <file_or_directory> <config_file_path>

#### To build/bundle portable version:
1. You'll need:
  - py2exe
2. cd to geotiffer repo root directory
3. run the bundler (this must be run from the root directory of the repo - otherwise errors will occur)
  - python .\bundle.py

#### To "install" portable version:
1. unpack geotiffer.zip
2. use the exe files as needed (see above)
3. leave all dlls in the same directory as exe files
4. use on any windows computer (no install required)

## CONFIG ATTRIBUTES

#### layers
`layers = Map_Frame.Projection_and_Grids,Map_Collar,Map_Frame.Woodland,Images`
- comma separated list of layers to include/exclude (based on value of 'layers_mode')

#### layers_mode
`layers_mode = off`
- on/off, the layers listed in 'layers' will either be 'on' or 'off' (included or excluded)
- if value is 'on', only the listed layers are included
- if value is 'off', all layers except the listed layers are included

#### append_filename
`append_filename = geotiff`
- text to be appended to geotiff output files

#### dpi
`dpi = 300`
- dpi of output geofiff files
- this option impacts speed: start with a smaller dpi if you want to play around with other options before creating your final product

#### fix_no_data
`fix_no_data = off`
- when on, this option will attempt to remove all white from behind the countour lines
- this feature is experimental... more dev is needed to refine it
- do not use this if including imagery layer (unexpected results)

#### x_trim_factor
`x_trim_factor = 153`
- amount to crop the x axis (left and right sides)
- use this to remove edge artifacts within the given map(s) (extra whitespace, etc)

#### y_trim_factor
`y_trim_factor = 138`
- amount to crop the y axis (top and bottom)
- use this to remove edge artifacts within the given map(s) (extra whitespace, etc)

#### threaded
`threaded = True`
- toggle threaded processing

#### threads
`threads = 8`
- if threaded is on, define number of threads to use
- generally 2 threads per core is the max

#### edge_smoothing_factor
`edge_smoothing_factor = 10`
- edge smoothing will attempt to correct for "rotated" topo maps
- use if gaps appear at borders between stitched maps
- set to 0 to turn off

#### produce_tiles
`produce_tiles = yes`
- produce ge superoverlay
- turn off to save processing time

#### tiles_min_zoom
`tiles_min_zoom = 11`
- min zoom level for ge superoverlay

#### tiles_max_zoom
`tiles_max_zoom = 17`
- max zoom level for ge superoverlay
