
import zlib
import base64

try:
    from urllib2 import urlopen
except ImportError:
    from urllib.request import urlopen

unicode_type = type(u'')

try:
	unichr_cast = unichr
except NameError:
	unichr_cast = chr

def zlib_encode(data):
	if isinstance(data, type(u'')):
		data = data.encode('utf-8')
	return base64.b64encode(zlib.compress(data))