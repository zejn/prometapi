
from django.http import HttpResponse
from prometapi.models import Events, Burja, BurjaZnaki, Counters, ParkiriscaLPT
from prometapi.bicikeljproxy.models import BicikeljData
from prometapi.sos112.models import SOS112


class List:
	def __init__(self, model):
		self.model = model
	
	def __call__(self, request):
		e = self.model.objects.latest('timestamp')
		resp = HttpResponse(e.json_data, mimetype='application/json')
		resp['Access-Control-Allow-Origin'] = '*'
		return resp


events = List(Events)
burja = List(Burja)
burjaznaki = List(BurjaZnaki)
counters = List(Counters)
parkirisca_lpt = List(ParkiriscaLPT)
bicikelj = List(BicikeljData)
sos112 = List(SOS112)

