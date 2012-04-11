CSS := $(shell find static/css -type f -name "*.css" -a -not -name "*.css.css")
JS := $(shell find static/js -type f -name "*.js" -a -not -name "*.js.js")

MIN_CSS = ${CSS:=.css} 
MIN_JS = ${JS:=.js}
COMPRESSED_CSS = ${CSS:=.gz}
COMPRESSED_JS = ${JS:=.gz}
CLEANUP = 

all: $(MIN_CSS) $(MIN_JS) $(COMPRESSED_JS) $(COMPRESSED_CSS) mofiles

%.css: %
	yui-compressor -o $@ $<
%.js: %
	yui-compressor -o $@ $<

%.gz: %.css
	gzip --best < $< > $@
%.gz: %.js
	gzip --best < $< > $@

pofiles:
	cd libravatar && for l in ca cs en es eu de fr ja ; do django-admin makemessages -l $$l -e html,txt ; done

mofiles:
	cd libravatar && django-admin compilemessages

clean:
	rm -f $(COMPRESSED_CSS) $(COMPRESSED_JS) $(MIN_CSS) $(MIN_JS)
	find -name "*.pyc" -delete
	( [ -h libravatar/settings.py ] && rm -f libravatar/settings.py ) || true

lint:
	@echo Running pylint...
	@( [ -d debian/libravatar-www ] && rm -rf debian/libravatar-www/ ) || true
	@DJANGO_SETTINGS_MODULE=libravatar.settings find libravatar/ -type f -name "*.py" -exec pylint --rcfile=.pylintrc {} \;

pyflakes:
	@echo Running pyflakes...
	@pyflakes libravatar/

pep8:
	@echo Running pep8...
	@pep8 --ignore=E501 libravatar/

unittests:
	@echo Running unit tests...
	@python libravatar/manage.py test public tools

test: pep8 pyflakes lint unittests

package:
	dpkg-buildpackage -us -uc
