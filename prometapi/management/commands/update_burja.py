
from django.core.management.base import BaseCommand
from optparse import make_option

class Command(BaseCommand):
	def handle(self, *args, **options):
		from prometapi.models import _dumps, fetch_burja, parse_burja, Burja
		import simplejson
		
		data = fetch_burja()
		try:
			json = parse_burja(data)
		except simplejson.decoder.JSONDecodeError:
			json = None
		e = Burja(json_data=_dumps(json), original_data=data.encode('zlib').encode('base64'))
		e.save()
