
from django.core.management.base import BaseCommand
from optparse import make_option

class Command(BaseCommand):
	def handle(self, *args, **options):
		from prometapi.models import _dumps, fetch_burjaznaki, parse_burjaznaki, BurjaZnaki
		import simplejson
		
		data = fetch_burjaznaki()
		try:
			json = parse_burjaznaki(data)
		except simplejson.decoder.JSONDecodeError:
			json = None
		e = BurjaZnaki(json_data=_dumps(json), original_data=data.encode('zlib').encode('base64'))
		e.save()
