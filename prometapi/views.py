
from django.http import HttpResponse
from prometapi.models import Events, Burja, BurjaZnaki, Counters, ParkiriscaLPT


class List:
	def __init__(self, model):
		self.model = model
	
	def __call__(self, request):
		e = self.model.objects.latest('timestamp')
		return HttpResponse(e.json_data, mimetype='application/json')


events = List(Events)
burja = List(Burja)
burjaznaki = List(BurjaZnaki)
counters = List(Counters)
parkirisca_lpt = List(ParkiriscaLPT)

