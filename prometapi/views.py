# coding: utf-8
import urllib

import simplejson
import dicttoxml
from django.http import HttpResponse
from django.shortcuts import render_to_response

from prometapi.models import EnEvents, Events, Cameras, Burja, BurjaZnaki, Counters, ParkiriscaLPT, _loads, \
    promet_to_2016_11
from prometapi.bicikeljproxy.models import BicikeljData
from prometapi.sos112.models import SOS112
from geoprocessing import get_coordtransform
from django.contrib.gis.geos import GEOSGeometry


class List(object):
    def __init__(self, model):
        self.model = model

    def __call__(self, request):
        return self.resp_latest(self.model.objects)

    def resp_latest(self, objects):
        e = objects.latest('timestamp')
        resp = HttpResponse(e.json_data, content_type='application/json')
        resp['Access-Control-Allow-Origin'] = '*'
        return resp


class EventsList(List):
    def __call__(self, request):
        language = request.GET.get('lang', 'sl')
        if language.lower() == 'en':
            model = EnEvents
        else:
            model = Events
        return self.resp_latest(model.objects)


events = EventsList(None)
cameras = List(Cameras)
burja = List(Burja)
burjaznaki = List(BurjaZnaki)
counters = List(Counters)
parkirisca_lpt = List(ParkiriscaLPT)
bicikelj = List(BicikeljData)
sos112 = List(SOS112)


def jsonresponse(func):
    def _inner(*args, **kwargs):
        request = args[0]
        format = request.GET.get('format', 'json')
        data = func(*args, **kwargs)
        if format == 'xml':
            return HttpResponse(dicttoxml.dicttoxml(data), content_type='application/xml')
        elif format == 'csv':
            # custom CSV format
            rows = []
            for k, v in data.items():
                if isinstance(v, (list, tuple)):
                    val = ','.join([str(i) for i in v])
                else:
                    val = v
                rows.append(";".join([k, val]))
            csv_str = "\n".join(rows)
            return HttpResponse(csv_str.encode('utf-8'), content_type='text/csv')
        return HttpResponse(simplejson.dumps(data, use_decimal=True, ensure_ascii=True), content_type='application/json')
    return _inner


@jsonresponse
def gk_to_wgs84(request):

    coords = map(request.GET.get, ['x', 'y'])

    if not all(coords):
        return {
            'status': 'fail',
            'error': 'Missing coordinates x and y as GET parameters.'
        }

    try:
        coords = map(float, coords)
    except ValueError:
        return {
            'status': 'fail',
            'error': 'Coordinates should be floats.'
        }

    xl, xh, yl, yh = 372543, 631496, 34152, 197602
    if not (xl <= coords[0] <= xh and yl <= coords[1] <= yh):
        return {
            'status': 'fail',
            'error': 'Coordinates (%s, %s) out of bounds: %d <= x <= %d and %d <= y <= %d.' % (coords[0], coords[1], xl, xh, yl, yh)
        }

    geotransform = get_coordtransform()
    point = GEOSGeometry('SRID=3787;POINT (%s %s)' % tuple(coords))
    point.transform(geotransform)
    transformed = (point.x, point.y)

    return {
        'status': 'ok',
        'gk': coords,
        'wgs84': transformed,
        'kml': point.kml,
    }


def debug_promet(request):
    from prometapi.encoders import decrypt
    from prometapi.models import PROMET_KEY
    import json

    context = {}
    if request.method == 'POST':
        encrypted_raw = request.POST.get('encrypted')
        encrypted = encrypted_raw.strip()
        if not set(encrypted.upper()) - set('0123456789ABCDEF'):
            print("hex decoding")
            encrypted = encrypted.decode('hex')

        print([encrypted])
        decoded = decrypt(encrypted, PROMET_KEY)
        decoded = urllib.unquote(decoded)
        decoded = decoded.rstrip('\x00')
        j = _loads(decoded)
        decoded = json.dumps(j, sort_keys=True, indent=4)
        print([decoded])
        context['encrypted'] = encrypted_raw
        context['decoded'] = decoded
    return render_to_response("debug_promet.html", context=context)


@jsonresponse
def debug_compat(request):
    import json

    with open('testdata/structure-2018-03.json') as f:
        data = json.load(f)

    return promet_to_2016_11(data)
