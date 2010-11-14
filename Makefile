all:

clean:
	find -name "*.pyc" -delete

package:
	dpkg-buildpackage -us -uc
