# *-* coding: utf-8 *-*
import datetime
import re
import os
import uuid

import simplejson
import time
import urllib
import requests

from prometapi.compat import urlopen, unicode_type, unichr_cast

import subprocess
from calendar import timegm
import xml.etree.ElementTree as ET

from django.db import models
from django.contrib.gis.geos import GEOSGeometry
from django.utils._os import safe_join
from django.utils.timezone import make_aware, utc
from django.conf import settings

from prometapi.encoders import encrypt
from prometapi.geoprocessing import get_coordtransform, find_coordtransform

PROMET_KEY = '1234567890123456'
URL_PROMET = 'http://promet.si/dc/agg'

COPYRIGHT_PROMET = u'Prometno-informacijski center za državne ceste'
URL_PROMET_EVENTS = 'http://promet.si/rwproxy/RWProxy.ashx?method=get&remoteUrl=http%3A//promet/events_pp'
URL_PROMET_CAMERAS = 'http://www.promet.si/rwproxy/RWProxy.ashx?method=GET&rproxytype=json&remoteUrl=http%3A//promet/cams_georss_si'
URL_PROMET_BURJA = 'http://promet.si/rwproxy/RWProxy.ashx?method=GET&rproxytype=json&remoteUrl=http%3A//promet/burja'
URL_PROMET_BURJAZNAKI = 'http://promet.si/rwproxy/RWProxy.ashx?method=GET&rproxytype=json&remoteUrl=http%3A//promet/burjaznaki'
URL_PROMET_COUNTERS = 'http://promet.si/rwproxy/RWProxy.ashx?method=get&remoteUrl=http%3A//promet/counters_si&rproxytype=json'

# prikljucki
# http://promet.si/rwproxy/RWProxy.ashx?method=GET&remoteUrl=http%3A//gis.dars.si/Realis.RMap/Realis.RMap.Content/dars/locations/ce_prpn_json.txt%3F_dc%3D1319314148590%26node%3Dynode-190
# razcepi
# http://promet.si/rwproxy/RWProxy.ashx?method=GET&remoteUrl=http%3A//gis.dars.si/Realis.RMap/Realis.RMap.Content/dars/locations/ce_rapn_json.txt%3F_dc%3D1319314157862%26node%3Dynode-191
# cestninske postaje
# http://promet.si/rwproxy/RWProxy.ashx?method=GET&remoteUrl=http%3A//gis.dars.si/Realis.RMap/Realis.RMap.Content/dars/locations/ce_cppn_json.txt%3F_dc%3D1319314182798%26node%3Dynode-191
# mejni prehodi
# http://promet.si/rwproxy/RWProxy.ashx?method=GET&remoteUrl=http%3A//gis.dars.si/Realis.RMap/Realis.RMap.Content/dars/locations/ce_mppn_json.txt%3F_dc%3D1319314003894%26node%3Dynode-193
# predori
# http://promet.si/rwproxy/RWProxy.ashx?method=GET&remoteUrl=http%3A//gis.dars.si/Realis.RMap/Realis.RMap.Content/dars/locations/ce_tupn_json.txt%3F_dc%3D1319314043278%26node%3Dynode-194
# pocivalisca
# http://promet.si/rwproxy/RWProxy.ashx?method=GET&remoteUrl=http%3A//gis.dars.si/Realis.RMap/Realis.RMap.Content/dars/locations/ce_popn_json.txt%3F_dc%3D1319314073348%26node%3Dynode-195

def get_lokacije_url(what):
    info_dict = {
        'prikljucki':	('ce_prpn_json.txt', 'ynode-189'),
        'razcepi':		('ce_rapn_json.txt', 'ynode-190'),
        'cestninske':	('ce_cppn_json.txt', 'ynode-192'),
        'mejni_prehodi':('ce_mppn_json.txt', 'ynode-193'),
        'predori':		('ce_tupn_json.txt', 'ynode-194'),
        'pocivalisca':	('ce_popn_json.txt', 'ynode-195'),
        }

    lokacija, node = info_dict[what]

    return 'http://promet.si/rwproxy/RWProxy.ashx?method=GET&remoteUrl=http%3A//gis.dars.si/Realis.RMap/Realis.RMap.Content/dars/locations/' + lokacija + '%3F_dc%3D' + str(int(time.time()*1000)) + '%26node%3D' + node


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

