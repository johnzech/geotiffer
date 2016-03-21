import sys
from gdal_wrappers.geoPDFlayers import LayerList
if __name__ == "__main__":
	targetFile = sys.argv[1]
	layerList = LayerList(targetFile)
	layerList.printSummary()