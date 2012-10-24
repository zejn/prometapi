from django.core.management.base import BaseCommand, CommandError
from optparse import make_option
import os
import sys

class Command(BaseCommand):
	help = 'Fetch bicikelj XMLs and store them in order not to storm on official servers'
	
	def handle(self, *args, **options):
		from prometapi.bicikeljproxy.models import fetch_xmls, BicikeljData, convert_citybikes
		import simplejson
		import datetime
		import urllib
		
		#timestamp, data = fetch_xmls()
		foreign_data = urllib.urlopen('http://api.citybik.es/bicikelj.json').read()
		
		data = convert_citybikes(foreign_data)
		timestamp = datetime.datetime.now()
		
		b = BicikeljData(timestamp=timestamp, json_data=simplejson.dumps(data))
		b.save()