def deobfuscate(s):
    """
    The encoding consists of reordering and translating.

    Reordering:

    Step 1: take evenly positioned characters, this is the first part of result
    Step 2: take oddly positioned characters
    Step 3: reverse oddly positioned characters
    Step 4: add them to the string from step 1

    Example:

    s = '123456789'

    Step 1: resultstr = '13579'
    Step 2: oddly = '2468'
    Step 3: oddly = '8642'
    Step 4: resultstr = '135798642'

    Translating characters is done via a self-inverse function:

        f(x) = unichr((255 - ord(x)) % 65536)

    """
    assert isinstance(s, unicode_type), 'Parameter is not unicode.'
    s2 = s[::2] + s[1::2][::-1]
    return ''.join((unichr_cast((255 - ord(c)) % 65536) for c in s2))


def _decode(s):
    # decode
    if not isinstance(s, unicode_type):
        s = s.decode('utf-8')
    return deobfuscate(s)

def datetime_encoder(obj):
    if isinstance(obj, datetime.datetime):
        return obj.isoformat()
    else:
        raise TypeError('Object of type %s with value of %s is not JSON serializable' % (type(obj), repr(obj)))

def dump_data(model, day, use_new=True):
    from django.db import connection
    yday = day + datetime.timedelta(1)
    the_day = datetime.datetime(day.year, day.month, day.day, 0, 0, 0)

    dump_dir = safe_join(settings.DUMP_DIR, the_day.strftime('%Y-%m'))

    if not os.path.isdir(dump_dir):
        os.makedirs(dump_dir)

    if use_new and the_day >= datetime.datetime(2015, 7, 31):
        # transition to utc timestamps
        if the_day == datetime.datetime(2015, 7, 31):
            start = the_day
            end = make_aware(start, utc) + datetime.timedelta(1)
        else:
            start = make_aware(the_day, utc)
            end = start + datetime.timedelta(1)

        qs = model.objects.filter(timestamp__gte=start, timestamp__lt=end)

        if qs.count() == 0:
            return

        sql, params = qs.query.get_compiler('default').as_sql()
        dump_file = safe_join(dump_dir, the_day.strftime(model.__name__.lower() + '_%Y-%m-%d.csv'))
        dump_file_relative = os.path.join(the_day.strftime('%Y-%m'), the_day.strftime(model.__name__.lower() + '_%Y-%m-%d.csv'))

        cur = connection.cursor()
        copy_sql = 'COPY (' + sql + ') TO stdout WITH CSV HEADER;'
        full_sql = cur.cursor.mogrify(copy_sql, params)

        args = ['psql']
        if connection.settings_dict['USER']:
            args += ["-U", connection.settings_dict['USER']]
        if connection.settings_dict['HOST']:
            args.extend(["-h", connection.settings_dict['HOST']])
        if connection.settings_dict['PORT']:
            args.extend(["-p", str(connection.settings_dict['PORT'])])
        args += [connection.settings_dict['NAME']]

        cmd = args + ["-c", full_sql]

        f = open(dump_file, 'w')
        p = subprocess.Popen(cmd, stdout=f)
        p.wait()
        #cur.cursor.copy_expert(full_sql, f)
        f.close()

        p = subprocess.Popen(['/bin/gzip', '-9f', dump_file])
        p.wait()

        f = open(safe_join(settings.DUMP_DIR, the_day.strftime('%Y-%m.sha1sums')), 'a')
        p = subprocess.Popen(['/usr/bin/sha1sum', dump_file_relative + '.gz'], cwd=safe_join(settings.DUMP_DIR, '.'), stdout=f)
        p.wait()
        f.close()

        pks = [i[0] for i in qs.values_list('pk')]
        qn = connection.ops.quote_name
        sql = 'DELETE FROM ' + qn(model._meta.db_table) + \
            ' WHERE ' + qn(model._meta.pk.name) + \
            ' IN (' + ', '.join(['%s' for i in pks]) + ');'
        cur.execute(sql, pks)
        cur.execute('COMMIT;')
        #qs.delete()
    else:
        qs = model.objects.filter(timestamp__gte=the_day, timestamp__lt=the_day + datetime.timedelta(1))

        if qs.count() == 0:
            return

        sql, params = qs.query.get_compiler('default').as_sql()
        class Dumper(list):
            def __init__(self, sql, params):
                self.cur = connection.cursor()
                self.cur.execute(sql, params)
                self.labels = [i[0] for i in self.cur.cursor.description]

            def __nonzero__(self):
                return True

            def __iter__(self):
                return self

            def next(self):
                rec = self.cur.fetchone()
                if rec is not None:
                    obj_data = dict(zip(self.labels, rec))
                    return obj_data
                else:
                    raise StopIteration

        dumper = Dumper(sql, params)
        dump_file = safe_join(dump_dir, the_day.strftime(model.__name__.lower() + '_%Y-%m-%d.json'))

        f = open(dump_file, 'w')
        for frag in simplejson.JSONEncoder(default=datetime_encoder).iterencode(dumper):
            f.write(frag)
        f.close()

        os.system('/bin/gzip -9 %s' % dump_file)

        qs.delete()


