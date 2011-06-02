from django.core.management.base import BaseCommand, CommandError
from optparse import make_option
import os
import sys

class Command(BaseCommand):
	help = 'Fetch bicikelj XMLs and store them in order not to storm on official servers'
	
	def handle(self, *args, **options):
		from prometapi.bicikeljproxy.models import fetch_xmls, BicikeljData
		import simplejson
		
		timestamp, data = fetch_xmls()
		
		b = BicikeljData(timestamp=timestamp, json_data=simplejson.dumps(data))
		b.save()
