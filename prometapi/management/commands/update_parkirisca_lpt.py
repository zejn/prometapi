
from django.core.management.base import BaseCommand


class Command(BaseCommand):
	def handle(self, *args, **options):
		from prometapi.models import _dumps, fetch_parkirisca_lpt, parse_parkirisca_lpt, ParkiriscaLPT
		import simplejson
		
		data = fetch_parkirisca_lpt()
		try:
			json = parse_parkirisca_lpt(*data)
		except simplejson.decoder.JSONDecodeError:
			json = None

		if json is not None:
			original_data = _dumps(data)

		e = ParkiriscaLPT(json_data=_dumps(json), original_data=original_data)
		e.save()
