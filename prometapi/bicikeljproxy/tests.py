
import unittest
import os, sys
import simplejson

from prometapi.bicikeljproxy.models import _parse_main_xml, _parse_station_xml

testdatadir = os.path.join(os.path.dirname(__file__), 'testdata')

class TestXMLParsing(unittest.TestCase):
	def runTest(self):
		
		main_data = open(os.path.join(testdatadir, 'carto.xml')).read()
		main_json = open(os.path.join(testdatadir, 'carto.json')).read()
		
		station_data = open(os.path.join(testdatadir, 'station_2.xml')).read()
		station_json = open(os.path.join(testdatadir, 'station_2.json')).read()
		
		a = _parse_main_xml(main_data)
		b = simplejson.loads(main_json)
		
		self.assertEqual(a, b, 'carto.xml does not match')
		
		a = _parse_station_xml(station_data)
		b = simplejson.loads(station_json)
		self.assertEqual(a, b, 'station_2.xml does not match')
