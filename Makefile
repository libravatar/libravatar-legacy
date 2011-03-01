CSS := $(shell find static/css -type f -name "*.css" -a -not -name "*.css.css")
JS := $(shell find static/js -type f -name "*.js" -a -not -name "*.js.js")

MIN_CSS = ${CSS:=.css} 
MIN_JS = ${JS:=.js}
COMPRESSED_CSS = ${CSS:=.gz}
COMPRESSED_JS = ${JS:=.gz}
CLEANUP = 

all: $(MIN_CSS) $(MIN_JS) $(COMPRESSED_JS) $(COMPRESSED_CSS)

%.css: %
	yui-compressor -o $@ $<
%.js: %
	yui-compressor -o $@ $<

%.gz: %.css
	gzip --best < $< > $@
%.gz: %.js
	gzip --best < $< > $@

clean:
	rm -f $(COMPRESSED_CSS) $(COMPRESSED_JS) $(MIN_CSS) $(MIN_JS)
	find -name "*.pyc" -delete
	( [ -h libravatar/settings.py ] && rm -f libravatar/settings.py ) || true

test:
	DJANGO_SETTINGS_MODULE=libravatar.settings find -type f -name "*.py" -exec pylint --rcfile=.pylintrc {} \;

package:
	dpkg-buildpackage -us -uc
