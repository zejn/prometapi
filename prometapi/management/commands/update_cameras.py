
from django.core.management.base import BaseCommand


class Command(BaseCommand):
	def handle(self, *args, **options):
		from prometapi.models import fetch_cameras, parse_cameras, Cameras, _dumps
		import simplejson
		
		cameradata = fetch_cameras()
		try:
			json = parse_cameras(cameradata)
		except simplejson.decoder.JSONDecodeError as e:
			json = None

		if json is not None:
			cameradata = ''

		cam = Cameras(json_data=_dumps(json), original_data=cameradata)
		cam.save()
