from django.core.management.base import BaseCommand, CommandError
from optparse import make_option
import os
import sys

class Command(BaseCommand):
    help = 'Update SPIN SOS112 feed.'
    
    def handle(self, *args, **options):
        from prometapi.sos112.models import SOS112, fetch_sos112, parse_sos112
        import simplejson
        
        timestamp, data = fetch_sos112()
        
        try:
            json_data = parse_sos112(timestamp, data)
        except Exception, e:
            print e
            json_data = ''
        
        obj = SOS112(
            timestamp=timestamp,
            original_data=data,
            json_data=simplejson.dumps(json_data))
        obj.save()