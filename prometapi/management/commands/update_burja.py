
from django.core.management.base import BaseCommand


class Command(BaseCommand):
	def handle(self, *args, **options):
		from prometapi.models import _dumps, fetch_burja, parse_burja, Burja
		import simplejson
		
		data = fetch_burja()
		try:
			json = parse_burja(data)
		except simplejson.decoder.JSONDecodeError:
			json = None

		if json is not None:
			data = ''

		e = Burja(json_data=_dumps(json), original_data=data)
		e.save()
