# coding: utf-8
import time
import urllib2

from django.db import models
from django.contrib.gis.geos import GEOSGeometry

from prometapi.geoprocessing import get_coordtransform



SOS112_URL = '''http://spin.sos112.si/SPIN2/Javno/GIS/AktualniDogodki.aspx?ur=24&SkupinaID1=1&SkupinaID2=1&SkupinaID3=1&SkupinaID4=1&SkupinaID5=1&SkupinaID6=1&SkupinaID7=1&SkupinaID8=1&pseudo?%s&bbox=243700,-99000,755700,301000'''

ENCODING = 'utf-8'

class SOS112(models.Model):
    timestamp = models.DateTimeField(auto_now_add=True)
    original_data = models.TextField()
    json_data = models.TextField()


def fetch_sos112():
    url = SOS112_URL % (int(time.time() * 1000),)
    u = urllib2.urlopen(url)
    data = u.read()
    ts = time.time()
    return ts, data

def parse_sos112(timestamp, data):
    data = data.decode(ENCODING).strip()

    records = []
    lines = [i.strip() for i in data.split('\r\n')]
    keys = lines[0].lower().split('\t')

    geotransform = get_coordtransform()

    for line in lines[1:]:
        rec = dict(zip(keys, line.split('\t')))
        y, x = rec['point'].split(',')

        point = GEOSGeometry('SRID=3787;POINT (%s %s)' % (x, y))
        point.transform(geotransform)
        rec['x_wgs'] = point.x
        rec['y_wgs'] = point.y

        records.append(rec)

    json_data = {
        'updated': timestamp,
        'records': records,
        'copyright': u'Uprava RS za zaščito in reševanje',
    }

    return json_data

