# *-* coding: utf-8 *-*
import datetime
import re
import os
import simplejson
import time
import urllib2
import lxml.etree

from django.db import models
from django.contrib.gis.geos import GEOSGeometry
from django.utils._os import safe_join
from django.conf import settings


from prometapi.decoder import dstr
from prometapi.geoprocessing import get_coordtransform

COPYRIGHT_PROMET = u'Prometno-informacijski center za državne ceste'
URL_PROMET_EVENTS = 'http://promet.si/rwproxy/RWProxy.ashx?method=get&remoteUrl=http%3A//promet/events_pp'
URL_PROMET_BURJA = 'http://promet.si/rwproxy/RWProxy.ashx?method=GET&rproxytype=json&remoteUrl=http%3A//promet/burja'
URL_PROMET_BURJAZNAKI = 'http://promet.si/rwproxy/RWProxy.ashx?method=GET&rproxytype=json&remoteUrl=http%3A//promet/burjaznaki'
URL_PROMET_COUNTERS = 'http://promet.si/rwproxy/RWProxy.ashx?method=get&remoteUrl=http%3A//promet/counters_si&rproxytype=json'
COPYRIGHT_LPT = u'Ljubljanska parkirišča in tržnice, d.o.o.'
URL_LPT_PARKIRISCA = 'http://www.lpt.si/uploads/xml/map/parkirisca.xml'
URL_LPT_OCCUPANCY = 'http://www.lpt.si/uploads/xml/traffic/occupancy.xml'

################################
# utility functions

def _loads(s):
	return simplejson.loads(s, use_decimal=True)

def _dumps(s):
	return simplejson.dumps(s, use_decimal=True, ensure_ascii=True)

def _datetime2timestamp(s):
	s[1] += 1 # javascript months = 0:11, python = 1:12
	dt = datetime.datetime(*s)
	return int(time.mktime(dt.timetuple()))

def _decode(s):
	# decode
	if not isinstance(s, unicode):
		s = s.decode('utf-8')
	return dstr(s)

def datetime_encoder(obj):
	if isinstance(obj, datetime.datetime):
		return obj.isoformat()
	else:
		raise TypeError, 'Object of type %s with value of %s is not JSON serializable' % (type(obj), repr(obj))

def dump_data(model, day):
	prevday = day
	yday = prevday + datetime.timedelta(1)
	the_day = datetime.datetime(prevday.year, prevday.month, prevday.day, 0, 0, 0)
	
	qs = model.objects.filter(timestamp__gte=the_day, timestamp__lt=the_day + datetime.timedelta(1))
	
	data = []
	
	for obj in qs:
		
		obj_data = {}
		for f in obj._meta.fields:
			obj_data[f.name] = getattr(obj, f.name)
		
		data.append(obj_data)
	
	dump_dir = safe_join(settings.DUMP_DIR, the_day.strftime('%Y-%m'))
	dump_file = safe_join(dump_dir, the_day.strftime(model.__name__ + '_%Y-%m-%d.json'))
	
	if not os.path.isdir(dump_dir):
		os.makedirs(dump_dir)
	
	f = open(dump_file, 'w')
	simplejson.dump(data, f, default=datetime_encoder)
	f.close()
	
	os.system('/bin/gzip -9 %s' % dump_file)
	
	qs.delete()


################################
# Models

class Events(models.Model):
	timestamp = models.DateTimeField(auto_now_add=True, db_index=True)
	json_data = models.TextField(null=True, blank=True)
	original_data = models.TextField()

class Burja(models.Model):
	timestamp = models.DateTimeField(auto_now_add=True, db_index=True)
	json_data = models.TextField(null=True, blank=True)
	original_data = models.TextField()

class BurjaZnaki(models.Model):
	timestamp = models.DateTimeField(auto_now_add=True, db_index=True)
	json_data = models.TextField(null=True, blank=True)
	original_data = models.TextField()

class Counters(models.Model):
	timestamp = models.DateTimeField(auto_now_add=True, db_index=True)
	json_data = models.TextField(null=True, blank=True)
	original_data = models.TextField()

class ParkiriscaLPT(models.Model):
	timestamp = models.DateTimeField(auto_now_add=True, db_index=True)
	json_data = models.TextField(null=True, blank=True)
	original_data = models.TextField()

################################
# functions

def fetch(url, postdata=None):
	u = urllib2.urlopen(url, postdata)
	obfuscated_data = u.read()
	return obfuscated_data

def fetch_events():
	return fetch(URL_PROMET_EVENTS, {})

def parse_events(obfuscated_data):
	decoded = _decode(obfuscated_data)
	
	# postprocess
	data = re.sub('new Date\((\d+)\)', r'\1', decoded)
	
	json = _loads(data)
	
	geotransform = get_coordtransform()
	for d in json['dogodki']['dogodek']:
		
		# convert geometric system
		point = GEOSGeometry('SRID=3787;POINT (%s %s)' % (d['x'], d['y']))
		point.transform(geotransform)
		d['x_wgs'] = point.x
		d['y_wgs'] = point.y
	
	json['updated'] = time.time()
	json['copyright'] = COPYRIGHT_PROMET
	return json

def fetch_burja():
	return fetch(URL_PROMET_BURJA)

