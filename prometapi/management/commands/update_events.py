
from django.core.management.base import BaseCommand


class Command(BaseCommand):
	def handle(self, *args, **options):
		from prometapi.models import _dumps, fetch_events, parse_events, Events
		import simplejson
		
		eventsdata = fetch_events()
		try:
			json = parse_events(eventsdata)
		except simplejson.decoder.JSONDecodeError:
			json = None

		if json is not None:
			eventsdata = ''

		ev = Events(json_data=_dumps(json), original_data=eventsdata)
		ev.save()
