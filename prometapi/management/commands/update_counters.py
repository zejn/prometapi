
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    def handle(self, *args, **options):
        from prometapi.models import _dumps, fetch_counters, parse_counters, Counters
        import simplejson

        data = fetch_counters()
        try:
            json = parse_counters(data)
        except simplejson.decoder.JSONDecodeError:
            json = None

        # if parsing succeeded, don't store original
        if json is not None:
            data = ''

        e = Counters(json_data=_dumps(json), original_data=data)
        e.save()