def parse_burja(obfuscated_data):
	decoded = _decode(obfuscated_data)
	
	# postprocess
	data = re.sub('new Date\(([\d,]+)\)', r'[\1]', decoded)
	data = data.rstrip(')').lstrip('(')
	
	json = _loads(data)
	
	json['feed']['updated'] = _datetime2timestamp(json['feed']['updated'])
	for k in json['feed']['entry']:
		k['updated'] = _datetime2timestamp(k['updated'])
	
	json['updated'] = time.time()
	json['copyright'] = COPYRIGHT_PROMET
	return json

def fetch_burjaznaki():
	return fetch(URL_PROMET_BURJAZNAKI)

parse_burjaznaki = parse_burja
"""
def parse_burjaznaki(obfuscated_data):
	decoded = _decode(obfuscated_data)
	
	# postprocess
	data = re.sub('new Date\(([\d,]+)\)', r'[\1]', decoded)
	data = data.rstrip(')').lstrip('(')
	
	json = _loads(data)
	json['feed']['updated'] = _datetime2timestamp(json['feed']['updated'])
	for k in json['feed']['entry']:
		k['updated'] = _datetime2timestamp(k['updated'])
	
	return json
"""
def fetch_counters():
	return fetch(URL_PROMET_COUNTERS, {})

def parse_counters(obfuscated_data):
	decoded = _decode(obfuscated_data)
	
	# postprocess
	data = re.sub('new Date\(([\d,]+)\)', r'[\1]', decoded)
	data = data.rstrip(')').lstrip('(')
	
	json = _loads(data)
	json['feed']['updated'] = _datetime2timestamp(json['feed']['updated'])
	geotransform = get_coordtransform()
	for e in json['feed']['entry']:
		e['updated'] = _datetime2timestamp(e['updated'])
		
		# convert geo points to WGS84
		si_point = GEOSGeometry('SRID=3787;POINT (%s %s)' % (e['stevci_geoX'], e['stevci_geoY']))
		si_point.transform(geotransform)
		e[u'stevci_geoX_wgs'] = si_point.x
		e[u'stevci_geoY_wgs'] = si_point.y
	
	json['updated'] = time.time()
	json['copyright'] = COPYRIGHT_PROMET
	return json

def fetch_parkirisca_lpt():
	return fetch(URL_LPT_PARKIRISCA), fetch(URL_LPT_OCCUPANCY)

def parse_parkirisca_lpt(parkirisca_data, occupancy_data):
	
	# silly xmlns
	parkirisca_data = parkirisca_data.replace(' xmlns="http://www.tempuri.org/dsP.xsd"', '')
	
	parkirisca = lxml.etree.fromstring(parkirisca_data)
	occupancy = lxml.etree.fromstring(occupancy_data)
	
	zattrs = ['ID_ParkiriscaNC', 'Cas', 'P_kratkotrajniki']
	zattrs.sort()
	zasedenost = {}
	for e in occupancy.xpath('//ROOT/ZASEDENOST'):
		zdict = dict([(i.tag, i.text) for i in e.getchildren()])
		assert list(sorted(zdict.keys())) == zattrs, 'occupancy.xml attributes changed!'
		zdict['Cas_timestamp'] = int(time.mktime(datetime.datetime.strptime(zdict['Cas'], '%Y-%m-%d %H:%M:%S').timetuple()))
		for k, v in zdict.items():
			if isinstance(v, basestring) and re.match('^\d+$', v):
				zdict[k] = int(v)
		zasedenost[zdict['ID_ParkiriscaNC']] = zdict
	
	json = {'Parkirisca': [],}
	
	attrs = ['A_St_Mest', 'Cena_dan_Eur', 'Cena_mesecna_Eur', 'Cena_splosno', 'Cena_ura_Eur', 'ID_Parkirisca', 'ID_ParkiriscaNC', 'Ime', 'Invalidi_St_mest', 'KoordinataX', 'KoordinataY', 'Opis', 'St_mest', 'Tip_parkirisca', 'U_delovnik', 'U_sobota', 'U_splosno', 'Upravljalec']
	attrs.sort()
	geotransform = get_coordtransform()
	
	for p in parkirisca.xpath('//Parkirisca/Parkirisca'):
		pdict = dict([(i.tag, i.text) for i in p.getchildren()])
		
		for k, v in pdict.items():
			if isinstance(v, basestring) and re.match('^\d+$', v):
				pdict[k] = int(v)
		
		assert list(sorted(pdict.keys())) == attrs, "parkirisca.xml Attributes changed!?"
		if zasedenost.get(pdict['ID_ParkiriscaNC']) != None:
			pdict['zasedenost'] = zasedenost[pdict['ID_ParkiriscaNC']]
		
		# convert coords to WGS84
		if pdict['KoordinataX'] and pdict['KoordinataY']:
			si_point = GEOSGeometry('SRID=3787;POINT (%s %s)' % (pdict['KoordinataX'], pdict['KoordinataY']))
			si_point.transform(geotransform)
			pdict[u'KoordinataX_wgs'] = si_point.x
			pdict[u'KoordinataY_wgs'] = si_point.y
		
		json['Parkirisca'].append(pdict)
	
	json['updated'] = time.time()
	json['copyright'] = COPYRIGHT_LPT
	return json


