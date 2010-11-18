all:

clean:
	find -name "*.pyc" -delete
	( [ -h libravatar/settings.py ] && rm -f libravatar/settings.py ) || true

package:
	dpkg-buildpackage -us -uc
