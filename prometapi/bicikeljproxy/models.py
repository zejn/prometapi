from django.db import models
import lxml.etree
import datetime
import time
import urllib2
import foojson

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
	assert list(sorted(sta_dict.keys())) == ['available', 'free', 'ticket', 'total'], 'Missing or added keys in station XML!?'
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
	citybikes = foojson.loads(data)
	markers = {}
	updateds = []
	
	for d in citybikes:
		st_id = d['id']
		u = datetime.datetime.strptime(d['timestamp'], '%Y-%m-%d %H:%M:%S.%f')
		updated = int(time.mktime(u.timetuple()))
		updateds.append(updated)
		markers[st_id] = {
			'name': d['name'],
			'fullAddress': d['name'],
			'number': st_id,
			'station': {
				'available': d['bikes'],
				'free': d['free'],
				'total': d['bikes'] + d['free']
				},
			'lat': '%s.%s' % (d['lat'][:2], d['lat'][2:]),
			'lng': '%s.%s' % (d['lng'][:2], d['lng'][2:]),
			'station_valid': True,
			'updated': updated,
			'timestamp': d['timestamp'],
		}
	resp = {
		'markers': markers,
		'updated': min(updateds),
		}
	return resp

