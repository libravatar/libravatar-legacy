all: build

build:
	# Minify and compress javascript and css files
	find static/css -type f -name "[^.]*.css" -execdir yui-compressor -o {}.css {} \;
	find static/js -type f -name "[^.]*.js"  -execdir yui-compressor -o {}.js {} \;
	cd static/css && for f in *.css.css ; do gzip -c $$f > `basename $$f .css`.gz ; done
	cd static/js && for f in *.js.js ; do gzip -c $$f > `basename $$f .js`.gz ; done

clean:
	find static/css -name "*.css.css" -delete
	find static/js -name "*.js.js" -delete
	find static/css -name "*.css.gz" -delete
	find static/js -name "*.js.gz" -delete
	find -name "*.pyc" -delete
	( [ -h libravatar/settings.py ] && rm -f libravatar/settings.py ) || true

package:
	dpkg-buildpackage -us -uc