################################
# Models

class Events(models.Model):
    timestamp = models.DateTimeField(auto_now_add=True, db_index=True)
    json_data = models.TextField(null=True, blank=True)
    original_data = models.TextField()

class EnEvents(models.Model):
    timestamp = models.DateTimeField(auto_now_add=True, db_index=True)
    json_data = models.TextField(null=True, blank=True)
    original_data = models.TextField()

class Cameras(models.Model):
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

class Prikljucki(models.Model):
    timestamp = models.DateTimeField(auto_now_add=True, db_index=True)
    json_data = models.TextField(null=True, blank=True)
    original_data = models.TextField()

class Razcepi(models.Model):
    timestamp = models.DateTimeField(auto_now_add=True, db_index=True)
    json_data = models.TextField(null=True, blank=True)
    original_data = models.TextField()

################################
# functions

def fetch(url, postdata=None):
    data = None
    if postdata is not None:
        data = urllib.urlencode(postdata)
    u = urlopen(url, data)
    obfuscated_data = u.read()
    return obfuscated_data

def fetch_promet(language, contents):
    post = {
        u'Contents': [],
        u'Language': language,
        u'Type': u'www.promet.si',
        u'Version': u'1.0',
        u'RunId': str(uuid.uuid4())
    }

    for name in contents:
        post['Contents'].append({u'ContentName': name, u'ModelVersion': 1})

    d = simplejson.dumps(post, sort_keys=True)
    encrypted = encrypt(d, PROMET_KEY)
    data = encrypted.encode('hex').upper()
    resp = requests.post(URL_PROMET, data=data)
    obfuscated_data = resp.content

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

def fetch_cameras():
    return fetch(URL_PROMET_CAMERAS, {})

def _date_to_epoch_matcher(m):
    """
    Dates are sometimes written in JSON as `new Date(2016, 6, 6, 23, 30, 59, 0)`. This grabs a regex matcher that
    groups the numbers and outputs an epoch integer string.
    """
    date = datetime.datetime(int(m.group(1)),       # Year
                             int(m.group(2)) + 1,    # Month (JS 0-indexed, PY 1-indexed)
                             int(m.group(3)),        # Day
                             int(m.group(4)),        # Hour
                             int(m.group(5)),        # Minute
                             int(m.group(6)),        # Second
                             int(m.group(7)))        # Millisecond
    epoch = datetime.datetime.utcfromtimestamp(0)
    return str(int((date - epoch).total_seconds() * 1000))


