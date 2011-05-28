

# This entry is not the same as in the EPSG database, it's adjusted for
# 14 seconds to the west because of a bug in EPSG database. It should
# be resolved some time in the future, when the software packages
# include updated EPSG dataset.
#
# This entry here is more of a hack than a real solution, but is
# still a proper, valid and reasonably working hack.
#
# For more info what really happened see this thread
# http://lists.maptools.org/pipermail/proj/2009-February/004397.html
#
# http://www.map-reading.com/ch4-1.php

sl_wkt = '''
PROJCS["MGI / Slovene National Grid",
	GEOGCS["MGI",
		DATUM["Militar_Geographische_Institute",
			SPHEROID["Bessel 1841",6377397.155,299.1528128,
				AUTHORITY["EPSG","7004"]],
			TOWGS84[577.326,90.129,463.919,5.137,1.474,-9.297,2.4232],
			AUTHORITY["EPSG","6312"]],
		PRIMEM["Greenwich",0,
			AUTHORITY["EPSG","8901"]],
		UNIT["degree",0.0174532925199433,
			AUTHORITY["EPSG","9108"]],
		AUTHORITY["EPSG","4312"]],
	UNIT["metre",1,
		AUTHORITY["EPSG","9001"]],
	PROJECTION["Transverse_Mercator"],
	PARAMETER["latitude_of_origin",0],
	PARAMETER["central_meridian",15],
	PARAMETER["scale_factor",0.9999],
	PARAMETER["false_easting",500000],
	PARAMETER["false_northing",-5000000],
	AUTHORITY["EPSG","3787"],
	AXIS["Y",EAST],
	AXIS["X",NORTH]]
'''

def get_coordtransform():
	from django.contrib.gis.gdal.srs import SpatialReference, CoordTransform
	sl = SpatialReference('EPSG:3787')
	sl.import_wkt(sl_wkt)
	wgs = SpatialReference('EPSG:4326')
	trans = CoordTransform(sl, wgs)
	return trans
