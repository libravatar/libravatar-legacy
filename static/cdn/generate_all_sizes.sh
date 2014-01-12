#!/bin/bash
#
# This script needs a lot of external tools (see below)
#
# Copyright (C) 2010, 2012  Francois Marier <francois@libravatar.org>
#
# Copying and distribution of this file, with or without modification,
# are permitted in any medium without royalty provided the copyright
# notice and this notice are preserved.  This file is offered as-is,
# without any warranty.

if [ "z$1" = "z" -o "z$2" = "z" ] ; then
        echo "Usage: $0 <original_image> <output_extension>"
        echo "       (e.g. $0 nobody.svg png)"
        exit 1;
fi

ORIG_IMAGE=$1
EXTENSION=$2

for s in {1..512} ; do
        if [ "$EXTENSION" = "png" ] ; then
                # ORIG_IMAGE is an SVG file
                inkscape --without-gui --export-width=${s} --export-height=${s} --export-png=${s}.png $ORIG_IMAGE
                pngcrush -q -rem gAMA -rem alla -rem text ${s}.$EXTENSION ${s}.crushed.$EXTENSION
                mv ${s}.crushed.$EXTENSION ${s}.$EXTENSION
                pngnq -f -n 32 -s 3 ${s}.$EXTENSION
                mv ${s}-nq8.$EXTENSION ${s}.$EXTENSION
                pngquant --speed=1 ${s}.$EXTENSION
                mv ${s}-fs8.$EXTENSION ${s}.$EXTENSION
                optipng -o9 -q ${s}.$EXTENSION
                advpng -z -4 -q ${s}.$EXTENSION
        elif [ "$EXTENSION" = "jpg" ] ; then
                # ORIG_IMAGE is a JPEG file
                convert $ORIG_IMAGE -resize ${s}x${s} ${s}.$EXTENSION
                jpegoptim -q -p --strip-all ${s}.$EXTENSION
        fi
done