def events_to_2016_11(jsondata):
    content_data = {}
    new = {
        "ContentName": jsondata["ContentName"],
        "ModifiedTime": jsondata['ModifiedTime'],
        "IsModified": jsondata["IsModified"],
        "Language": jsondata["Language"],
        "Expires": jsondata['Expires'],
        "ETag": jsondata["ETag"],
        "Data": content_data,
    }

    content_data['ContentName'] = jsondata['Data']['properties']['ContentName']
    content_data['Language'] = jsondata['Data']['properties']['Language']
    items = content_data["Items"] = []

    keys = [u'Prioriteta',
             u'Title',
             # u'CrsId',
             u'isMejniPrehod',
             u'Cesta',
             u'Updated',
             u'IconW',
             u'Description',
             u'ContentName',
             u'IsRoadClosed',
             u'Stacionaza',
             u'Odsek',
             u'IconH',
             u'Icon',
             u'SmerStacionaza',
             u'PrioritetaCeste',
             u'VeljavnostOd',
             # u'Y',
             # u'X',
             u'SideContent',
             u'Kategorija',
             u'VeljavnostDo',
             u'Id']

    for feat in jsondata["Data"]["features"]:
        item = {}
        for k in keys:
            item[k] = feat["properties"][k]
        item['CrsId'] = feat['crs']['properties']['name']
        if feat['geometry']['type'] == 'Point':
            item['X'], item['Y'] = feat['geometry']['coordinates']
        try:
            uuid_int = str(uuid.UUID(item['Id']).int)
            item['Id'] = uuid_int
        except Exception:
            pass
        items.append(item)

    return new


def counters_to_2016_11(jsondata):
    content_data = {}
    new = {
        "ContentName": jsondata["ContentName"],
        "ModifiedTime": jsondata['ModifiedTime'],
        "IsModified": jsondata["IsModified"],
        "Language": jsondata["Language"],
        "Expires": jsondata['Expires'],
        "ETag": jsondata["ETag"],
        "Data": content_data,
    }
    content_data['ContentName'] = jsondata['Data']['properties']['ContentName']
    content_data['Language'] = jsondata['Data']['properties']['Language']
    items = content_data["Items"] = []

    keys = [
        u'ContentName',
        u'Description',
        u'Id',
        u'stevci_cestaOpis',
        u'stevci_lokacijaOpis',
        u'Title',
    ]

    stevciItems = {}

    for feat in jsondata["Data"]["features"]:
        stevec_id = feat["properties"]['stevci_lokacija']
        try:
            item = stevciItems[stevec_id]
        except KeyError:
            item = {}
            for k in keys:
                item[k] = feat["properties"][k]
            item['Icon'] = feat['properties']['GroupIcon']
            item['Data'] = []
            item['CrsId'] = feat['crs']['properties']['name']
            if feat['geometry']['type'] == 'Point':
                item['X'], item['Y'] = feat['geometry']['coordinates']
            stevciItems[stevec_id] = item
            items.append(item)

        stevec_data = {}
        for k in ['stevci_gap', 'stevci_statOpis', 'stevci_hit', 'stevci_stev', 'stevci_pasOpis', 'stevci_smerOpis', 'stevci_stat']:
            stevec_data[k] = unicode(feat['properties'][k]).replace('.', ',')

        icon_match = re.match('res/icons/stevci/stevec_(\d+)\.png', feat['properties']['Icon'])
        icon = ''
        if icon_match:
            icon = icon_match.group(1)

        item['Data'].append({
            'Id': feat['properties']['Id'],
            'Icon': icon,
            'properties': stevec_data,
        })

    return new


