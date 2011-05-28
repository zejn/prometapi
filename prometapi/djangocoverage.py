import coverage

def coverage_decorator(func):
	"Decorator for Django's built in test runner"
	c = coverage.coverage()
	def _inner_coverage(*args, **kwargs):
		from django.conf import settings
		c.erase()
		c.start()
		
		retval = func(*args, **kwargs)
		
		c.stop()
		
		coverage_dir = getattr(settings, 'COVERAGE_DIR', './coverage_results')
		omit_prefixes = getattr(settings, 'COVERAGE_OMIT_PREFIXES', None)
		c.html_report(directory=coverage_dir, omit_prefixes=omit_prefixes)
		return retval
	return _inner_coverage

def coverage_test_runner(*args, **kwargs):
	"Test runner you can put in your application's settings file"
	from django.test import simple
	return coverage_decorator(simple.run_tests)(*args, **kwargs)

