from django.core.management.base import BaseCommand

class Command(BaseCommand):
	def handle(self, *args, **options):
		from prometapi.models import dump_data, Events
		import datetime
		
		if len(args):
			day = datetime.datetime.strptime(args[0], '%Y-%m-%d')
		else:
			day = datetime.datetime.now() - timedelta(2)
		
		dump_data(model=Events, day=day)