def burja_to_2016_11(jsondata):
    content_data = {}
    new = {
        "ContentName": jsondata["ContentName"],
        "ModifiedTime": jsondata['ModifiedTime'],
        "IsModified": jsondata["IsModified"],
        "Language": jsondata["Language"],
        "Expires": jsondata['Expires'],
        "ETag": jsondata["ETag"],
        "Data": content_data,
    }
    content_data['ContentName'] = jsondata['Data']['properties']['ContentName']
    content_data['Language'] = jsondata['Data']['properties']['Language']
    items = content_data["Items"] = []

    keys = [
        'ContentName',
        'Description',
        'Icon',
        'Id',
        'sunki',
        'Title',
        'veter',
    ]

    for feat in jsondata["Data"]["features"]:
        item = {}
        for k in keys:
            item[k] = feat["properties"][k]
        item['CrsId'] = feat['crs']['properties']['name']
        if feat['geometry']['type'] == 'Point':
            item['X'], item['Y'] = feat['geometry']['coordinates']
        items.append(item)

    return new


def cameras_to_2016_11(jsondata):
    content_data = {}
    new = {
        "ContentName": jsondata["ContentName"],
        "ModifiedTime": jsondata['ModifiedTime'],
        "IsModified": jsondata["IsModified"],
        "Language": jsondata["Language"],
        "Expires": jsondata['Expires'],
        "ETag": jsondata["ETag"],
        "Data": content_data,
    }
    content_data['ContentName'] = jsondata['Data']['properties']['ContentName']
    content_data['Language'] = jsondata['Data']['properties']['Language']
    items = content_data["Items"] = []

    keys = [
        'ContentName',
        'Icon',
        'Id',
        'Title',
    ]

    cameraGroups = {}

    for feat in jsondata["Data"]["features"]:
        groupid = feat['properties']['GroupId']
        try:
            item = cameraGroups[groupid]
        except KeyError:
            item = {}
            for k in keys:
                item[k] = feat["properties"][k]
            item['CrsId'] = feat['crs']['properties']['name']
            if feat['geometry']['type'] == 'Point':
                item['X'], item['Y'] = feat['geometry']['coordinates']
            item['Description'] = feat['properties']['Title']
            item['Id'] = feat['properties']['Title']
            item['Kamere'] = []
            items.append(item)
            cameraGroups[groupid] = item

        item['Kamere'].append({
            'Text': feat['properties']['Description'],
            'Image': feat['properties']['Image'].strip(),
            'Region': feat['properties']['Region'],
        })

    return new


def promet_to_2016_11(jsondata):
    v201611 = {
        u'Expires': jsondata[u'Expires'],
        u'ModelVersion': jsondata[u'ModelVersion'],
        u'ModifiedTime': jsondata[u'ModifiedTime'],
        u'RoutingVersion': jsondata[u'RoutingVersion'],
    }
    v201611[u'Contents'] = contents = []

    ctransforms = {
        u'dogodki': events_to_2016_11,
        u'stevci': counters_to_2016_11,
        u'burja': burja_to_2016_11,
        u'kamere': cameras_to_2016_11,
    }

    for c in jsondata[u'Contents']:
        typ = c[u'ContentName']
        try:
            transformed = ctransforms[typ](c)
        except KeyError as e:
            print(e)
            pass
        else:
            contents.append(transformed)

    return v201611


