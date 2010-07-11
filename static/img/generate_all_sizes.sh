#!/bin/bash
#
# This script needs imagemagick (apt-get install imagemagick)
#
# Copyright (C) 2010  Francois Marier <fmarier@gmail.com>
#
# Copying and distribution of this file, with or without modification,
# are permitted in any medium without royalty provided the copyright
# notice and this notice are preserved.  This file is offered as-is,
# without any warranty.

if [ "z$1" = "z" -o "z$2" = "z" ] ; then
        echo "Usage: $0 <original_image> <output_extension>"
        echo "       (e.g. $0 nobody.png png)"
        exit 1;
fi

ORIG_IMAGE=$1
EXTENSION=$2

for s in {1..512} ; do
        convert $ORIG_IMAGE -resize ${s}x${s} ${s}.$EXTENSION
done
