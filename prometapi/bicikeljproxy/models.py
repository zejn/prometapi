from django.db import models
import lxml.etree
import datetime
import time
import sys
import urllib2
import foojson
import json

URL_CARTO = 'http://www.bicikelj.si/service/carto'
URL_STATION = 'http://www.bicikelj.si/service/stationdetails/ljubljana/%s'

class BicikeljData(models.Model):
	timestamp = models.DateTimeField(auto_now_add=True, db_index=True)
	json_data = models.TextField()

def _parse_main_xml(data):
	json = {}
	carto = lxml.etree.fromstring(data)
	
	count = 0
	for marker in carto.xpath('//carto/markers/marker'):
		assert len(marker.getchildren()) == 0, 'Marker has children!? ' + repr(marker.getchildren())
		station_id = unicode(marker.attrib['number'])
		json[station_id] = dict(marker.attrib)
	
		count += 1
	assert count > 0, 'No markers found in main XML!?'
	
	return json

def _parse_station_xml(data):
	sta_xml = lxml.etree.fromstring(data)
	sta_dict = {}
	for elem in sta_xml.xpath('//station/*'):
		sta_dict[elem.tag] = elem.text
	assert list(sorted(sta_dict.keys())) == ['available', 'connected', 'free', 'open', 'ticket', 'total', 'updated'], 'Missing or added keys in station XML!?'
	# backwards compatibility
	del sta_dict['connected']
	del sta_dict['open']
	del sta_dict['updated']
	return sta_dict

def fetch_xmls():
	main_xml = urllib2.urlopen(URL_CARTO, timeout=10).read()
	json = _parse_main_xml(main_xml)
	
	for k, v in json.iteritems():
		sta_xml_data = urllib2.urlopen(URL_STATION % k, timeout=10).read()
		sta_dict = _parse_station_xml(sta_xml_data)
		v['station'] = sta_dict
		v['station_valid'] = not int(sta_dict['total']) == 0
	
	now = datetime.datetime.now()
	resp = {
		'markers': json,
		'updated': time.mktime(now.timetuple())
		}
	return now, resp

def convert_citybikes(data):
	try:
		citybikes = json.loads(data)
	except ValueError, e:
		print >> sys.stderr, [data]
		raise
		
	markers = {}
	updateds = []
	
	for d in citybikes:
		st_id = d['id']
		u = datetime.datetime.strptime(d['timestamp'].rstrip('Z'), '%Y-%m-%dT%H:%M:%S.%f')
		updated = int(time.mktime(u.timetuple()))
		updateds.append(updated)
		lat = str(d['lat'])
		lng = str(d['lng'])
		markers[st_id] = {
			u'name': d['name'],
			u'fullAddress': d['name'],
			u'address': d['name'],
			u'number': st_id,
			u'station': {
				u'available': str(d['bikes']),
				u'free': str(d['free']),
				u'total': str(d['bikes'] + d['free']),
				u'ticket': '0',
				},
			u'lat': '%s.%s' % (lat[:2], lat[2:]),
			u'lng': '%s.%s' % (lng[:2], lng[2:]),
			u'station_valid': True,
			'updated': updated,
			'timestamp': d['timestamp'],
			u'address': d['name'],
			u'bonus': '0',
			u'open': '1',
		}
	resp = {
		'markers': markers,
		'updated': min(updateds),
		}
	return resp


"""

name
bonus
fullAddress
number
station
address
lat
lng
open
station_valid


"""