def parse_promet(obfuscated_data):
    decoded = _decode(obfuscated_data)
    upstream_json = _loads(decoded)

    _transform_3787 = get_coordtransform()
    _transform_3912 = find_coordtransform(u'EPSG:3912')

    def transform3787(x, y):
        si_point = GEOSGeometry('SRID=3787;POINT (%s %s)' % (x, y))
        si_point.transform(_transform_3787)
        return si_point.x, si_point.y

    def transform4326(x, y):
        return x, y

    def transform3912(x, y):
        si_point = GEOSGeometry('SRID=3912;POINT (%s %s)' % (x, y))
        si_point.transform(_transform_3912)
        return si_point.x, si_point.y

    transforms = {
        u'EPSG:2170': transform3787,
        u'EPSG:3912': transform3912,
        u'EPSG:4326': transform4326,
    }

    json = promet_to_2016_11(upstream_json)

    for category_obj in json['Contents']:
        for item in category_obj['Data']['Items']:
            crsid = item.get('CrsId')
            x, y = item.get('X'), item.get('Y')
            item['x_wgs'], item['y_wgs'] = transforms[crsid](x, y)

    now = timegm(datetime.datetime.utcnow().utctimetuple())
    json['updated'] = now
    json['copyright'] = COPYRIGHT_PROMET
    return json

def parse_cameras(obfuscated_data):
    decoded = _decode(obfuscated_data)

    # postprocess
    data = re.sub('new Date\((\d+),(\d+),(\d+),(\d+),(\d+),(\d+),(\d+)\)',
                    _date_to_epoch_matcher,
                    decoded)
    json = _loads(data[1:len(data) - 1])

    # WGS coordinate parsing
    for cam in json['feed']['entry']:
        if "georss_point" not in cam:
            continue
        points = cam["georss_point"].split()
        cam["y_wgs"] = float(points[0])
        cam["x_wgs"] = float(points[1])

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

    parkirisca = ET.fromstring(parkirisca_data)
    occupancy = ET.fromstring(occupancy_data)

    zattrs = ['ID_ParkiriscaNC', 'Cas', 'P_kratkotrajniki']
    zattrs.sort()
    zasedenost = {}

    for e in occupancy.findall('./ZASEDENOST'):
        zdict = dict([(i.tag, i.text) for i in e.getchildren()])
        assert list(sorted(zdict.keys())) == zattrs, 'occupancy.xml attributes changed!'
        zdict['Cas_timestamp'] = int(time.mktime(datetime.datetime.strptime(zdict['Cas'], '%Y-%m-%d %H:%M:%S').timetuple()))
        for k, v in zdict.items():
            if isinstance(v, str) and re.match('^\d+$', v):
                zdict[k] = int(v)
        zasedenost[zdict['ID_ParkiriscaNC']] = zdict

    assert len(zasedenost) > 1, 'Ni elementov v occupancy.xml?!'

    json = {'Parkirisca': [],}

    attrs = ['A_St_Mest', 'Cena_dan_Eur', 'Cena_mesecna_Eur', 'Cena_splosno', 'Cena_ura_Eur', 'ID_Parkirisca', 'ID_ParkiriscaNC', 'Ime', 'Invalidi_St_mest', 'KoordinataX', 'KoordinataY', 'Opis', 'St_mest', 'Tip_parkirisca', 'U_delovnik', 'U_sobota', 'U_splosno', 'Upravljalec']
    attrs.sort()
    geotransform = get_coordtransform()

    for p in parkirisca.findall('.//Parkirisca'):
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

def _transform_dataset(original_data):
    data = _loads(original_data)
    geotransform = get_coordtransform()
    for pr in data:
        si_point = GEOSGeometry('SRID=3787;POINT (%s %s)' % (pr['x'], pr['y']))
        si_point.transform(geotransform)
        pr['x_wgs'] = si_point.x
        pr['y_wgs'] = si_point.y

    return data

def fetch_prikljucki():
    url = get_lokacije_url('prikljucki')
    original_data = urlopen(url).read()

    json = {
        'updated': time.time(),
        'copyright': COPYRIGHT_PROMET,
        'prikljucki': _transform_dataset(original_data),
        }
    return original_data, json

def fetch_razcepi():
    url = get_lokacije_url('razcepi')
    original_data = urlopen(url).read()

    json = {
        'updated': time.time(),
        'copyright': COPYRIGHT_PROMET,
        'razcepi': _transform_dataset(original_data),
        }
    return original_data, json















