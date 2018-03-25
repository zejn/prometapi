
from django.core.management.base import BaseCommand


class Command(BaseCommand):
	def handle(self, *args, **options):
		from prometapi.models import _dumps, fetch_promet, parse_promet, EnEvents, Events, Burja, Cameras, Counters
		import simplejson
		
		data = fetch_promet(
				language=u"sl_SI",
				contents=[u'dogodki', u'delo', u'kamere', u'stevci', u'burja']
			)

		try:
			full_json = parse_promet(data)
		except simplejson.decoder.JSONDecodeError:
			full_json = None

		dogodki = delo = kamere = stevci = burja = None
		if full_json:
			dogodki = [i for i in full_json['Contents'] if i['ContentName'] == 'dogodki']
			kamere = [i for i in full_json['Contents'] if i['ContentName'] == 'kamere']
			stevci = [i for i in full_json['Contents'] if i['ContentName'] == 'stevci']
			burja = [i for i in full_json['Contents'] if i['ContentName'] == 'burja']

		if full_json is None or not all([dogodki, kamere, stevci, burja]):
			e = Events(json_data=_dumps(full_json), original_data=data)
			e.save()
		else:
			json_templ = dict([(k, v) for k, v in full_json.items() if k != 'Contents'])
			json = json_templ.copy()
			json['Contents'] = dogodki
			e = Events(json_data=_dumps(json), original_data='')
			e.save()

			json = json_templ.copy()
			json['Contents'] = kamere
			ca = Cameras(json_data=_dumps(json), original_data='')
			ca.save()

			json = json_templ.copy()
			json['Contents'] = stevci
			co = Counters(json_data=_dumps(json), original_data='')
			co.save()

			json = json_templ.copy()
			json['Contents'] = burja
			b = Burja(json_data=_dumps(json), original_data='')
			b.save()


		data = fetch_promet(
				language=u"en_US",
				contents=[u'dogodki']
			)

		full_json = parse_promet(data)
		dogodki = [i for i in full_json['Contents'] if i['ContentName'] == 'dogodki']

		json_templ = dict([(k, v) for k, v in full_json.items() if k != 'Contents'])
		json = json_templ.copy()
		json['Contents'] = dogodki
		e = EnEvents(json_data=_dumps(json), original_data='')
		e.save()
