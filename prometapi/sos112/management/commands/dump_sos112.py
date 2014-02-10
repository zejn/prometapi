from django.core.management.base import BaseCommand, CommandError
from optparse import make_option
import os
import sys

class Command(BaseCommand):
    help = 'Update SPIN SOS112 feed.'
    
    def handle(self, *args, **options):
        from prometapi.models import dump_data
        import datetime
        from prometapi.sos112.models import SOS112
        
        if len(args):
            day = datetime.datetime.strptime(args[0], '%Y-%m-%d')
        else:
            day = datetime.datetime.now() - datetime.timedelta(2)
        
        dump_data(model=SOS112, day=day)