# -*- coding: utf-8 -*-

import urllib
import re
import simplejson

def ch(c):
	return unichr((255 - ord(c)) % 65536)

def dstr(s):
	d = []
	i = 0
	while i < len(s):
		#print i, '\t', ord(s[i]), '\t', s[i], '\t', repr(s[i]), '\t'
		#print repr(ch(s[i]))
		d.append(ch(s[i]))
		i += 2
	if len(s) > 0 and (len(s) % 2 == 1):
		s = s[0:len(s)-1]
		#print '==='
	i = len(s) - 1
	while i >= 0:
		#print i, '\t', ord(s[i]), '\t', s[i], '\t', repr(s[i]), '\t'
		#print repr(ch(s[i]))
		d.append(ch(s[i]))
		i += -2
	return ''.join(d)
