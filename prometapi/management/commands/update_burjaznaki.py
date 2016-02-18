
from django.core.management.base import BaseCommand


class Command(BaseCommand):
	def handle(self, *args, **options):
		from prometapi.models import _dumps, fetch_burjaznaki, parse_burjaznaki, BurjaZnaki
		import simplejson
		
		data = fetch_burjaznaki()
		try:
			json = parse_burjaznaki(data)
		except simplejson.decoder.JSONDecodeError:
			json = None

		if json is not None:
			data = ''

		e = BurjaZnaki(json_data=_dumps(json), original_data=data)
		e.save()
