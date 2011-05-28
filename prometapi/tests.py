import unittest
import os

testfile = lambda x: os.path.join(os.path.dirname(__file__), 'testdata', x)
obffile = lambda x: testfile(os.path.join('obfuscated', x))

class TestPrometDecoder(unittest.TestCase):
	def runTest(self):
		import codecs
		from django.test.client import Client
		from prometapi.models import parse_burja, parse_burjaznaki, parse_counters, parse_events, parse_parkirisca_lpt
		from prometapi.models import Burja, BurjaZnaki, Counters, Events, ParkiriscaLPT
		from prometapi.models import _decode, _loads, _dumps
		
		modls = {
			'burja': Burja,
			'burjaznaki': BurjaZnaki,
			'counters': Counters,
			'events': Events,
			}
		
		for fn in ('burja', 'burjaznaki', 'counters', 'events'):
			for n in (1, 2, 3):
				obf = open(obffile('%s_%s.txt' % (fn, n))).read()
				
				self.assertEqual(_decode(obf), codecs.open(obffile('%s_%s.json' % (fn, n)), 'r', 'utf-8').read(), 'obfuscated vs. json mismatch, %s_%s.json' % (fn, n))
				
				parser = locals()['parse_%s' % fn]
				json = parser(obf)
				self.assertEqual(type(json), type({}))
				
				m = modls[fn]
				obj = m(json_data=_dumps(json), original_data=obf.encode('zlib').encode('base64'))
				obj.save()
		
		# load parkirisca
		park = open(testfile('parkirisca_1.xml')).read()
		occu = open(testfile('occupancy_1.xml')).read()
		json = parse_parkirisca_lpt(park, occu)
		obj = ParkiriscaLPT(json_data=_dumps(json), original_data=_dumps([park, occu]).encode('zlib').encode('base64'))
		obj.save()
		
		# GET
		c = Client()
		
		resp = c.get('/promet/events/')
		self.assertEqual(resp.status_code, 200)
		json = _loads(resp.content)
		self.assertEqual(type(json), type({}))
		resp = c.get('/promet/burja/')
		self.assertEqual(resp.status_code, 200)
		json = _loads(resp.content)
		self.assertEqual(type(json), type({}))
		resp = c.get('/promet/burjaznaki/')
		self.assertEqual(resp.status_code, 200)
		json = _loads(resp.content)
		self.assertEqual(type(json), type({}))
		resp = c.get('/promet/counters/')
		self.assertEqual(resp.status_code, 200)
		json = _loads(resp.content)
		self.assertEqual(type(json), type({}))
		resp = c.get('/promet/parkirisca/lpt/')
		self.assertEqual(resp.status_code, 200)
		json = _loads(resp.content)
		self.assertEqual(type(json), type({}))
		
		
		

if __name__ == "__main__":
	class TestFetchAndParse(unittest.TestCase):
		def runTest(self):
			from prometapi import models
			
			for fn in ('burja', 'burjaznaki', 'counters', 'events'):
				fetcher = getattr(models, 'fetch_%s' % fn)
				resp = fetcher()
				parser = getattr(models, 'parse_%s' % fn)
				json = parser(resp)
				self.assertEqual(type(json), type({}))
	
	import sys
	sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
	os.environ['DJANGO_SETTINGS_MODULE'] = 'prometapi.settings'
	unittest.main()
