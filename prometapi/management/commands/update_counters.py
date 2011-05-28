
from django.core.management.base import BaseCommand
from optparse import make_option

class Command(BaseCommand):
	def handle(self, *args, **options):
		from prometapi.models import _dumps, fetch_counters, parse_counters, Counters
		import simplejson
		
		data = fetch_counters()
		try:
			json = parse_counters(data)
		except simplejson.decoder.JSONDecodeError:
			json = None
		e = Counters(json_data=_dumps(json), original_data=data.encode('zlib').encode('base64'))
		e.save()
